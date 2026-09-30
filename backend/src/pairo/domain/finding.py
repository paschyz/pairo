from dataclasses import dataclass
from enum import StrEnum


class Axis(StrEnum):
    CRAFTS = "crafts"
    ECO = "eco"
    A11Y = "a11y"


class Source(StrEnum):
    RULE = "rule"
    LLM = "llm"


@dataclass(frozen=True)
class CodeSuggestion:
    """Directly applicable replacement for lines [finding.line, end_line]."""

    replacement: str
    end_line: int | None = None


def parse_line(raw: object) -> int | None:
    """Lenient line number parse of untrusted data ("10" -> 10); None if not one."""
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw)
    return None


def parse_code_suggestion(raw: object) -> CodeSuggestion | None:
    """Lenient parse of untrusted (LLM / cache) data; None when malformed."""
    if not isinstance(raw, dict):
        return None
    replacement = raw.get("replacement")
    if not isinstance(replacement, str):
        return None
    return CodeSuggestion(replacement, parse_line(raw.get("end_line")))


@dataclass(frozen=True)
class Finding:
    axis: Axis
    file: str
    line: int | None
    issue: str
    suggestion: str
    source: Source
    category: str = ""
    code_suggestion: CodeSuggestion | None = None
