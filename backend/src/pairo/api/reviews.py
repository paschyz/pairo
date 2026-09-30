from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from pairo.infrastructure.persistence.decision_repo import (
    SqlDecisionRepository,
)
from pairo.infrastructure.persistence.engine import get_session
from pairo.infrastructure.persistence.repository import SqlReviewRepository

router = APIRouter(prefix="/api")


def _session() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()


_Session = Annotated[Session, Depends(_session)]


def _iso(dt: datetime | None) -> str | None:
    """Naive DB datetimes are UTC; emit an explicit offset so browsers don't guess."""
    return dt.replace(tzinfo=UTC).isoformat() if dt else None


@router.get("/reviews")
async def list_reviews(
    session: _Session, offset: int = 0, limit: int = 20
) -> list[dict[str, object]]:
    repo = SqlReviewRepository(session)
    reviews = await repo.list_reviews(offset=offset, limit=limit)
    return [
        {
            "id": r.id,
            "delivery_id": r.delivery_id,
            "owner": r.owner,
            "repo": r.repo,
            "pr_number": r.pr_number,
            "head_sha": r.head_sha,
            "model": r.model,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "total_findings": r.total,
            "pr_created_at": _iso(r.pr_created_at),
            "created_at": _iso(r.created_at),
        }
        for r in reviews
    ]


@router.get("/reviews/{review_id}", response_model=None)
async def get_review(review_id: int, session: _Session) -> dict[str, object] | Response:
    repo = SqlReviewRepository(session)
    r = await repo.get(review_id)
    if r is None:
        return Response(
            content='{"detail":"Not found"}',
            status_code=404,
            media_type="application/json",
        )
    history = await repo.list_for_pr(r.owner, r.repo, r.pr_number)
    return {
        "id": r.id,
        "delivery_id": r.delivery_id,
        "owner": r.owner,
        "repo": r.repo,
        "pr_number": r.pr_number,
        "head_sha": r.head_sha,
        "model": r.model,
        "input_tokens": r.input_tokens,
        "output_tokens": r.output_tokens,
        "pr_created_at": _iso(r.pr_created_at),
        "created_at": _iso(r.created_at),
        "history": [
            {
                "id": h.id,
                "head_sha": h.head_sha,
                "total_findings": h.total,
                "created_at": _iso(h.created_at),
            }
            for h in history
        ],
        "findings": [
            {
                "axis": f.axis.value,
                "file": f.file,
                "line": f.line,
                "issue": f.issue,
                "suggestion": f.suggestion,
                "source": f.source.value,
                "category": f.category,
            }
            for f in r.findings
        ],
    }


@router.get("/stats")
async def stats(session: _Session) -> dict[str, int]:
    repo = SqlReviewRepository(session)
    return await repo.stats()


@router.get("/stats/memory")
async def memory_stats(session: _Session) -> dict[str, Any]:
    decision_repo = SqlDecisionRepository(session)
    return await decision_repo.memory_stats()
