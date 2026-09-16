import hashlib
import hmac
import json

from httpx import AsyncClient

WEBHOOK_SECRET = "test-webhook-secret"
DELIVERY_ID = "abc-123-def"

PR_OPENED_PAYLOAD = {
    "action": "opened",
    "number": 42,
    "pull_request": {
        "draft": False,
        "head": {"sha": "abc123"},
        "base": {"ref": "main"},
    },
    "repository": {
        "full_name": "owner/repo",
        "owner": {"login": "owner"},
        "name": "repo",
    },
    "installation": {"id": 12345},
}


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _headers(
    payload: bytes,
    *,
    event: str = "pull_request",
    delivery_id: str = DELIVERY_ID,
    secret: str = WEBHOOK_SECRET,
) -> dict[str, str]:
    return {
        "X-Hub-Signature-256": _sign(payload, secret),
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": "application/json",
    }


async def test_webhook_accepts_valid_pr_opened(client: AsyncClient) -> None:
    body = json.dumps(PR_OPENED_PAYLOAD).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 202


async def test_webhook_rejects_missing_signature(client: AsyncClient) -> None:
    body = json.dumps(PR_OPENED_PAYLOAD).encode()
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": DELIVERY_ID,
        "Content-Type": "application/json",
    }
    resp = await client.post("/webhook", content=body, headers=headers)
    assert resp.status_code == 401


async def test_webhook_rejects_bad_signature(client: AsyncClient) -> None:
    body = json.dumps(PR_OPENED_PAYLOAD).encode()
    headers = _headers(body, secret="wrong-secret")
    resp = await client.post("/webhook", content=body, headers=headers)
    assert resp.status_code == 401


async def test_webhook_ignores_non_pr_event(client: AsyncClient) -> None:
    body = json.dumps({"action": "created"}).encode()
    headers = _headers(body, event="issues")
    resp = await client.post("/webhook", content=body, headers=headers)
    assert resp.status_code == 200
    assert "ignored" in resp.json()["detail"].lower()


async def test_webhook_ignores_irrelevant_action(client: AsyncClient) -> None:
    payload = {**PR_OPENED_PAYLOAD, "action": "closed"}
    body = json.dumps(payload).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 200
    assert "ignored" in resp.json()["detail"].lower()


async def test_webhook_ignores_draft_pr(client: AsyncClient) -> None:
    payload = json.loads(json.dumps(PR_OPENED_PAYLOAD))
    payload["pull_request"]["draft"] = True
    body = json.dumps(payload).encode()
    resp = await client.post("/webhook", content=body, headers=_headers(body))
    assert resp.status_code == 200
    assert "draft" in resp.json()["detail"].lower()


async def test_webhook_idempotent_delivery(client: AsyncClient) -> None:
    body = json.dumps(PR_OPENED_PAYLOAD).encode()
    headers = _headers(body)
    resp1 = await client.post("/webhook", content=body, headers=headers)
    assert resp1.status_code == 202
    resp2 = await client.post("/webhook", content=body, headers=headers)
    assert resp2.status_code == 200
    assert "already" in resp2.json()["detail"].lower()
