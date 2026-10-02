"""Token pricing, read from the price table litellm ships."""

from functools import lru_cache

import litellm


@lru_cache(maxsize=64)
def _rates(model: str) -> tuple[float, float] | None:
    """USD per (input, output) token, or None when litellm has no price for it."""
    try:
        return litellm.cost_per_token(model=model, prompt_tokens=1, completion_tokens=1)
    except Exception:
        return None


def cost_usd(model: str | None, input_tokens: int, output_tokens: int) -> float | None:
    # ponytail: base-tier rate from today's litellm table, applied at read time.
    # Persist a cost_usd column at review time if historical prices or the
    # >200k-token tier start to matter.
    rates = _rates(model) if model else None
    if rates is None:
        return None
    return input_tokens * rates[0] + output_tokens * rates[1]
