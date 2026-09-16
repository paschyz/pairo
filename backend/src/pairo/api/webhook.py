import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request, Response

from pairo.application.review_pull_request import ReviewPullRequest
from pairo.config import settings
from pairo.infrastructure.github.auth import GitHubAppAuth
from pairo.infrastructure.github.client import GitHubClient
from pairo.infrastructure.llm.factory import create_reviewer

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


def _load_private_key() -> str:
    if settings.github_private_key:
        return settings.github_private_key
    with open(settings.github_private_key_path) as f:
        return f.read()


async def _run_review(payload: dict[str, Any]) -> None:
    repo_full = payload["repository"]["full_name"]
    pr_number = payload["number"]
    try:
        owner, repo = repo_full.split("/")
        installation_id = payload["installation"]["id"]
        pr = payload["pull_request"]
        head_sha = pr["head"]["sha"]
        action = payload["action"]
        before_sha = payload.get("before")

        auth = GitHubAppAuth(settings.github_app_id, _load_private_key())
        token = await auth.get_installation_token(installation_id)
        code_host = GitHubClient(token)
        llm = create_reviewer(
            provider=settings.llm_provider,
            api_key=settings.gemini_api_key,
            model=settings.llm_model_default,
            rpm_limit=settings.llm_rpm_limit,
        )

        uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
        await uc.execute(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            action=action,
            before_sha=before_sha,
        )
        logger.info("Review posted for %s#%s", repo_full, pr_number)
    except Exception:
        logger.exception("Review failed for %s#%s", repo_full, pr_number)


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
