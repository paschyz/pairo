from collections.abc import Iterator
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
            "created_at": str(r.created_at) if r.created_at else None,
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
        "created_at": str(r.created_at) if r.created_at else None,
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
