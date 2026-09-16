"""Rebuild finding decisions from GitHub comment data. Pure domain."""

from typing import Any

from pairo.domain.decision import (
    DecisionSignal,
    DecisionStatus,
    FindingDecision,
)
from pairo.domain.marker import parse_marker


def rebuild_decisions_from_comments(
    comments: list[dict[str, Any]],
    repo: str,
    pr_number: int,
) -> list[FindingDecision]:
    """Parse Pairo markers from comment dicts and infer decision status.

    Each comment dict has: id, body, reactions (list of reaction types),
    is_resolved (bool).
    """
    decisions: list[FindingDecision] = []

    for comment in comments:
        parsed = parse_marker(comment["body"])
        if parsed is None:
            continue

        status = DecisionStatus.POSTED
        signal: DecisionSignal | None = None

        # Deterministic signals: resolved thread or thumbs-down reaction
        if comment.get("is_resolved"):
            status = DecisionStatus.REJECTED
            signal = DecisionSignal.RESOLVED_UNCHANGED
        elif "-1" in comment.get("reactions", []):
            status = DecisionStatus.REJECTED
            signal = DecisionSignal.REACTION

        decisions.append(
            FindingDecision(
                repo=repo,
                pr_number=pr_number,
                fingerprint=parsed["fp"],
                axis=parsed["axis"],
                category=parsed["cat"],
                status=status,
                signal=signal,
                github_comment_id=comment["id"],
            )
        )

    return decisions
