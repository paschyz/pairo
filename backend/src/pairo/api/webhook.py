import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request, Response
from sqlalchemy.orm import Session

from pairo.application.propose_context_rule import ProposeContextRule
from pairo.application.review_pull_request import ReviewPullRequest
from pairo.config import settings
from pairo.domain.command import parse_command
from pairo.domain.context_rule import is_trusted
from pairo.domain.decision import DecisionSignal, DecisionStatus, FindingDecision
from pairo.domain.marker import parse_marker
from pairo.infrastructure.github.auth import GitHubAppAuth
from pairo.infrastructure.github.client import GitHubClient
from pairo.infrastructure.llm.cached_reviewer import CachedLLMReviewer
from pairo.infrastructure.llm.factory import (
    create_judge,
    create_reviewer,
    create_rule_filter,
)
from pairo.infrastructure.persistence.decision_repo import SqlDecisionRepository
from pairo.infrastructure.persistence.engine import get_session
from pairo.infrastructure.persistence.finding_cache import SqlFindingCache
from pairo.infrastructure.persistence.repository import SqlReviewRepository

logger = logging.getLogger(__name__)

router = APIRouter()

_HANDLED_ACTIONS = {"opened", "synchronize", "reopened", "ready_for_review"}

# ponytail: per-process memory of recent deliveries (insertion-ordered, bounded).
# Reviews are also checked against the DB; use a shared store with several workers.
_seen_deliveries: dict[str, None] = {}
_MAX_SEEN_DELIVERIES = 10_000


def _already_delivered(delivery_id: str) -> bool:
    """True for a GitHub redelivery; records the id otherwise."""
    if not delivery_id:
        return False
    if delivery_id in _seen_deliveries:
        return True
    _seen_deliveries[delivery_id] = None
    if len(_seen_deliveries) > _MAX_SEEN_DELIVERIES:
        del _seen_deliveries[next(iter(_seen_deliveries))]
    return False


