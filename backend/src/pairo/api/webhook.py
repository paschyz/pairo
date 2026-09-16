import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request, Response

from pairo.application.review_pull_request import ReviewPullRequest
from pairo.config import settings
from pairo.domain.command import parse_command
from pairo.domain.decision import DecisionSignal, DecisionStatus, FindingDecision
from pairo.domain.marker import parse_marker
from pairo.infrastructure.github.auth import GitHubAppAuth
from pairo.infrastructure.github.client import GitHubClient
from pairo.infrastructure.llm.factory import create_reviewer
from pairo.infrastructure.persistence.decision_repo import SqlDecisionRepository
from pairo.infrastructure.persistence.engine import get_session
from pairo.infrastructure.persistence.repository import SqlReviewRepository

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


async def _run_review(payload: dict[str, Any], delivery_id: str) -> None:
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

        session = get_session()
        review_repo = SqlReviewRepository(session)

        uc = ReviewPullRequest(
            code_host=code_host,
            llm_reviewer=llm,
            review_repo=review_repo,
            daily_quota=settings.daily_review_quota,
        )
        await uc.execute(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            action=action,
            before_sha=before_sha,
            delivery_id=delivery_id,
        )
        logger.info("Review posted for %s#%s", repo_full, pr_number)
    except Exception:
        logger.exception("Review failed for %s#%s", repo_full, pr_number)
    finally:
        if "session" in locals():
            session.close()


async def _handle_comment(payload: dict[str, Any]) -> None:
    """Process @pairo command from a review comment reply."""
    comment = payload["comment"]
    repo_full = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    user = comment["user"]["login"]
    parent_id = comment.get("in_reply_to_id")

    cmd = parse_command(comment["body"])
    if cmd is None or parent_id is None:
        return

    try:
        installation_id = payload["installation"]["id"]
        auth = GitHubAppAuth(settings.github_app_id, _load_private_key())
        token = await auth.get_installation_token(installation_id)
        code_host = GitHubClient(token)
        owner, repo = repo_full.split("/")

        # Fetch the parent comment to get its marker
        parent = await code_host.get_comment(owner, repo, parent_id)
        marker = parse_marker(parent.get("body", ""))
        if marker is None:
            return  # Not a Pairo comment

        session = get_session()
        try:
            decision_repo = SqlDecisionRepository(session)

            if cmd.action == "ignore":
                decision = FindingDecision(
                    repo=repo_full,
                    pr_number=pr_number,
                    fingerprint=marker["fp"],
                    axis=marker["axis"],
                    category=marker["cat"],
                    status=DecisionStatus.REJECTED,
                    signal=DecisionSignal.COMMAND,
                    reason=cmd.reason,
                    decided_by=user,
                    github_comment_id=parent_id,
                )
                await decision_repo.save(decision)
                await code_host.reply_to_comment(
                    owner, repo, pr_number, comment["id"],
                    "\U0001f44d Noté, je ne reposerai pas cette remarque sur cette PR.",
                )
            elif cmd.action == "valid":
                existing = await decision_repo.get_by_fingerprint(
                    repo_full, pr_number, marker["fp"]
                )
                if existing and existing.status == DecisionStatus.REJECTED:
                    decision = FindingDecision(
                        repo=repo_full,
                        pr_number=pr_number,
                        fingerprint=marker["fp"],
                        axis=marker["axis"],
                        category=marker["cat"],
                        status=DecisionStatus.ACCEPTED,
                        signal=DecisionSignal.COMMAND,
                        decided_by=user,
                        github_comment_id=parent_id,
                    )
                    await decision_repo.save(decision)
                    await code_host.reply_to_comment(
                        owner, repo, pr_number, comment["id"],
                        "\U0001f44d Remarque réactivée.",
                    )
        finally:
            session.close()

        logger.info("Command %s processed for %s#%s", cmd.action, repo_full, pr_number)
    except Exception:
        logger.exception("Comment command failed for %s#%s", repo_full, pr_number)


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

    import json

    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body)

    if event == "pull_request_review_comment":
        action = payload.get("action", "")
        if action != "created":
            return _ignored(f"Ignored comment action: {action}")
        comment = payload.get("comment", {})
        cmd = parse_command(comment.get("body", ""))
        if cmd is None or not comment.get("in_reply_to_id"):
            return _ignored("No command in comment")
        background_tasks.add_task(_handle_comment, payload)
        return {"detail": "Command queued"}

    if event != "pull_request":
        return _ignored(f"Ignored event: {event}")

    action = payload.get("action", "")
    if action not in _HANDLED_ACTIONS:
        return _ignored(f"Ignored action: {action}")

    if payload.get("pull_request", {}).get("draft"):
        return _ignored("Ignored draft PR")

    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if delivery_id in _seen_deliveries:
        return _ignored("Already processed")

    _seen_deliveries.add(delivery_id)
    background_tasks.add_task(_run_review, payload, delivery_id)
    return {"detail": "Review queued"}
