"""Turn a durable reviewer instruction into one line of .pairo.md. Pure domain."""

from dataclasses import dataclass

MAX_RULE_CHARS = 280
MAX_FILE_CHARS = 8000
HEADER = "# Pairo context"
_TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}


@dataclass(frozen=True)
class RuleVerdict:
    persist: bool
    confidence: float


NO_VERDICT = RuleVerdict(persist=False, confidence=0.0)


def is_trusted(author_association: str | None) -> bool:
    return author_association in _TRUSTED


def _clean(rule: str) -> str:
    return " ".join(rule.split())[:MAX_RULE_CHARS].strip()


def accept(verdict: RuleVerdict, threshold: float) -> bool:
    return verdict.persist and verdict.confidence >= threshold


def _norm(line: str) -> str:
    return " ".join(line.lstrip("-* ").split()).lower()


def merge_rule(existing: str | None, rule: str) -> str | None:
    """Append `rule` to the file. None if blank, duplicate or the file is full."""
    rule = _clean(rule)
    if not rule:
        return None
    base = existing if existing else HEADER + "\n"
    if any(_norm(line) == _norm(rule) for line in base.splitlines()):
        return None
    merged = base.rstrip("\n") + f"\n- {rule}\n"
    return None if len(merged) > MAX_FILE_CHARS else merged
