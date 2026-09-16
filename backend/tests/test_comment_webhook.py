"""Tests for pull_request_review_comment webhook handling."""

import hashlib
import hmac
import json

from httpx import AsyncClient

WEBHOOK_SECRET = "test-webhook-secret"


def _sign(payload: bytes) -> str:
    sig = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _headers(payload: bytes, *, event: str = "pull_request_review_comment") -> dict[str, str]:
    return {
        "X-Hub-Signature-256": _sign(payload),
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": "comment-delivery-1",
        "Content-Type": "application/json",
    }


COMMENT_PAYLOAD = {
    "action": "created",
    "comment": {
        "id": 999,
        "body": "@pairo ignore not relevant",
        "user": {"login": "alice"},
        "in_reply_to_id": 100,
    },
    "pull_request": {
        "number": 42,
    },
    "repository": {
        "full_name": "acme/web",
        "owner": {"login": "acme"},
        "name": "web",
    },
    "installation": {"id": 12345},
}


async def test_comment_webhook_accepts_pairo_command(client: AsyncClient) -> None:
    body = json.dumps(COMMENT_PAYLOAD).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 202
    assert "command" in resp.json()["detail"].lower()


async def test_comment_webhook_ignores_non_command(client: AsyncClient) -> None:
    payload = {**COMMENT_PAYLOAD, "comment": {**COMMENT_PAYLOAD["comment"], "body": "Just a regular reply"}}
    body = json.dumps(payload).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 200
    assert "no command" in resp.json()["detail"].lower()


async def test_comment_webhook_ignores_non_reply(client: AsyncClient) -> None:
    """Only replies (in_reply_to_id set) are processed for commands."""
    payload = {
        **COMMENT_PAYLOAD,
        "comment": {
            "id": 999,
            "body": "@pairo ignore",
            "user": {"login": "alice"},
            # no in_reply_to_id — this is a top-level comment
        },
    }
    body = json.dumps(payload).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 200


async def test_comment_webhook_ignores_non_created_action(client: AsyncClient) -> None:
    payload = {**COMMENT_PAYLOAD, "action": "edited"}
    body = json.dumps(payload).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 200
    assert "ignored" in resp.json()["detail"].lower()
