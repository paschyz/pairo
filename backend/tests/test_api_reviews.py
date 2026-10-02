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


def _review(
    delivery_id: str = "d-1", n_findings: int = 1, pr_number: int = 7
) -> Review:
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
        pr_number=pr_number,
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
    client: AsyncClient,
    _db: SqlReviewRepository,
) -> None:
    await _db.save(_review("d-1", pr_number=1))
    await _db.save(_review("d-2", pr_number=2))

    resp = await client.get("/api/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["delivery_id"] in ("d-1", "d-2")
    assert "findings" not in data[0]


async def test_list_reviews_pagination(
    client: AsyncClient,
    _db: SqlReviewRepository,
) -> None:
    for i in range(5):
        await _db.save(_review(f"d-{i}", pr_number=i))

    resp = await client.get("/api/reviews?offset=2&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_review(
    client: AsyncClient,
    _db: SqlReviewRepository,
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
    client: AsyncClient,
    _db: SqlReviewRepository,
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


async def test_list_is_one_row_per_pr_with_utc_timestamps(
    client: AsyncClient, _db: SqlReviewRepository
) -> None:
    from datetime import datetime

    for sha in ("a1", "b2"):
        await _db.save(
            Review(
                owner="o",
                repo="r",
                pr_number=1,
                head_sha=sha,
                delivery_id=sha,
                pr_created_at=datetime(2026, 9, 30, 8, 0, 0),
            )
        )
    rows = (await client.get("/api/reviews")).json()
    assert len(rows) == 1
    assert rows[0]["head_sha"] == "b2"
    assert rows[0]["created_at"].endswith("+00:00")
    assert rows[0]["pr_created_at"] == "2026-09-30T08:00:00+00:00"

    detail = (await client.get(f"/api/reviews/{rows[0]['id']}")).json()
    assert [h["head_sha"] for h in detail["history"]] == ["b2", "a1"]


def _flat_price(
    model: str | None, input_tokens: int, output_tokens: int
) -> float | None:
    """$1 per input token, $2 per output token; "mystery" has no known price."""
    if model == "mystery":
        return None
    return input_tokens + 2.0 * output_tokens


@pytest.fixture
def _priced(monkeypatch: pytest.MonkeyPatch) -> None:
    import pairo.api.reviews as api

    monkeypatch.setattr(api, "cost_usd", _flat_price)


async def test_kpis_empty(client: AsyncClient, _priced: None) -> None:
    resp = await client.get("/api/stats/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost_usd"] is None
    assert data["unpriced_reviews"] == 0
    assert data["total_prs"] == 0
    assert data["clean_reviews"] == 0
    assert data["median_minutes_to_first_review"] is None
    assert data["by_repo"] == []
    assert data["by_model"] == []
    assert data["by_axis"] == {}
    assert data["by_source"] == {}
    assert len(data["daily"]) == 14
    assert all(d["reviews"] == 0 for d in data["daily"])


async def test_kpis_breakdowns(
    client: AsyncClient, _db: SqlReviewRepository, _priced: None
) -> None:
    from datetime import UTC, datetime

    await _db.save(_review("d-1", n_findings=2, pr_number=1))
    await _db.save(_review("d-2", n_findings=0, pr_number=1))
    unpriced = _review("d-3", n_findings=1, pr_number=1)
    unpriced.repo = "api"
    unpriced.model = "mystery"
    await _db.save(unpriced)

    data = (await client.get("/api/stats/kpis")).json()

    assert data["total_cost_usd"] == 400.0
    assert data["unpriced_reviews"] == 1
    assert data["total_prs"] == 2
    assert data["clean_reviews"] == 1
    assert data["by_repo"] == [
        {
            "repo": "acme/web",
            "reviews": 2,
            "prs": 1,
            "findings": 2,
            "input_tokens": 200,
            "output_tokens": 100,
            "cost_usd": 400.0,
        },
        {
            "repo": "acme/api",
            "reviews": 1,
            "prs": 1,
            "findings": 1,
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": None,
        },
    ]
    assert [(m["model"], m["reviews"], m["cost_usd"]) for m in data["by_model"]] == [
        ("gemini-3.6-flash", 2, 400.0),
        ("mystery", 1, None),
    ]
    assert data["by_axis"] == {"eco": 3}
    assert data["by_source"] == {"llm": 3}

    today = data["daily"][-1]
    assert today["date"] == str(datetime.now(tz=UTC).date())
    assert today["reviews"] == 3
    assert today["cost_usd"] == 400.0
    assert sum(d["reviews"] for d in data["daily"][:-1]) == 0


async def test_kpis_median_time_to_first_review(
    client: AsyncClient, _db: SqlReviewRepository, _priced: None
) -> None:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(tz=UTC).replace(tzinfo=None)
    for pr_number, minutes in ((1, 10), (2, 30)):
        review = _review(f"d-{pr_number}", pr_number=pr_number)
        review.pr_created_at = now - timedelta(minutes=minutes)
        await _db.save(review)
    await _db.save(_review("d-3", pr_number=3))  # no PR creation date: ignored

    data = (await client.get("/api/stats/kpis")).json()

    assert data["median_minutes_to_first_review"] == pytest.approx(20, abs=1)
