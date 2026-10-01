"""RuleJudge on Jev, OpenRouter's decision model (Decisions API, not chat)."""

import logging

import httpx

from pairo.domain.context_rule import NO_VERDICT, RuleVerdict
from pairo.infrastructure.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
_KEY = "durable_rule"
_QUESTION = {
    "type": "noul",
    "instructions": (
        "A developer dismissed an automated code-review finding with this reason. "
        "Does the reason state a durable, project-wide convention?"
    ),
    "criteria": {
        "true": (
            "States how the whole project works: a technology it uses or does not "
            "use, a policy, or a style rule that applies beyond this code."
        ),
        "false": (
            "An exception for this line, file or PR, a promise to fix later, "
            "or no rule at all."
        ),
    },
}


class JevJudge:
    def __init__(self, model: str, rate_limiter: RateLimiter, api_key: str) -> None:
        self._model = model
        self._rate_limiter = rate_limiter
        self._api_key = api_key

    async def judge_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleVerdict:
        body = {
            "model": self._model,
            "questions": {_KEY: _QUESTION},
            "state": {"file": file, "finding": finding_text, "reason": reason},
        }
        try:
            await self._rate_limiter.acquire()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    DECISIONS_URL,
                    json=body,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            resp.raise_for_status()
            noul = float(resp.json()["answers"][_KEY]["noul"])
        except Exception:
            logger.exception("Jev decision failed for %s", self._model)
            return NO_VERDICT
        logger.info("Jev durable_rule=%.2f for reason %r", noul, reason[:80])
        return RuleVerdict(persist=noul >= 0.5, confidence=noul)
