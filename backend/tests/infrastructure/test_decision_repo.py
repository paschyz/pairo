import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.domain.decision import DecisionSignal, DecisionStatus, FindingDecision
from pairo.infrastructure.persistence.models import Base
from pairo.infrastructure.persistence.decision_repo import SqlDecisionRepository


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        yield s


@pytest.fixture
def repo(session: Session) -> SqlDecisionRepository:
    return SqlDecisionRepository(session)


def _decision(**kwargs: object) -> FindingDecision:
    defaults: dict[str, object] = {
        "repo": "acme/web",
        "pr_number": 42,
        "fingerprint": "abc123def4567890",
        "axis": "crafts",
        "category": "naming",
        "status": DecisionStatus.POSTED,
        "signal": None,
    }
    defaults.update(kwargs)
    return FindingDecision(**defaults)  # type: ignore[arg-type]


async def test_save_and_get_decisions(repo: SqlDecisionRepository) -> None:
    d = _decision()
    await repo.save(d)
    decisions = await repo.get_decisions("acme/web", 42)
    assert len(decisions) == 1
    assert decisions[0].fingerprint == "abc123def4567890"
    assert decisions[0].status == DecisionStatus.POSTED


async def test_get_by_fingerprint(repo: SqlDecisionRepository) -> None:
    await repo.save(_decision(fingerprint="fp1"))
    await repo.save(_decision(fingerprint="fp2"))

    result = await repo.get_by_fingerprint("acme/web", 42, "fp1")
    assert result is not None
    assert result.fingerprint == "fp1"

    assert await repo.get_by_fingerprint("acme/web", 42, "fp_missing") is None


async def test_upsert_on_duplicate_fingerprint(repo: SqlDecisionRepository) -> None:
    """Unique constraint on (repo, pr_number, fingerprint): second save updates."""
    await repo.save(_decision(status=DecisionStatus.POSTED))
    await repo.save(
        _decision(
            status=DecisionStatus.REJECTED,
            signal=DecisionSignal.COMMAND,
            reason="not relevant",
            decided_by="alice",
        )
    )

    decisions = await repo.get_decisions("acme/web", 42)
    assert len(decisions) == 1
    assert decisions[0].status == DecisionStatus.REJECTED
    assert decisions[0].reason == "not relevant"


async def test_get_decisions_filters_by_pr(repo: SqlDecisionRepository) -> None:
    await repo.save(_decision(pr_number=1, fingerprint="fp1"))
    await repo.save(_decision(pr_number=2, fingerprint="fp2"))

    assert len(await repo.get_decisions("acme/web", 1)) == 1
    assert len(await repo.get_decisions("acme/web", 2)) == 1
    assert len(await repo.get_decisions("acme/web", 99)) == 0


async def test_save_with_all_fields(repo: SqlDecisionRepository) -> None:
    d = _decision(
        status=DecisionStatus.REJECTED,
        signal=DecisionSignal.REACTION,
        reason="thumbs down",
        decided_by="bob",
        github_comment_id=12345,
    )
    await repo.save(d)

    loaded = await repo.get_by_fingerprint("acme/web", 42, "abc123def4567890")
    assert loaded is not None
    assert loaded.signal == DecisionSignal.REACTION
    assert loaded.decided_by == "bob"
    assert loaded.github_comment_id == 12345
