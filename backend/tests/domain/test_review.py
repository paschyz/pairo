from datetime import UTC, datetime

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review


def _finding(axis: Axis = Axis.CRAFTS, source: Source = Source.RULE) -> Finding:
    return Finding(
        axis=axis, file="f.py", line=1, issue="x", suggestion="y", source=source
    )


def test_review_counts_by_axis() -> None:
    r = Review(
        findings=[
            _finding(Axis.CRAFTS),
            _finding(Axis.CRAFTS),
            _finding(Axis.A11Y),
        ]
    )
    counts = r.counts_by_axis()
    assert counts[Axis.CRAFTS] == 2
    assert counts[Axis.A11Y] == 1
    assert counts.get(Axis.ECO, 0) == 0


def test_review_empty() -> None:
    r = Review(findings=[])
    assert r.counts_by_axis() == {}
    assert r.total == 0


def test_review_total() -> None:
    r = Review(findings=[_finding(), _finding(), _finding()])
    assert r.total == 3


def test_review_tracks_llm_metadata() -> None:
    r = Review(
        findings=[_finding(source=Source.LLM)],
        model="gemini-2.0-flash-lite",
        input_tokens=500,
        output_tokens=120,
        co2_g=0.002,
    )
    assert r.model == "gemini-2.0-flash-lite"
    assert r.input_tokens == 500
    assert r.output_tokens == 120
    assert r.co2_g == 0.002


def test_review_persistence_fields() -> None:
    now = datetime.now(tz=UTC)
    r = Review(
        findings=[_finding()],
        owner="acme",
        repo="web",
        pr_number=42,
        delivery_id="abc-123",
        head_sha="deadbeef",
        created_at=now,
    )
    assert r.owner == "acme"
    assert r.repo == "web"
    assert r.pr_number == 42
    assert r.delivery_id == "abc-123"
    assert r.head_sha == "deadbeef"
    assert r.created_at == now
    assert r.id is None


def test_review_persistence_defaults() -> None:
    r = Review()
    assert r.id is None
    assert r.delivery_id == ""
    assert r.owner == ""
    assert r.repo == ""
    assert r.pr_number == 0
    assert r.head_sha == ""
    assert r.created_at is None
