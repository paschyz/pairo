import json
import logging
from typing import Any

import litellm

from pairo.domain.finding import Axis, Finding, Source, parse_code_suggestion
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.prompt import build_prompt
from pairo.infrastructure.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_VALID_AXES = {a.value for a in Axis}


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
    try:
        raw = _load_json(text)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON: %s", text[:200])
        return []
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
                    line=item.get("line"),
                    issue=item["issue"],
                    suggestion=item["suggestion"],
                    source=Source.LLM,
                    code_suggestion=parse_code_suggestion(
                        item.get("code_suggestion")
                    ),
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
    ) -> list[Finding]:
        prompt = build_prompt(files, existing_findings, axes, language)
        try:
            await self._rate_limiter.acquire()
            response = await litellm.acompletion(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                api_key=self._api_key,
            )
            usage = response.usage
            self.last_input_tokens = usage.prompt_tokens or 0 if usage else 0
            self.last_output_tokens = (
                usage.completion_tokens or 0 if usage else 0
            )
            text = response.choices[0].message.content or ""
            return _parse_findings(text)
        except Exception:
            logger.exception("LiteLLM call failed for model %s", self._model)
            return []
