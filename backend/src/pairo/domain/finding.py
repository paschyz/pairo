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


def parse_code_suggestion(raw: object) -> CodeSuggestion | None:
    """Lenient parse of untrusted (LLM / cache) data; None when malformed."""
    if not isinstance(raw, dict):
        return None
    replacement, end_line = raw.get("replacement"), raw.get("end_line")
    if not isinstance(replacement, str):
        return None
    return CodeSuggestion(
        replacement, end_line if isinstance(end_line, int) else None
    )


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
