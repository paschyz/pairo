import json
import logging
from typing import Any

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.prompt import build_prompt
from pairo.infrastructure.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_VALID_AXES = {a.value for a in Axis}


def _parse_findings(text: str) -> list[Finding]:
    try:
        raw: list[dict[str, Any]] = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Gemini returned invalid JSON: %s", text[:200])
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
                )
            )
        except (KeyError, ValueError):
            continue
    return findings


class GeminiReviewer:
    def __init__(
        self,
        client: Any,
        model: str,
        rate_limiter: RateLimiter,
    ) -> None:
        self._client = client
        self._model = model
        self._rate_limiter = rate_limiter
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0

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
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            self.last_input_tokens = (
                response.usage_metadata.prompt_token_count or 0
            )
            self.last_output_tokens = (
                response.usage_metadata.candidates_token_count or 0
            )
            return _parse_findings(response.text)
        except Exception:
            logger.exception("Gemini API call failed")
            return []
