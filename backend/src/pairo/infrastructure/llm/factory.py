from typing import Any

from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.gemini import GeminiReviewer
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
        from google import genai

        client = genai.Client(api_key=api_key)
        return GeminiReviewer(
            client=client,
            model=model or "gemini-2.0-flash",
            rate_limiter=RateLimiter(rpm=rpm_limit),
        )
    msg = f"unknown LLM provider: {provider}"
    raise ValueError(msg)
