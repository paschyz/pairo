from dataclasses import dataclass
from enum import Enum


class Axis(str, Enum):
    CRAFTS = "crafts"
    ECO = "eco"
    A11Y = "a11y"


class Source(str, Enum):
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