def _written_by_bot(comment: dict[str, Any]) -> bool:
    """Markers are only trusted in a bot's comment: anyone can paste one."""
    return (comment.get("user") or {}).get("type") == "Bot"


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    if not signature or not settings.github_webhook_secret:
        return False
    expected = hmac.new(
        settings.github_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _parse_github_time(value: str | None) -> datetime | None:
    """GitHub ISO timestamp -> naive UTC (matches the DateTime columns)."""
    if not value:
        return None
    return datetime.fromisoformat(value).astimezone(UTC).replace(tzinfo=None)


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


def _llm_api_key() -> str:
    return settings.llm_api_key or (
        settings.gemini_api_key if settings.llm_provider == "gemini" else ""
    )


def _make_llm() -> Any:
    return create_reviewer(
        provider=settings.llm_provider,
        api_key=_llm_api_key(),
        model=settings.llm_model_default,
        rpm_limit=settings.llm_rpm_limit,
    )


def _with_cache(llm: Any, session: Session) -> Any:
    """Same diff, rules, prompt and model: reuse the stored findings, zero LLM cost."""
    model = getattr(llm, "model_name", "")
    if not model:  # the fake provider has no model to key the cache on
        return llm
    cache = SqlFindingCache(session, ttl_days=settings.llm_cache_ttl_days)
    return CachedLLMReviewer(llm, cache, model=model, axes=[])


def _make_judge() -> Any:
    if not settings.llm_model_judge:
        return _make_llm()
    return create_judge(
        provider=settings.llm_provider,
        api_key=_llm_api_key(),
        model=settings.llm_model_judge,
        rpm_limit=settings.llm_rpm_limit,
    )


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

        session = get_session()
        llm = _with_cache(_make_llm(), session)
        review_repo = SqlReviewRepository(session)
        decision_repo = SqlDecisionRepository(session)
        # Survives a restart, unlike the in-memory set: don't pay and post twice.
        if delivery_id and await review_repo.exists(delivery_id):
            logger.info("Delivery %s already reviewed, skipping", delivery_id)
            return

        uc = ReviewPullRequest(
            code_host=code_host,
            llm_reviewer=llm,
            review_repo=review_repo,
            daily_quota=settings.daily_review_quota,
            decision_repo=decision_repo,
            rule_filter=create_rule_filter(
                provider=settings.llm_provider,
                api_key=_llm_api_key(),
                model=settings.llm_model_judge,
                rpm_limit=settings.llm_rpm_limit,
            ),
        )
        await uc.execute(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            action=action,
            before_sha=before_sha,
            delivery_id=delivery_id,
            pr_created_at=_parse_github_time(pr.get("created_at")),
            base_ref=pr.get("base", {}).get("ref"),
        )
        logger.info("Review posted for %s#%s", repo_full, pr_number)
    except Exception:
        logger.exception("Review failed for %s#%s", repo_full, pr_number)
    finally:
        if "session" in locals():
            session.close()


async def _propose_rule(
    code_host: GitHubClient,
    payload: dict[str, Any],
    parent: dict[str, Any],
    reason: str,
) -> str | None:
    """Best effort: the rejection is already saved, a failure here must not undo it."""
    repo_full = payload["repository"]["full_name"]
    owner, repo = repo_full.split("/")
    try:
        uc = ProposeContextRule(
            code_host,
            judge=_make_judge(),
            writer=_make_llm(),
            threshold=settings.context_rule_threshold,
        )
        return await uc.execute(
            owner=owner,
            repo=repo,
            default_branch=payload["repository"].get("default_branch", "main"),
            reason=reason,
            finding_text=parent.get("body", "").split("<!--")[0].strip(),
            file=parent.get("path", ""),
        )
    except Exception:
        logger.exception(
            "Rule proposal failed for %s#%s",
            repo_full,
            payload["pull_request"]["number"],
        )
        return None


async def _handle_comment(payload: dict[str, Any]) -> None:
    """Process `@pairo ignore [reason]` replied to a Pairo review comment."""
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
        if marker is None or not _written_by_bot(parent):
            logger.info("Comment %s is not a Pairo finding, ignoring", parent_id)
            return

        # Dismissing is for maintainers and the PR's author, not any passer-by
        # able to comment on a public repo.
        assoc = comment.get("author_association")
        pr_author = (payload["pull_request"].get("user") or {}).get("login")
        if not is_trusted(assoc) and user != pr_author:
            logger.info("%s may not dismiss findings on %s", user, repo_full)
            return

        session = get_session()
        try:
            await SqlDecisionRepository(session).save(
                FindingDecision(
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
            )
        finally:
            session.close()

        reply = "\U0001f44d Ignored on this PR."
        if cmd.reason and is_trusted(assoc):
            outcome = await _propose_rule(code_host, payload, parent, cmd.reason)
            if outcome:
                reply += f" {outcome}"
        await code_host.reply_to_comment(owner, repo, pr_number, comment["id"], reply)

        logger.info("Command %s processed for %s#%s", cmd.action, repo_full, pr_number)
    except Exception:
        logger.exception("Comment command failed for %s#%s", repo_full, pr_number)


async def _handle_thread(payload: dict[str, Any]) -> None:
    """Resolve conversation = reject the finding; unresolve = undo that rejection."""
    repo_full = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    try:
        first = payload["thread"]["comments"][0]
        marker = parse_marker(first.get("body", ""))
        if marker is None or not _written_by_bot(first):
            logger.info(
                "Thread on %s#%s is not a Pairo finding, ignoring", repo_full, pr_number
            )
            return

        session = get_session()
        try:
            decision_repo = SqlDecisionRepository(session)
            resolved = payload["action"] == "resolved"
            if not resolved:
                existing = await decision_repo.get_by_fingerprint(
                    repo_full, pr_number, marker["fp"]
                )
                if not existing or existing.signal != DecisionSignal.RESOLVED_UNCHANGED:
                    return
            await decision_repo.save(
                FindingDecision(
                    repo=repo_full,
                    pr_number=pr_number,
                    fingerprint=marker["fp"],
                    axis=marker["axis"],
                    category=marker["cat"],
                    status=DecisionStatus.REJECTED
                    if resolved
                    else DecisionStatus.POSTED,
                    signal=DecisionSignal.RESOLVED_UNCHANGED if resolved else None,
                    decided_by=payload.get("sender", {}).get("login"),
                    github_comment_id=first["id"],
                )
            )
        finally:
            session.close()
        logger.info("Thread %s for %s#%s", payload["action"], repo_full, pr_number)
    except Exception:
        logger.exception("Thread handling failed for %s#%s", repo_full, pr_number)


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
    logger.info("Webhook event=%s action=%s", event, payload.get("action"))

    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if _already_delivered(delivery_id):
        return _ignored("Already processed")

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

    if event == "pull_request_review_thread":
        action = payload.get("action", "")
        if action not in ("resolved", "unresolved"):
            return _ignored(f"Ignored thread action: {action}")
        background_tasks.add_task(_handle_thread, payload)
        return {"detail": "Thread queued"}

    if event != "pull_request":
        return _ignored(f"Ignored event: {event}")

    action = payload.get("action", "")
    if action not in _HANDLED_ACTIONS:
        return _ignored(f"Ignored action: {action}")

    if payload.get("pull_request", {}).get("draft"):
        return _ignored("Ignored draft PR")

    background_tasks.add_task(_run_review, payload, delivery_id)
    return {"detail": "Review queued"}
