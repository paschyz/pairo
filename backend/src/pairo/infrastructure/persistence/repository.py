import asyncio
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.persistence.models import FindingRow, ReviewRow


class SqlReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, review: Review) -> None:
        def _save() -> None:
            row = ReviewRow(
                delivery_id=review.delivery_id,
                owner=review.owner,
                repo=review.repo,
                pr_number=review.pr_number,
                head_sha=review.head_sha,
                model=review.model,
                input_tokens=review.input_tokens,
                output_tokens=review.output_tokens,
                co2_g=review.co2_g,
            )
            for f in review.findings:
                row.findings.append(
                    FindingRow(
                        axis=f.axis.value,
                        file=f.file,
                        line=f.line,
                        issue=f.issue,
                        suggestion=f.suggestion,
                        source=f.source.value,
                    )
                )
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
            review.id = row.id
            review.created_at = row.created_at

        await asyncio.to_thread(_save)

    async def exists(self, delivery_id: str) -> bool:
        def _exists() -> bool:
            stmt = select(ReviewRow.id).where(ReviewRow.delivery_id == delivery_id)
            return self._session.execute(stmt).scalar() is not None

        return await asyncio.to_thread(_exists)

    async def get(self, review_id: int) -> Review | None:
        def _get() -> Review | None:
            row = self._session.get(ReviewRow, review_id)
            if row is None:
                return None
            return _to_domain(row)

        return await asyncio.to_thread(_get)

    async def list_reviews(self, offset: int = 0, limit: int = 20) -> list[Review]:
        def _list() -> list[Review]:
            stmt = (
                select(ReviewRow)
                .order_by(ReviewRow.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = self._session.scalars(stmt).all()
            return [_to_domain(r) for r in rows]

        return await asyncio.to_thread(_list)

    async def today_review_count(self) -> int:
        def _count() -> int:
            today = datetime.now(tz=UTC).date()
            stmt = select(func.count(ReviewRow.id)).where(
                func.date(ReviewRow.created_at) == today
            )
            return self._session.execute(stmt).scalar() or 0

        return await asyncio.to_thread(_count)


def _to_domain(row: ReviewRow) -> Review:
    return Review(
        id=row.id,
        delivery_id=row.delivery_id,
        owner=row.owner,
        repo=row.repo,
        pr_number=row.pr_number,
        head_sha=row.head_sha,
        model=row.model,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        co2_g=row.co2_g,
        created_at=row.created_at,
        findings=[
            Finding(
                axis=Axis(f.axis),
                file=f.file,
                line=f.line,
                issue=f.issue,
                suggestion=f.suggestion,
                source=Source(f.source),
            )
            for f in row.findings
        ],
    )
