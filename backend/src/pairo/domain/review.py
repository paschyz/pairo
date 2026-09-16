from collections import Counter
from dataclasses import dataclass, field

from pairo.domain.finding import Axis, Finding


@dataclass
class Review:
    findings: list[Finding] = field(default_factory=list)
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    co2_g: float | None = None

    def counts_by_axis(self) -> dict[Axis, int]:
        if not self.findings:
            return {}
        return dict(Counter(f.axis for f in self.findings))

    @property
    def total(self) -> int:
        return len(self.findings)
