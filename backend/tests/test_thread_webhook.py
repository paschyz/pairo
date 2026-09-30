"""Tests for pull_request_review_thread handling (Resolve = reject)."""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.api import webhook
from pairo.domain.decision import DecisionSignal, DecisionStatus
from pairo.domain.marker import build_marker
from pairo.infrastructure.persistence.decision_repo import SqlDecisionRepository
from pairo.infrastructure.persistence.models import Base
from tests.test_comment_webhook import _headers

FP = "abc123def4567890"


def _payload(action: str, body: str | None = None) -> dict:
    return {
        "action": action,
        "thread": {
            "comments": [
                {"id": 7, "body": body or f"x\n\n{build_marker(FP, 'crafts', '')}"}
            ]
        },
        "pull_request": {"number": 42},
        "repository": {"full_name": "acme/web"},
        "sender": {"login": "alice"},
    }


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    monkeypatch.setattr(webhook, "get_session", lambda: s)
    monkeypatch.setattr(s, "close", lambda: None)
    return s


async def test_webhook_queues_resolved(client: AsyncClient) -> None:
    body = json.dumps(_payload("resolved")).encode()
    resp = await client.post(
        "/webhook",
        content=body,
        headers=_headers(body, event="pull_request_review_thread"),
    )
    assert resp.status_code == 202


async def test_webhook_ignores_other_thread_action(client: AsyncClient) -> None:
    body = json.dumps(_payload("edited")).encode()
    resp = await client.post(
        "/webhook",
        content=body,
        headers=_headers(body, event="pull_request_review_thread"),
    )
    assert resp.status_code == 200


async def test_resolve_rejects_then_unresolve_reopens(session: Session) -> None:
    repo = SqlDecisionRepository(session)
    await webhook._handle_thread(_payload("resolved"))
    d = await repo.get_by_fingerprint("acme/web", 42, FP)
    assert d and d.status == DecisionStatus.REJECTED
    assert d.signal == DecisionSignal.RESOLVED_UNCHANGED
    assert d.decided_by == "alice"

    await webhook._handle_thread(_payload("unresolved"))
    d = await repo.get_by_fingerprint("acme/web", 42, FP)
    assert d and d.status == DecisionStatus.POSTED


async def test_non_pairo_thread_is_ignored(session: Session) -> None:
    await webhook._handle_thread(_payload("resolved", body="plain comment"))
    assert await SqlDecisionRepository(session).get_decisions("acme/web", 42) == []
