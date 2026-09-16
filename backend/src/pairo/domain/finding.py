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
class Finding:
    axis: Axis
    file: str
    line: int | None
    issue: str
    suggestion: str
    source: Source
