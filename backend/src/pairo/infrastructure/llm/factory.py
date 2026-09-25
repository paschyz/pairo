from typing import Any

from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.litellm_reviewer import LiteLLMReviewer
from pairo.infrastructure.llm.rate_limiter import RateLimiter


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
            rate_limiter=RateLimiter(rpm=rpm_limit),
            api_key=api_key,
        )
    if provider == "litellm":
        return LiteLLMReviewer(
            model=model or "gemini/gemini-2.0-flash",
            rate_limiter=RateLimiter(rpm=rpm_limit),
            api_key=api_key,
        )
    msg = f"unknown LLM provider: {provider}"
    raise ValueError(msg)
