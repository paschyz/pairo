"""Turn a durable reviewer instruction into one line of .pairo.md. Pure domain."""

from dataclasses import dataclass

MAX_RULE_CHARS = 280
MAX_FILE_CHARS = 8000
HEADER = "# Pairo context"
_TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}


@dataclass(frozen=True)
class RuleProposal:
    persist: bool
    confidence: float
    rule: str


NO_RULE = RuleProposal(persist=False, confidence=0.0, rule="")


def is_trusted(author_association: str | None) -> bool:
    return author_association in _TRUSTED


def _clean(rule: str) -> str:
    return " ".join(rule.split())[:MAX_RULE_CHARS].strip()


def accept(proposal: RuleProposal, threshold: float) -> bool:
    return (
        proposal.persist
        and proposal.confidence >= threshold
        and bool(_clean(proposal.rule))
    )


def _norm(line: str) -> str:
    return " ".join(line.lstrip("-* ").split()).lower()


def merge_rule(existing: str | None, rule: str) -> str | None:
    """Append `rule` to the file. None if duplicate or the file would exceed the cap."""
    rule = _clean(rule)
    base = existing if existing else HEADER + "\n"
    if any(_norm(line) == _norm(rule) for line in base.splitlines()):
        return None
    merged = base.rstrip("\n") + f"\n- {rule}\n"
    return None if len(merged) > MAX_FILE_CHARS else merged
