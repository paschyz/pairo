from functools import lru_cache
from typing import Any

from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.litellm_reviewer import LiteLLMReviewer
from pairo.infrastructure.llm.rate_limiter import RateLimiter


@lru_cache
def _shared_limiter(provider: str, rpm: int) -> RateLimiter:
    # The RPM quota is per API key, so the limiter must outlive a single webhook.
    # ponytail: per-process only; with several workers use a shared store (Redis).
    return RateLimiter(rpm=rpm)


def create_reviewer(
    provider: str,
    api_key: str = "",
    model: str = "",
    rpm_limit: int = 15,
) -> Any:
    if provider == "fake":
        return FakeLLMReviewer()
    if provider == "gemini":
        model_name = model or "gemini-2.0-flash"
        if not model_name.startswith("gemini/"):
            model_name = f"gemini/{model_name}"
        return LiteLLMReviewer(
            model=model_name,
            rate_limiter=_shared_limiter(provider, rpm_limit),
            api_key=api_key,
        )
    if provider == "openrouter":
        model_name = model or "anthropic/claude-haiku-4.5"
        if not model_name.startswith("openrouter/"):
            model_name = f"openrouter/{model_name}"
        return LiteLLMReviewer(
            model=model_name,
            rate_limiter=_shared_limiter(provider, rpm_limit),
            api_key=api_key,
        )
    if provider == "litellm":
        return LiteLLMReviewer(
            model=model or "gemini/gemini-2.0-flash",
            rate_limiter=_shared_limiter(provider, rpm_limit),
            api_key=api_key,
        )
    msg = f"unknown LLM provider: {provider}"
    raise ValueError(msg)
