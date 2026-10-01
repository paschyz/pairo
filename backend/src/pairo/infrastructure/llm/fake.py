from pairo.domain.context_rule import NO_VERDICT, RuleVerdict
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff

_DURABLE_HINTS = ("always", "never", "we use", "we don't use")


class FakeLLMReviewer:
    last_input_tokens: int = 0
    last_output_tokens: int = 0
    model_name: str = "fake"

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        axis = Axis(axes[0]) if axes else Axis.CRAFTS
        for f in files:
            if not f.added_lines:
                continue
            findings.append(
                Finding(
                    axis=axis,
                    file=f.path,
                    line=f.added_lines[0].number,
                    issue="[fake] Finding detected by the fake LLM",
                    suggestion="[fake] Suggestion from the fake LLM",
                    source=Source.LLM,
                )
            )
        return findings

    async def judge_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleVerdict:
        if any(hint in reason.lower() for hint in _DURABLE_HINTS):
            return RuleVerdict(persist=True, confidence=0.9)
        return NO_VERDICT

    async def write_rule(self, reason: str, finding_text: str, file: str) -> str:
        return reason
