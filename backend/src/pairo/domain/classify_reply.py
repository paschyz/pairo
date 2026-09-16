"""Reply classification schema for LLM-based rejection detection. Pure domain."""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_VALID_VERDICTS = {"rejects", "accepts", "unclear"}
_HIGH_CONFIDENCE = 0.8


@dataclass(frozen=True)
class ReplyClassification:
    fingerprint: str
    verdict: str  # "rejects" | "accepts" | "unclear"
    confidence: float

    def is_rejection(self) -> bool:
        return (
            self.verdict == "rejects"
            and self.confidence >= _HIGH_CONFIDENCE
        )


def parse_classifications(raw: str) -> list[ReplyClassification]:
    """Parse LLM JSON response into classifications. Tolerant."""
    try:
        items = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid classification JSON: %s", raw[:200])
        return []

    results: list[ReplyClassification] = []
    for item in items:
        try:
            verdict = item["verdict"]
            if verdict not in _VALID_VERDICTS:
                continue
            results.append(
                ReplyClassification(
                    fingerprint=item["fingerprint"],
                    verdict=verdict,
                    confidence=float(item["confidence"]),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    return results
