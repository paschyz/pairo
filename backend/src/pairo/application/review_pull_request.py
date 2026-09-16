import logging
from typing import Any, Protocol

from pairo.domain.finding import Finding
from pairo.domain.ports import FileDiff
from pairo.domain.repo_config import parse_repo_config
from pairo.domain.review import Review
from pairo.domain.rules.alt import check_missing_alt
from pairo.domain.rules.contrast import check_contrast

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


class LLMReviewer(Protocol):
    last_input_tokens: int
    last_output_tokens: int

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]: ...


class ReviewPullRequest:
    def __init__(
        self,
        code_host: Any,
        llm_reviewer: Any,
        review_repo: Any = None,
        daily_quota: int = 0,
    ) -> None:
        self._code_host: CodeHost = code_host
        self._llm: LLMReviewer = llm_reviewer
        self._repo = review_repo
        self._daily_quota = daily_quota

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
            files = await self._code_host.get_pull_request_files(
                owner, repo, pr_number
            )

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
            llm_findings = await self._llm.review(
                files, findings, config.axes, config.language
            )
            findings.extend(llm_findings)

        review = Review(
            findings=findings,
            delivery_id=delivery_id,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            model=getattr(self._llm, "model_name", None),
            input_tokens=self._llm.last_input_tokens,
            output_tokens=self._llm.last_output_tokens,
        )
        await self._code_host.post_review(owner, repo, pr_number, review)

        if self._repo:
            await self._repo.save(review)
