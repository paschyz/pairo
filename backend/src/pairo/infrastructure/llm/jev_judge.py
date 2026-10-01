"""Jev, OpenRouter's decision model (Decisions API, not chat): judges if a dismissal
reason is a project rule, and if .pairo.md rules exclude hard-coded rule findings."""

import logging
from typing import Any

import httpx

from pairo.domain.context_rule import NO_VERDICT, RuleVerdict
from pairo.domain.finding import Finding
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

_EXCLUDED_CRITERIA = {
    "true": (
        "A rule in project_rules explicitly allows this code or excludes this kind "
        "of finding."
    ),
    "false": "No rule in project_rules covers this finding.",
}


class JevJudge:
    def __init__(self, model: str, rate_limiter: RateLimiter, api_key: str) -> None:
        self._model = model
        self._rate_limiter = rate_limiter
        self._api_key = api_key

    async def _decide(self, questions: dict[str, Any], state: Any) -> dict[str, float]:
        """`noul` per question key. Raises on HTTP or payload errors."""
        await self._rate_limiter.acquire()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                DECISIONS_URL,
                json={"model": self._model, "questions": questions, "state": state},
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        resp.raise_for_status()
        answers = resp.json()["answers"]
        return {key: float(answers[key]["noul"]) for key in questions}

    async def judge_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleVerdict:
        state = {"file": file, "finding": finding_text, "reason": reason}
        try:
            noul = (await self._decide({_KEY: _QUESTION}, state))[_KEY]
        except Exception:
            logger.exception("Jev decision failed for %s", self._model)
            return NO_VERDICT
        logger.info("Jev durable_rule=%.2f for reason %r", noul, reason[:80])
        return RuleVerdict(persist=noul >= 0.5, confidence=noul)

    async def excluded_by_rules(
        self, project_rules: str, findings: list[Finding]
    ) -> list[bool]:
        """Per finding: does a .pairo.md rule say it must not be reported?"""
        if not findings:
            return []
        ids = [f"f{i}" for i in range(len(findings))]
        questions = {
            fid: {
                "type": "noul",
                "instructions": (
                    "Does a project rule say this finding must not be reported? "
                    f"(finding {fid})"
                ),
                "criteria": _EXCLUDED_CRITERIA,
            }
            for fid in ids
        }
        state = {
            "project_rules": project_rules,
            "findings": [
                {"id": fid, "file": f.file, "issue": f.issue}
                for fid, f in zip(ids, findings, strict=True)
            ],
        }
        try:
            nouls = await self._decide(questions, state)
        except Exception:
            # Fail open: a Jev outage must not silently hide findings.
            logger.exception("Jev rule filter failed for %s", self._model)
            return [False] * len(findings)
        excluded = [nouls[fid] >= 0.5 for fid in ids]
        logger.info("Jev excluded %d/%d rule findings", sum(excluded), len(findings))
        return excluded
