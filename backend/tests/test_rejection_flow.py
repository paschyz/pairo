"""End-to-end: signed GitHub webhook -> SQLite decision -> next review suppresses it.

Only GitHub's API is faked; signature check, routing, background handlers, the
marker round-trip and the real SqlDecisionRepository are all exercised.
"""

import json
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pairo.api import webhook
from pairo.application.review_pull_request import ReviewPullRequest
from pairo.domain.decision import DecisionSignal, DecisionStatus
from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.fingerprint import fingerprint_for
from pairo.domain.ports import FileDiff
from pairo.infrastructure.github.client import render_review_comment
from pairo.infrastructure.persistence.decision_repo import SqlDecisionRepository
from pairo.infrastructure.persistence.models import Base
from tests.test_comment_webhook import _headers
from tests.test_review_use_case import FakeCodeHost, FakeLLM

REPO = "acme/web"
PR = 42
PAIRO_COMMENT_ID = 100

FINDING = Finding(
    axis=Axis.CRAFTS,
    file="a.py",
    line=1,
    issue="Function too long",
    suggestion="Split it",
    source=Source.LLM,
)
# Exactly what Pairo posts on GitHub (visible text + hidden marker).
PAIRO_BODY = render_review_comment(FINDING)["body"]


class FakeGitHub:
    """Stands in for GitHubClient inside the webhook handlers."""

    comments: dict[int, str] = {}
    replies: list[tuple[int, str]] = []

    def __init__(self, token: str) -> None:
        pass

    async def get_comment(self, owner: str, repo: str, cid: int) -> dict[str, Any]:
        return {"id": cid, "body": self.comments[cid]}

    async def reply_to_comment(
        self, owner: str, repo: str, pr: int, cid: int, body: str
    ) -> None:
        self.replies.append((cid, body))


class FakeAuth:
    def __init__(self, *_: object) -> None:
        pass

    async def get_installation_token(self, _: int) -> str:
        return "tok"


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Session:
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
    monkeypatch.setattr(webhook, "GitHubAppAuth", FakeAuth)
    monkeypatch.setattr(webhook, "GitHubClient", FakeGitHub)
    monkeypatch.setattr(webhook, "_load_private_key", lambda: "key")
    FakeGitHub.comments = {PAIRO_COMMENT_ID: PAIRO_BODY}
    FakeGitHub.replies = []
    return factory()


async def _post(client: AsyncClient, event: str, payload: dict[str, Any]) -> int:
    body = json.dumps(payload).encode()
    resp = await client.post(
        "/webhook", content=body, headers=_headers(body, event=event)
    )
    return resp.status_code


def _reply_payload(text: str, parent: int = PAIRO_COMMENT_ID) -> dict[str, Any]:
    return {
        "action": "created",
        "comment": {
            "id": 555,
            "body": text,
            "user": {"login": "alice"},
            "in_reply_to_id": parent,
        },
        "pull_request": {"number": PR},
        "repository": {"full_name": REPO},
        "installation": {"id": 1},
    }


def _thread_payload(action: str, body: str = PAIRO_BODY) -> dict[str, Any]:
    return {
        "action": action,
        "thread": {"comments": [{"id": PAIRO_COMMENT_ID, "body": body}]},
        "pull_request": {"number": PR},
        "repository": {"full_name": REPO},
        "sender": {"login": "alice"},
    }


async def _decision(session: Session) -> Any:
    return await SqlDecisionRepository(session).get_by_fingerprint(
        REPO, PR, fingerprint_for(FINDING)
    )


async def _next_review(session: Session, host: FakeCodeHost) -> Any:
    uc = ReviewPullRequest(
        host, FakeLLM([FINDING]), decision_repo=SqlDecisionRepository(session)
    )
    await uc.execute(
        owner="acme", repo="web", pr_number=PR, head_sha="s", action="opened"
    )
    assert host.posted_review is not None
    return host.posted_review


