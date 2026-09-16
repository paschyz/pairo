import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.persistence.models import Base
from pairo.infrastructure.persistence.repository import SqlReviewRepository


@pytest.fixture(autouse=True)
def _db(monkeypatch: pytest.MonkeyPatch) -> SqlReviewRepository:
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
    return SqlReviewRepository(session)


def _review(delivery_id: str = "d-1", n_findings: int = 1) -> Review:
    findings = [
        Finding(
            axis=Axis.ECO,
            file="app.py",
            line=i + 1,
            issue=f"issue-{i}",
            suggestion=f"fix-{i}",
            source=Source.LLM,
        )
        for i in range(n_findings)
    ]
    return Review(
        findings=findings,
        delivery_id=delivery_id,
        owner="acme",
        repo="web",
        pr_number=7,
        head_sha="abc",
        model="gemini-3.6-flash",
        input_tokens=100,
        output_tokens=50,
    )


async def test_list_reviews_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_reviews(
    client: AsyncClient, _db: SqlReviewRepository,
) -> None:
    await _db.save(_review("d-1"))
    await _db.save(_review("d-2"))

    resp = await client.get("/api/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["delivery_id"] in ("d-1", "d-2")
    assert "findings" not in data[0]


async def test_list_reviews_pagination(
    client: AsyncClient, _db: SqlReviewRepository,
) -> None:
    for i in range(5):
        await _db.save(_review(f"d-{i}"))

    resp = await client.get("/api/reviews?offset=2&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_review(
    client: AsyncClient, _db: SqlReviewRepository,
) -> None:
    r = _review()
    await _db.save(r)

    resp = await client.get(f"/api/reviews/{r.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["delivery_id"] == "d-1"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["axis"] == "eco"


async def test_get_review_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/reviews/999")
    assert resp.status_code == 404


async def test_stats_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_reviews"] == 0
    assert data["total_findings"] == 0


async def test_stats(
    client: AsyncClient, _db: SqlReviewRepository,
) -> None:
    await _db.save(_review("d-1", n_findings=2))
    await _db.save(_review("d-2", n_findings=3))

    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_reviews"] == 2
    assert data["total_findings"] == 5
    assert data["total_input_tokens"] == 200
    assert data["total_output_tokens"] == 100
