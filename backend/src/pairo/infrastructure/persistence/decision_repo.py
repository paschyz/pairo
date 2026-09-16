"""SQLAlchemy implementation of DecisionRepository."""

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import Session

from pairo.domain.decision import (
    DecisionSignal,
    DecisionStatus,
    FindingDecision,
)
from pairo.infrastructure.persistence.models import FindingDecisionRow


class SqlDecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_decisions(
        self, repo: str, pr_number: int
    ) -> list[FindingDecision]:
        def _query() -> list[FindingDecision]:
            stmt = select(FindingDecisionRow).where(
                FindingDecisionRow.repo == repo,
                FindingDecisionRow.pr_number == pr_number,
            )
            rows = self._session.scalars(stmt).all()
            return [_to_domain(r) for r in rows]

        return await asyncio.to_thread(_query)

    async def save(self, decision: FindingDecision) -> None:
        def _save() -> None:
            stmt = select(FindingDecisionRow).where(
                FindingDecisionRow.repo == decision.repo,
                FindingDecisionRow.pr_number == decision.pr_number,
                FindingDecisionRow.fingerprint == decision.fingerprint,
            )
            existing = self._session.scalars(stmt).first()

            if existing:
                existing.status = decision.status.value
                existing.signal = decision.signal.value if decision.signal else None
                existing.reason = decision.reason
                existing.decided_by = decision.decided_by
                existing.github_comment_id = decision.github_comment_id
            else:
                row = FindingDecisionRow(
                    repo=decision.repo,
                    pr_number=decision.pr_number,
                    fingerprint=decision.fingerprint,
                    axis=decision.axis,
                    category=decision.category,
                    status=decision.status.value,
                    signal=decision.signal.value if decision.signal else None,
                    reason=decision.reason,
                    decided_by=decision.decided_by,
                    github_comment_id=decision.github_comment_id,
                )
                self._session.add(row)

            self._session.commit()

        await asyncio.to_thread(_save)

    async def get_by_fingerprint(
        self, repo: str, pr_number: int, fingerprint: str
    ) -> FindingDecision | None:
        def _query() -> FindingDecision | None:
            stmt = select(FindingDecisionRow).where(
                FindingDecisionRow.repo == repo,
                FindingDecisionRow.pr_number == pr_number,
                FindingDecisionRow.fingerprint == fingerprint,
            )
            row = self._session.scalars(stmt).first()
            return _to_domain(row) if row else None

        return await asyncio.to_thread(_query)


def _to_domain(row: FindingDecisionRow) -> FindingDecision:
    return FindingDecision(
        repo=row.repo,
        pr_number=row.pr_number,
        fingerprint=row.fingerprint,
        axis=row.axis,
        category=row.category,
        status=DecisionStatus(row.status),
        signal=DecisionSignal(row.signal) if row.signal else None,
        reason=row.reason,
        decided_by=row.decided_by,
        github_comment_id=row.github_comment_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
