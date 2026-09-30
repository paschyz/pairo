from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff


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
