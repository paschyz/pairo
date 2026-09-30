import base64
import logging
import re
from dataclasses import replace
from typing import Any

import httpx

from pairo.domain.diff import parse_patch
from pairo.domain.finding import Finding
from pairo.domain.fingerprint import fingerprint_for
from pairo.domain.marker import build_marker
from pairo.domain.ports import FileDiff
from pairo.domain.review import Review

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

_SKIP_EXTENSIONS = (".lock", ".min.js", ".min.css")
_SKIP_FILENAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
_SKIP_PREFIXES = ("vendor/", "node_modules/")

_AXIS_EMOJI = {"crafts": "🔧", "eco": "🌱", "a11y": "♿"}


def _should_skip(filename: str) -> bool:
    if filename in _SKIP_FILENAMES:
        return True
    if any(filename.startswith(p) for p in _SKIP_PREFIXES):
        return True
    return any(filename.endswith(ext) for ext in _SKIP_EXTENSIONS)


def _parse_file(raw: dict[str, Any]) -> FileDiff | None:
    status = raw.get("status", "")
    if status == "removed":
        return None
    filename = raw["filename"]
    if _should_skip(filename):
        return None
    patch = raw.get("patch", "")
    added_lines = parse_patch(patch) if patch else []
    return FileDiff(path=filename, added_lines=added_lines, status=status)


def _fence(code: str) -> str:
    # Fence must be longer than any backtick run inside the code.
    longest = max((len(m) for m in re.findall(r"`+", code)), default=0)
    return "`" * max(3, longest + 1)


def render_review_comment(finding: Finding) -> dict[str, Any]:
    """Build a GitHub review comment; adds a native ```suggestion block if any."""
    emoji = _AXIS_EMOJI.get(finding.axis, "")
    body = f"{emoji} **{finding.axis}** : {finding.issue}\n\n{finding.suggestion}"
    comment: dict[str, Any] = {
        "path": finding.file,
        "line": finding.line,
        "side": "RIGHT",
    }
    cs = finding.code_suggestion
    if cs is not None and cs.replacement.strip() and finding.line is not None:
        fence = _fence(cs.replacement)
        body += f"\n\n{fence}suggestion\n{cs.replacement}\n{fence}"
        if cs.end_line is not None and cs.end_line != finding.line:
            comment.update(
                start_line=finding.line, start_side="RIGHT", line=cs.end_line
            )
    body += "\n\n" + build_marker(fingerprint_for(finding), finding.axis.value, "")
    comment["body"] = body
    return comment


def _format_review_body(review: Review) -> str:
    if not review.findings:
        return "✅ Nothing to report."

    lines = ["**Pairo summary**\n"]
    counts = review.counts_by_axis()
    for axis, count in counts.items():
        emoji = _AXIS_EMOJI.get(axis, "")
        lines.append(f"- {emoji} {axis} : {count} finding(s)")

    if review.co2_g is not None:
        lines.append(f"🌍 Estimated CO₂ : {review.co2_g:.4f} g")
    if review.memory_summary:
        lines.append(f"\n🧠 {review.memory_summary}")

    return "\n".join(lines)


class GitHubClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

    async def get_pull_request_files(
        self, owner: str, repo: str, pr_number: int
    ) -> list[FileDiff]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers=self._headers,
            )
            resp.raise_for_status()
        raw_files: list[dict[str, Any]] = resp.json()
        return [f for raw in raw_files if (f := _parse_file(raw)) is not None]

    async def get_compare_files(
        self, owner: str, repo: str, base: str, head: str
    ) -> list[FileDiff]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/compare/{base}...{head}",
                headers=self._headers,
            )
            resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        raw_files: list[dict[str, Any]] = data.get("files", [])
        return [f for raw in raw_files if (f := _parse_file(raw)) is not None]

    async def get_file_size_kb(self, owner: str, repo: str, path: str, ref: str) -> int:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
                headers=self._headers,
            )
            resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return int(data["size"]) // 1024

    async def get_repo_file(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
                headers=self._headers,
            )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return base64.b64decode(data["content"]).decode()

    async def propose_file_change(
        self,
        owner: str,
        repo: str,
        *,
        default_branch: str,
        branch: str,
        path: str,
        content: str,
        message: str,
        title: str,
        body: str,
    ) -> str:
        # ponytail: after a merge the branch may be stale; if the PR then conflicts,
        # delete-branch-on-merge (or recreate from default when no PR is open).
        base = f"{GITHUB_API}/repos/{owner}/{repo}"
        h = self._headers
        async with httpx.AsyncClient() as client:
            ref = await client.get(f"{base}/git/ref/heads/{branch}", headers=h)
            if ref.status_code == 404:
                src = await client.get(
                    f"{base}/git/ref/heads/{default_branch}", headers=h
                )
                src.raise_for_status()
                created = await client.post(
                    f"{base}/git/refs",
                    headers=h,
                    json={
                        "ref": f"refs/heads/{branch}",
                        "sha": src.json()["object"]["sha"],
                    },
                )
                created.raise_for_status()
            else:
                ref.raise_for_status()

            current = await client.get(
                f"{base}/contents/{path}", params={"ref": branch}, headers=h
            )
            payload: dict[str, Any] = {
                "message": message,
                "branch": branch,
                "content": base64.b64encode(content.encode()).decode(),
            }
            if current.status_code == 200:
                payload["sha"] = current.json()["sha"]
            elif current.status_code != 404:
                current.raise_for_status()
            put = await client.put(f"{base}/contents/{path}", headers=h, json=payload)
            put.raise_for_status()

            prs = await client.get(
                f"{base}/pulls",
                params={"head": f"{owner}:{branch}", "state": "open"},
                headers=h,
            )
            prs.raise_for_status()
            if prs.json():
                return str(prs.json()[0]["html_url"])
            pr = await client.post(
                f"{base}/pulls",
                headers=h,
                json={
                    "title": title,
                    "head": branch,
                    "base": default_branch,
                    "body": body,
                },
            )
            pr.raise_for_status()
            return str(pr.json()["html_url"])

    async def post_review(
        self, owner: str, repo: str, pr_number: int, review: Review
    ) -> None:
        comments: list[dict[str, Any]] = []
        body_findings: list[Finding] = []

        for finding in review.findings:
            if finding.line is not None:
                comments.append(render_review_comment(finding))
            else:
                body_findings.append(finding)

        body = _format_review_body(review)
        if body_findings:
            body += "\n\n**General comments :**\n"
            for f in body_findings:
                emoji = _AXIS_EMOJI.get(f.axis, "")
                body += f"\n- {emoji} `{f.file}` : {f.issue}"

        payload: dict[str, Any] = {
            "event": "COMMENT",
            "body": body,
            "comments": comments,
        }

        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        n_sugg = sum(1 for f in review.findings if f.code_suggestion)
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            if resp.status_code == 422 and n_sugg:
                # A bad suggestion range must not sink the whole review:
                # repost every finding as a plain comment.
                logger.warning(
                    "GitHub rejected review with %d code suggestion(s), "
                    "retrying as plain comments: %s",
                    n_sugg,
                    resp.text[:300],
                )
                payload["comments"] = [
                    render_review_comment(replace(f, code_suggestion=None))
                    for f in review.findings
                    if f.line is not None
                ]
                n_sugg = 0
                resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
        if n_sugg:
            logger.info("code suggestions posted=%d", n_sugg)

    async def get_comment(
        self, owner: str, repo: str, comment_id: int
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/comments/{comment_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    async def reply_to_comment(
        self, owner: str, repo: str, pr_number: int, comment_id: int, body: str
    ) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                headers=self._headers,
                json={"body": body, "in_reply_to": comment_id},
            )
            resp.raise_for_status()

    async def get_comment_reactions(
        self, owner: str, repo: str, comment_id: int
    ) -> list[str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions",
                headers={**self._headers, "Accept": "application/vnd.github+json"},
            )
            resp.raise_for_status()
        return [r["content"] for r in resp.json()]

    async def get_review_threads(
        self, owner: str, repo: str, pr_number: int
    ) -> list[dict[str, Any]]:
        """Fetch review threads via GraphQL to get isResolved status."""
        query = """
        query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $pr) {
              reviewThreads(first: 100, after: $cursor) {
                nodes {
                  isResolved
                  comments(first: 1) {
                    nodes { id databaseId body }
                  }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
        """
        threads: list[dict[str, Any]] = []
        cursor: str | None = None

        async with httpx.AsyncClient() as client:
            while True:
                resp = await client.post(
                    "https://api.github.com/graphql",
                    headers={
                        "Authorization": f"bearer {self._token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "variables": {
                            "owner": owner,
                            "repo": repo,
                            "pr": pr_number,
                            "cursor": cursor,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()["data"]["repository"]["pullRequest"]["reviewThreads"]
                for node in data["nodes"]:
                    first = (
                        node["comments"]["nodes"][0]
                        if node["comments"]["nodes"]
                        else None
                    )
                    if first:
                        threads.append(
                            {
                                "is_resolved": node["isResolved"],
                                "comment_id": first["databaseId"],
                                "body": first["body"],
                            }
                        )
                if not data["pageInfo"]["hasNextPage"]:
                    break
                cursor = data["pageInfo"]["endCursor"]

        return threads
