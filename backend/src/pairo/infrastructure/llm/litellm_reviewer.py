import json
import logging
from typing import Any

import litellm

from pairo.domain.context_rule import NO_VERDICT, RuleVerdict
from pairo.domain.finding import (
    Axis,
    Finding,
    Source,
    parse_code_suggestion,
    parse_line,
)
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.prompt import build_prompt
from pairo.infrastructure.llm.rate_limiter import RateLimiter
from pairo.infrastructure.llm.rule_classifier import (
    build_judge_prompt,
    build_write_prompt,
    parse_rule,
    parse_verdict,
)

logger = logging.getLogger(__name__)

_VALID_AXES = {a.value for a in Axis}
# Bound the call: a hung provider must not hold a review (and the limiter) for long.
_TIMEOUT_S = 60
_RETRIES = 2


def _load_json(text: str) -> Any:
    """Parse the model output, tolerating ```json fences and surrounding prose."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        raise json.JSONDecodeError("no JSON array found", text, 0)
    return json.loads(text[start : end + 1])


def _parse_findings(text: str) -> list[Finding]:
    """Raises on unreadable output: that is a failed review, not a clean one."""
    try:
        raw = _load_json(text)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON: %s", text[:200])
        raise
    if isinstance(raw, dict):
        raw = raw.get("findings", [])
    if not isinstance(raw, list):
        return []

    findings: list[Finding] = []
    for item in raw:
        try:
            axis = item["axis"]
            if axis not in _VALID_AXES:
                continue
            findings.append(
                Finding(
                    axis=Axis(axis),
                    file=item["file"],
                    line=parse_line(item.get("line")),
                    issue=item["issue"],
                    suggestion=item["suggestion"],
                    source=Source.LLM,
                    code_suggestion=parse_code_suggestion(item.get("code_suggestion")),
                )
            )
        except (KeyError, ValueError):
            continue
    return findings


class LiteLLMReviewer:
    def __init__(
        self,
        model: str,
        rate_limiter: RateLimiter,
        api_key: str = "",
    ) -> None:
        self._model = model
        self._rate_limiter = rate_limiter
        self._api_key = api_key or None
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0
        self.model_name: str = model

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
        project_context: str = "",
    ) -> list[Finding]:
        """Raises when the call or its output fails, so the caller can say so
        on the PR instead of posting an empty review that reads as "all clear"."""
        prompt = build_prompt(files, existing_findings, axes, language, project_context)
        response = await self._complete(prompt)
        usage = response.usage
        self.last_input_tokens = usage.prompt_tokens or 0 if usage else 0
        self.last_output_tokens = usage.completion_tokens or 0 if usage else 0
        return _parse_findings(response.choices[0].message.content or "")

    async def _complete(self, prompt: str) -> Any:
        await self._rate_limiter.acquire()
        return await litellm.acompletion(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            api_key=self._api_key,
            timeout=_TIMEOUT_S,
            num_retries=_RETRIES,
        )

    async def _json_call(self, prompt: str) -> str | None:
        """Raw JSON answer, or None when the LLM call fails."""
        try:
            response = await self._complete(prompt)
            return response.choices[0].message.content or ""
        except Exception:
            logger.exception("LiteLLM rule call failed for %s", self._model)
            return None

    async def judge_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleVerdict:
        text = await self._json_call(build_judge_prompt(reason, finding_text, file))
        return NO_VERDICT if text is None else parse_verdict(text)

    async def write_rule(self, reason: str, finding_text: str, file: str) -> str:
        text = await self._json_call(build_write_prompt(reason, finding_text, file))
        return "" if text is None else parse_rule(text)
