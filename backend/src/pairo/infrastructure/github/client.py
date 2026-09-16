import base64
import logging
from typing import Any

import httpx

from pairo.domain.diff import parse_patch
from pairo.domain.finding import Finding
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


def _format_comment(finding: Finding) -> dict[str, Any]:
    emoji = _AXIS_EMOJI.get(finding.axis, "")
    body = f"{emoji} **{finding.axis}** : {finding.issue}\n\n{finding.suggestion}"
    return {
        "path": finding.file,
        "line": finding.line,
        "side": "RIGHT",
        "body": body,
    }


def _format_review_body(review: Review) -> str:
    if not review.findings:
        return "✅ Rien à signaler."

    lines = ["**Résumé Pairo**\n"]
    counts = review.counts_by_axis()
    for axis, count in counts.items():
        emoji = _AXIS_EMOJI.get(axis, "")
        lines.append(f"- {emoji} {axis} : {count} finding(s)")

    if review.model:
        lines.append(f"\n📊 Modèle : {review.model}")
        lines.append(f"Tokens : {review.input_tokens} in / {review.output_tokens} out")
    if review.co2_g is not None:
        lines.append(f"🌍 CO₂ estimé : {review.co2_g:.4f} g")

    return "\n".join(lines)


class GitHubClient:
    def __init__(self, token: str) -> None:
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

    async def post_review(
        self, owner: str, repo: str, pr_number: int, review: Review
    ) -> None:
        comments: list[dict[str, Any]] = []
        body_findings: list[Finding] = []

        for finding in review.findings:
            if finding.line is not None:
                comments.append(_format_comment(finding))
            else:
                body_findings.append(finding)

        body = _format_review_body(review)
        if body_findings:
            body += "\n\n**Commentaires globaux :**\n"
            for f in body_findings:
                emoji = _AXIS_EMOJI.get(f.axis, "")
                body += f"\n- {emoji} `{f.file}` : {f.issue}"

        payload: dict[str, Any] = {
            "event": "COMMENT",
            "body": body,
            "comments": comments,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
