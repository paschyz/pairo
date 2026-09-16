"""Tests for CachedLLMReviewer wrapper."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.cached_reviewer import CachedLLMReviewer
from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.persistence.finding_cache import SqlFindingCache
from pairo.infrastructure.persistence.models import Base


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
def cache(session: Session) -> SqlFindingCache:
    return SqlFindingCache(session, ttl_days=30)


def _files() -> list[FileDiff]:
    return [
        FileDiff(
            path="app.py",
            added_lines=[AddedLine(number=1, content="x = 1")],
        )
    ]


async def test_cache_miss_calls_llm(cache: SqlFindingCache) -> None:
    inner = FakeLLMReviewer()
    reviewer = CachedLLMReviewer(inner, cache, model="fake", axes=["crafts"])

    findings = await reviewer.review(_files(), [], ["crafts"], "fr")
    assert len(findings) > 0
    assert reviewer.cache_hits == 0


async def test_cache_hit_skips_llm(cache: SqlFindingCache) -> None:
    inner = FakeLLMReviewer()
    reviewer = CachedLLMReviewer(inner, cache, model="fake", axes=["crafts"])

    # First call populates cache
    first = await reviewer.review(_files(), [], ["crafts"], "fr")
    assert reviewer.cache_hits == 0

    # Second call with same input should hit cache
    second = await reviewer.review(_files(), [], ["crafts"], "fr")
    assert reviewer.cache_hits == 1
    assert len(second) == len(first)
    # Cached call should report 0 tokens used
    assert reviewer.last_input_tokens == 0
    assert reviewer.last_output_tokens == 0


async def test_different_prompt_version_misses_cache(
    cache: SqlFindingCache,
) -> None:
    inner = FakeLLMReviewer()
    r1 = CachedLLMReviewer(
        inner, cache, model="fake", axes=["crafts"], prompt_version="1"
    )
    await r1.review(_files(), [], ["crafts"], "fr")

    r2 = CachedLLMReviewer(
        inner, cache, model="fake", axes=["crafts"], prompt_version="2"
    )
    await r2.review(_files(), [], ["crafts"], "fr")
    assert r2.cache_hits == 0
