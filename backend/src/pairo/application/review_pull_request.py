import logging
from datetime import datetime
from typing import Any, Protocol

from pairo.application.propose_context_rule import PATH as PAIRO_MD
from pairo.domain.context_rule import MAX_FILE_CHARS
from pairo.domain.decision import DecisionStatus
from pairo.domain.decision_rebuild import rebuild_decisions_from_comments
from pairo.domain.filter_findings import filter_findings, memory_summary_line
from pairo.domain.finding import Finding
from pairo.domain.fingerprint import fingerprint_for
from pairo.domain.ports import FileDiff
from pairo.domain.repo_config import parse_repo_config
from pairo.domain.review import Review
from pairo.domain.rules.alt import check_missing_alt
from pairo.domain.rules.contrast import check_contrast
from pairo.domain.suggestion import sanitize_suggestions

logger = logging.getLogger(__name__)


class CodeHost(Protocol):
    async def get_pull_request_files(
        self, owner: str, repo: str, pr_number: int
    ) -> list[FileDiff]: ...

    async def get_compare_files(
        self, owner: str, repo: str, base: str, head: str
    ) -> list[FileDiff]: ...

    async def get_file_size_kb(
        self, owner: str, repo: str, path: str, ref: str
    ) -> int: ...

    async def post_review(
        self, owner: str, repo: str, pr_number: int, review: Review
    ) -> None: ...

    async def get_repo_file(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None: ...

    async def get_review_threads(
        self, owner: str, repo: str, pr_number: int
    ) -> list[dict[str, Any]]: ...

    async def get_comment_reactions(
        self, owner: str, repo: str, comment_id: int
    ) -> list[str]: ...


class LLMReviewer(Protocol):
    last_input_tokens: int
    last_output_tokens: int

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
        project_context: str = "",
    ) -> list[Finding]: ...


class ReviewPullRequest:
    def __init__(
        self,
        code_host: Any,
        llm_reviewer: Any,
        review_repo: Any = None,
        daily_quota: int = 0,
        decision_repo: Any = None,
    ) -> None:
        self._code_host: CodeHost = code_host
        self._llm: LLMReviewer = llm_reviewer
        self._repo = review_repo
        self._daily_quota = daily_quota
        self._decision_repo = decision_repo

    async def _sync_github_decisions(
        self, owner: str, repo: str, pr_number: int
    ) -> None:
        """Persist Resolve / thumbs-down rejections found on the PR's threads."""
        try:
            threads = await self._code_host.get_review_threads(owner, repo, pr_number)
            comments = [
                {
                    "id": t["comment_id"],
                    "body": t["body"],
                    "is_resolved": t["is_resolved"],
                    "reactions": await self._code_host.get_comment_reactions(
                        owner, repo, t["comment_id"]
                    ),
                }
                for t in threads
            ]
            for d in rebuild_decisions_from_comments(
                comments, f"{owner}/{repo}", pr_number
            ):
                if d.status == DecisionStatus.REJECTED:
                    await self._decision_repo.save(d)
        except Exception:
            logger.exception(
                "Decision sync failed for %s/%s#%s", owner, repo, pr_number
            )

    async def execute(
        self,
        *,
        owner: str,
        repo: str,
        pr_number: int,
        head_sha: str,
        action: str,
        before_sha: str | None = None,
        delivery_id: str = "",
        pr_created_at: datetime | None = None,
        base_ref: str | None = None,
    ) -> None:
        config_raw = await self._code_host.get_repo_file(
            owner, repo, ".pairo.yml", head_sha
        )
        config = parse_repo_config(config_raw)

        if action == "synchronize" and before_sha:
            files = await self._code_host.get_compare_files(
                owner, repo, before_sha, head_sha
            )
        else:
            files = await self._code_host.get_pull_request_files(owner, repo, pr_number)

        files = [f for f in files if not config.should_ignore(f.path)]

        findings: list[Finding] = []

        for f in files:
            if not f.added_lines:
                continue
            if "a11y" in config.axes:
                findings.extend(check_missing_alt(f.path, f.added_lines))
                findings.extend(check_contrast(f.path, f.added_lines))

        has_added_lines = any(f.added_lines for f in files)
        skip_llm = False
        if self._repo and self._daily_quota:
            count = await self._repo.today_review_count()
            if count >= self._daily_quota:
                skip_llm = True
                logger.warning("Daily quota reached (%d), skipping LLM", count)

        if has_added_lines and not skip_llm:
            # Rules come from the base branch: they apply once merged, and a PR
            # can't rewrite the rules its own review follows.
            pairo_md = await self._code_host.get_repo_file(
                owner, repo, PAIRO_MD, base_ref or head_sha
            )
            llm_findings = await self._llm.review(
                files,
                findings,
                config.axes,
                config.language,
                project_context=(pairo_md or "")[:MAX_FILE_CHARS],
            )
            findings.extend(llm_findings)

        proposed = sum(1 for f in findings if f.code_suggestion)
        findings, dropped = sanitize_suggestions(findings, files)
        if proposed:
            logger.info(
                "code suggestions: proposed=%d kept=%d dropped_invalid=%d",
                proposed,
                proposed - dropped,
                dropped,
            )

        # --- Memory filtering ---
        filtered_count = 0
        memory_line = ""
        if self._decision_repo:
            repo_full = f"{owner}/{repo}"
            await self._sync_github_decisions(owner, repo, pr_number)
            decisions = await self._decision_repo.get_decisions(repo_full, pr_number)
            if decisions:
                # Build fingerprint -> finding mapping
                findings_by_fp: dict[str, Finding] = {}
                for finding in findings:
                    fp = fingerprint_for(finding)
                    findings_by_fp[fp] = finding

                kept, filtered_count = filter_findings(findings_by_fp, decisions)
                findings = list(kept.values())
                memory_line = memory_summary_line(filtered_count)

        review = Review(
            findings=findings,
            delivery_id=delivery_id,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            pr_created_at=pr_created_at,
            model=getattr(self._llm, "model_name", None),
            input_tokens=self._llm.last_input_tokens,
            output_tokens=self._llm.last_output_tokens,
            memory_filtered=filtered_count,
            memory_summary=memory_line,
        )
        await self._code_host.post_review(owner, repo, pr_number, review)

        if self._repo:
            await self._repo.save(review)
