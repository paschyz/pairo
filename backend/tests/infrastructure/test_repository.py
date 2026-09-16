from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.persistence.models import Base
from pairo.infrastructure.persistence.repository import SqlReviewRepository


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
def repo(session: Session) -> SqlReviewRepository:
    return SqlReviewRepository(session)


def _review(**kwargs: object) -> Review:
    defaults: dict[str, object] = {
        "findings": [
            Finding(
                axis=Axis.ECO,
                file="app.py",
                line=10,
                issue="N+1",
                suggestion="use join",
                source=Source.LLM,
            )
        ],
        "delivery_id": "d-1",
        "owner": "acme",
        "repo": "web",
        "pr_number": 7,
        "head_sha": "abc123",
        "input_tokens": 100,
        "output_tokens": 50,
    }
    defaults.update(kwargs)
    return Review(**defaults)  # type: ignore[arg-type]


async def test_save_and_get(repo: SqlReviewRepository) -> None:
    r = _review()
    await repo.save(r)
    assert r.id is not None

    loaded = await repo.get(r.id)
    assert loaded is not None
    assert loaded.delivery_id == "d-1"
    assert loaded.owner == "acme"
    assert loaded.pr_number == 7
    assert loaded.input_tokens == 100
    assert len(loaded.findings) == 1
    assert loaded.findings[0].axis == Axis.ECO
    assert loaded.findings[0].source == Source.LLM


async def test_exists(repo: SqlReviewRepository) -> None:
    assert await repo.exists("d-1") is False
    await repo.save(_review(delivery_id="d-1"))
    assert await repo.exists("d-1") is True
    assert await repo.exists("d-2") is False


async def test_list_reviews(repo: SqlReviewRepository) -> None:
    for i in range(3):
        await repo.save(_review(delivery_id=f"d-{i}"))
    reviews = await repo.list_reviews(offset=0, limit=10)
    assert len(reviews) == 3


async def test_list_reviews_pagination(repo: SqlReviewRepository) -> None:
    for i in range(5):
        await repo.save(_review(delivery_id=f"d-{i}"))
    page = await repo.list_reviews(offset=2, limit=2)
    assert len(page) == 2


async def test_get_nonexistent(repo: SqlReviewRepository) -> None:
    assert await repo.get(999) is None


async def test_today_review_count(repo: SqlReviewRepository) -> None:
    await repo.save(_review(delivery_id="d-today"))
    count = await repo.today_review_count()
    assert count == 1


async def test_today_review_count_excludes_old(
    repo: SqlReviewRepository, session: Session,
) -> None:
    await repo.save(_review(delivery_id="d-old"))
    from pairo.infrastructure.persistence.models import ReviewRow

    row = session.query(ReviewRow).filter_by(delivery_id="d-old").one()
    row.created_at = datetime.now(tz=UTC) - timedelta(days=2)
    session.commit()

    count = await repo.today_review_count()
    assert count == 0
