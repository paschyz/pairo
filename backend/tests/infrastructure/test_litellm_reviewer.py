import json
from unittest.mock import AsyncMock, Mock, patch

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.litellm_reviewer import LiteLLMReviewer, _parse_findings
from pairo.infrastructure.llm.rate_limiter import RateLimiter


def _make_response(findings_json: list[dict[str, object]]) -> Mock:
    usage = Mock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50

    message = Mock()
    message.content = json.dumps(findings_json)

    choice = Mock()
    choice.message = message

    resp = Mock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def test_parse_findings_valid() -> None:
    raw = [
        {
            "axis": "crafts",
            "file": "app.py",
            "line": 1,
            "issue": "bad name",
            "suggestion": "rename",
        }
    ]
    findings = _parse_findings(json.dumps(raw))
    assert len(findings) == 1
    assert findings[0].axis == Axis.CRAFTS
    assert findings[0].source == Source.LLM
    assert findings[0].file == "app.py"


def test_parse_findings_empty_array() -> None:
    assert _parse_findings("[]") == []


def test_parse_findings_malformed_json() -> None:
    assert _parse_findings("not json") == []


def test_parse_findings_skips_invalid_entries() -> None:
    raw = [
        {"axis": "crafts", "file": "a.py", "line": 1, "issue": "x", "suggestion": "y"},
        {"bad": "entry"},
    ]
    findings = _parse_findings(json.dumps(raw))
    assert len(findings) == 1


def test_parse_findings_null_line() -> None:
    raw = [
        {
            "axis": "eco",
            "file": "a.py",
            "line": None,
            "issue": "heavy dep",
            "suggestion": "remove",
        }
    ]
    findings = _parse_findings(json.dumps(raw))
    assert len(findings) == 1
    assert findings[0].line is None


@patch("pairo.infrastructure.llm.litellm_reviewer.litellm")
async def test_litellm_reviewer_calls_api(mock_litellm: Mock) -> None:
    mock_litellm.acompletion = AsyncMock(
        return_value=_make_response(
            [
                {
                    "axis": "crafts",
                    "file": "app.py",
                    "line": 1,
                    "issue": "bad",
                    "suggestion": "fix",
                }
            ]
        )
    )

    reviewer = LiteLLMReviewer(
        model="gpt-4o",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    findings = await reviewer.review(files, [], ["crafts"], "fr")

    assert len(findings) == 1
    assert findings[0].source == Source.LLM
    mock_litellm.acompletion.assert_called_once()


@patch("pairo.infrastructure.llm.litellm_reviewer.litellm")
async def test_litellm_reviewer_tracks_tokens(mock_litellm: Mock) -> None:
    mock_litellm.acompletion = AsyncMock(return_value=_make_response([]))

    reviewer = LiteLLMReviewer(
        model="gpt-4o",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    await reviewer.review(files, [], ["crafts"], "fr")

    assert reviewer.last_input_tokens == 100
    assert reviewer.last_output_tokens == 50


@patch("pairo.infrastructure.llm.litellm_reviewer.litellm")
async def test_litellm_reviewer_returns_empty_on_error(mock_litellm: Mock) -> None:
    mock_litellm.acompletion = AsyncMock(side_effect=Exception("API error"))

    reviewer = LiteLLMReviewer(
        model="gpt-4o",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    findings = await reviewer.review(files, [], ["crafts"], "fr")

    assert findings == []


@patch("pairo.infrastructure.llm.litellm_reviewer.litellm")
async def test_litellm_reviewer_passes_api_key(mock_litellm: Mock) -> None:
    mock_litellm.acompletion = AsyncMock(return_value=_make_response([]))

    reviewer = LiteLLMReviewer(
        model="gpt-4o",
        rate_limiter=RateLimiter(rpm=15),
        api_key="sk-test-123",
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    await reviewer.review(files, [], ["crafts"], "fr")

    call_kwargs = mock_litellm.acompletion.call_args[1]
    assert call_kwargs["api_key"] == "sk-test-123"
