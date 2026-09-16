import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request, Response

from pairo.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}

_seen_deliveries: set[str] = set()


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    if not signature or not settings.github_webhook_secret:
        return False
    expected = hmac.new(
        settings.github_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _ignored(detail: str) -> Response:
    return Response(
        content=f'{{"detail":"{detail}"}}',
        status_code=200,
        media_type="application/json",
    )


async def _run_review(payload: dict[str, Any]) -> None:
    # ponytail: stub — wired in step 4 when diff retrieval + review posting land
    logger.info(
        "Review queued for %s#%s",
        payload["repository"]["full_name"],
        payload["number"],
    )


@router.post("/webhook", status_code=202, response_model=None)
async def webhook(
    request: Request, background_tasks: BackgroundTasks
) -> Response | dict[str, str]:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(body, signature):
        return Response(
            content='{"detail":"Invalid signature"}',
            status_code=401,
            media_type="application/json",
        )

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return _ignored(f"Ignored event: {event}")

    import json

    payload = json.loads(body)

    action = payload.get("action", "")
    if action not in _HANDLED_ACTIONS:
        return _ignored(f"Ignored action: {action}")

    if payload.get("pull_request", {}).get("draft"):
        return _ignored("Ignored draft PR")

    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if delivery_id in _seen_deliveries:
        return _ignored("Already processed")

    _seen_deliveries.add(delivery_id)
    background_tasks.add_task(_run_review, payload)
    return {"detail": "Review queued"}
