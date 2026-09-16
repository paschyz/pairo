from __future__ import annotations

from typing import Protocol

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Finding
from pairo.domain.review import Review


class FileDiff:
    """A file's diff as returned by the code host."""

    __slots__ = ("path", "added_lines", "status")

    def __init__(
        self, path: str, added_lines: list[AddedLine], status: str = "modified"
    ) -> None:
        self.path = path
        self.added_lines = added_lines
        self.status = status


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
    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]: ...


class ReviewRepository(Protocol):
    async def save(self, review: Review, delivery_id: str) -> None: ...

    async def exists(self, delivery_id: str) -> bool: ...

    async def get(self, review_id: int) -> Review | None: ...

    async def list_reviews(
        self, offset: int = 0, limit: int = 20
    ) -> list[Review]: ...
