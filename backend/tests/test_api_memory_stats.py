"""Tests for memory stats in the API."""

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.domain.decision import (
    DecisionSignal,
    DecisionStatus,
    FindingDecision,
)
from pairo.infrastructure.persistence.decision_repo import (
    SqlDecisionRepository,
)
from pairo.infrastructure.persistence.models import Base


@pytest.fixture(autouse=True)
def _db(monkeypatch: pytest.MonkeyPatch) -> SqlDecisionRepository:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    import pairo.infrastructure.persistence.engine as eng

    monkeypatch.setattr(eng, "_engine", engine)
    monkeypatch.setattr(eng, "_SessionLocal", factory)

    session = factory()
    return SqlDecisionRepository(session)


def _decision(
    fingerprint: str = "fp1",
    status: DecisionStatus = DecisionStatus.REJECTED,
    signal: DecisionSignal = DecisionSignal.COMMAND,
    category: str = "naming",
    pr_number: int = 1,
) -> FindingDecision:
    return FindingDecision(
        repo="acme/web",
        pr_number=pr_number,
        fingerprint=fingerprint,
        axis="crafts",
        category=category,
        status=status,
        signal=signal,
    )


async def test_memory_stats_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/stats/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rejected"] == 0
    assert data["by_signal"] == {}
    assert data["by_category"] == {}


async def test_memory_stats_with_decisions(
    client: AsyncClient, _db: SqlDecisionRepository
) -> None:
    await _db.save(_decision("fp1", signal=DecisionSignal.COMMAND))
    await _db.save(
        _decision("fp2", signal=DecisionSignal.REACTION, category="complexity")
    )
    await _db.save(
        _decision(
            "fp3",
            signal=DecisionSignal.COMMAND,
            category="naming",
            pr_number=2,
        )
    )

    resp = await client.get("/api/stats/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rejected"] == 3
    assert data["by_signal"]["command"] == 2
    assert data["by_signal"]["reaction"] == 1
    assert data["by_category"]["naming"] == 2
    assert data["by_category"]["complexity"] == 1
