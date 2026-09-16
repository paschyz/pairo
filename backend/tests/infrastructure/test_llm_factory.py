import pytest

from pairo.infrastructure.llm.factory import create_reviewer
from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.gemini import GeminiReviewer


def test_create_fake_reviewer() -> None:
    reviewer = create_reviewer(provider="fake")
    assert isinstance(reviewer, FakeLLMReviewer)


def test_create_gemini_reviewer() -> None:
    reviewer = create_reviewer(
        provider="gemini",
        api_key="test-key",
        model="gemini-2.0-flash",
        rpm_limit=15,
    )
    assert isinstance(reviewer, GeminiReviewer)


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="unknown"):
        create_reviewer(provider="openai")
