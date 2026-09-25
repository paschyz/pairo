import pytest

from pairo.infrastructure.llm.factory import create_reviewer
from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.litellm_reviewer import LiteLLMReviewer


def test_create_fake_reviewer() -> None:
    reviewer = create_reviewer(provider="fake")
    assert isinstance(reviewer, FakeLLMReviewer)


def test_create_gemini_reviewer() -> None:
    reviewer = create_reviewer(
        provider="gemini",
        api_key="test-key",
        model="gemini-3.6-flash",
        rpm_limit=15,
    )
    assert isinstance(reviewer, LiteLLMReviewer)
    assert reviewer._model == "gemini/gemini-3.6-flash"


def test_create_litellm_reviewer() -> None:
    reviewer = create_reviewer(
        provider="litellm",
        api_key="test-key",
        model="gpt-4o",
        rpm_limit=10,
    )
    assert isinstance(reviewer, LiteLLMReviewer)
    assert reviewer._model == "gpt-4o"


def test_gemini_provider_prefixes_model() -> None:
    reviewer = create_reviewer(provider="gemini", model="gemini-2.0-flash")
    assert reviewer._model == "gemini/gemini-2.0-flash"


def test_gemini_provider_no_double_prefix() -> None:
    reviewer = create_reviewer(provider="gemini", model="gemini/gemini-2.0-flash")
    assert reviewer._model == "gemini/gemini-2.0-flash"


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="unknown"):
        create_reviewer(provider="openai")
