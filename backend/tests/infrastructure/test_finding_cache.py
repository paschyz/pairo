"""Tests for SQL FindingCache implementation."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.infrastructure.persistence.finding_cache import SqlFindingCache
from pairo.infrastructure.persistence.models import Base, LlmCacheRow


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


SAMPLE_FINDINGS = [
    {"axis": "crafts", "file": "a.py", "line": 1, "issue": "bad", "suggestion": "fix"}
]


async def test_miss_returns_none(cache: SqlFindingCache) -> None:
    assert await cache.get("nonexistent_key") is None


async def test_put_and_get(cache: SqlFindingCache) -> None:
    await cache.put("key1", SAMPLE_FINDINGS, input_tokens=100, output_tokens=50)
    result = await cache.get("key1")
    assert result is not None
    assert result["findings"] == SAMPLE_FINDINGS
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 50


async def test_expired_entry_returns_none(
    cache: SqlFindingCache, session: Session
) -> None:
    await cache.put("old_key", SAMPLE_FINDINGS, input_tokens=10, output_tokens=5)

    # Manually expire the entry
    row = session.query(LlmCacheRow).filter_by(cache_key="old_key").one()
    row.created_at = datetime.now(tz=UTC) - timedelta(days=31)
    session.commit()

    assert await cache.get("old_key") is None


async def test_overwrite_existing_key(cache: SqlFindingCache) -> None:
    await cache.put("key1", SAMPLE_FINDINGS, input_tokens=10, output_tokens=5)
    new_findings = [{"axis": "eco", "file": "b.py", "line": 2, "issue": "n+1", "suggestion": "join"}]
    await cache.put("key1", new_findings, input_tokens=200, output_tokens=100)

    result = await cache.get("key1")
    assert result is not None
    assert result["findings"] == new_findings
    assert result["input_tokens"] == 200
