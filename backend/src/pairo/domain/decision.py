"""Finding decision tracking. Pure domain, no external deps."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DecisionStatus(StrEnum):
    POSTED = "posted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    RESOLVED_WITH_CHANGE = "resolved_with_change"


class DecisionSignal(StrEnum):
    COMMAND = "command"
    REACTION = "reaction"
    RESOLVED_UNCHANGED = "resolved_unchanged"
    REPLY_LLM = "reply_llm"


@dataclass
class FindingDecision:
    repo: str
    pr_number: int
    fingerprint: str
    axis: str
    category: str
    status: DecisionStatus
    signal: DecisionSignal | None = None
    reason: str | None = None
    decided_by: str | None = None
    github_comment_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