def _host() -> FakeCodeHost:
    return FakeCodeHost([FileDiff(path="a.py", added_lines=[AddedLine(1, "x")])])


def test_posted_comment_carries_marker_matching_the_filter_fingerprint() -> None:
    from pairo.domain.marker import parse_marker

    marker = parse_marker(PAIRO_BODY)
    assert marker is not None
    assert marker["fp"] == fingerprint_for(FINDING)


async def test_pairo_ignore_reply_rejects_finding(
    client: AsyncClient, session: Session
) -> None:
    assert (
        await _post(
            client, "pull_request_review_comment", _reply_payload("@pairo ignore nope")
        )
        == 202
    )
    d = await _decision(session)
    assert d is not None
    assert (d.status, d.signal) == (DecisionStatus.REJECTED, DecisionSignal.COMMAND)
    assert d.reason == "nope"
    assert FakeGitHub.replies  # acknowledged on the thread


async def test_resolve_conversation_rejects_finding(
    client: AsyncClient, session: Session
) -> None:
    assert (
        await _post(client, "pull_request_review_thread", _thread_payload("resolved"))
        == 202
    )
    d = await _decision(session)
    assert d is not None
    assert (d.status, d.signal) == (
        DecisionStatus.REJECTED,
        DecisionSignal.RESOLVED_UNCHANGED,
    )
    assert d.decided_by == "alice"


async def test_unresolve_reopens_finding(client: AsyncClient, session: Session) -> None:
    await _post(client, "pull_request_review_thread", _thread_payload("resolved"))
    await _post(client, "pull_request_review_thread", _thread_payload("unresolved"))
    d = await _decision(session)
    assert d is not None and d.status == DecisionStatus.POSTED


async def test_non_pairo_comment_is_not_recorded(
    client: AsyncClient, session: Session
) -> None:
    FakeGitHub.comments[PAIRO_COMMENT_ID] = "a human comment, no marker"
    await _post(client, "pull_request_review_comment", _reply_payload("@pairo ignore"))
    await _post(
        client, "pull_request_review_thread", _thread_payload("resolved", body="human")
    )
    assert await SqlDecisionRepository(session).get_decisions(REPO, PR) == []


async def test_resolved_finding_is_not_reposted_on_next_review(
    client: AsyncClient, session: Session
) -> None:
    before = await _next_review(session, _host())
    assert before.findings  # sanity: it would be posted without a rejection

    await _post(client, "pull_request_review_thread", _thread_payload("resolved"))

    after = await _next_review(session, _host())
    assert after.findings == []
    assert after.memory_filtered == 1


async def test_ignored_finding_is_not_reposted_on_next_review(
    client: AsyncClient, session: Session
) -> None:
    await _post(client, "pull_request_review_comment", _reply_payload("@pairo ignore"))
    after = await _next_review(session, _host())
    assert after.findings == []


async def test_thumbs_down_is_picked_up_on_next_review(session: Session) -> None:
    """GitHub sends no webhook for reactions: they are read at review time."""
    host = _host()

    async def threads(*_: object) -> list[dict[str, object]]:
        return [
            {"is_resolved": False, "comment_id": PAIRO_COMMENT_ID, "body": PAIRO_BODY}
        ]

    async def reactions(*_: object) -> list[str]:
        return ["-1"]

    host.get_review_threads = threads  # type: ignore[attr-defined]
    host.get_comment_reactions = reactions  # type: ignore[attr-defined]

    after = await _next_review(session, host)

    assert after.findings == []
    d = await _decision(session)
    assert d is not None
    assert (d.status, d.signal) == (DecisionStatus.REJECTED, DecisionSignal.REACTION)


async def test_unsigned_webhook_is_rejected(client: AsyncClient) -> None:
    body = json.dumps(_thread_payload("resolved")).encode()
    resp = await client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "pull_request_review_thread"},
    )
    assert resp.status_code == 401
