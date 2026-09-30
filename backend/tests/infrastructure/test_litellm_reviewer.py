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
    findings = await reviewer.review(files, [], ["crafts"], "en")

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
    await reviewer.review(files, [], ["crafts"], "en")

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
    findings = await reviewer.review(files, [], ["crafts"], "en")

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
    await reviewer.review(files, [], ["crafts"], "en")

    call_kwargs = mock_litellm.acompletion.call_args[1]
    assert call_kwargs["api_key"] == "sk-test-123"


def test_parse_findings_code_suggestion() -> None:
    from pairo.domain.finding import CodeSuggestion

    base = {
        "axis": "crafts", "file": "a.py", "line": 1, "issue": "x", "suggestion": "y",
    }
    raw = [
        {**base, "code_suggestion": {"replacement": "z = 1", "end_line": 2}},
        {**base, "code_suggestion": "garbage"},
        base,
    ]
    got = [f.code_suggestion for f in _parse_findings(json.dumps(raw))]
    assert got == [CodeSuggestion("z = 1", end_line=2), None, None]


_ITEM = {"axis": "eco", "file": "u.py", "line": 10, "issue": "n+1", "suggestion": "join"}


def test_parse_findings_markdown_fenced_json() -> None:
    text = f"```json\n{json.dumps([_ITEM])}\n```"
    assert len(_parse_findings(text)) == 1


def test_parse_findings_prose_around_array() -> None:
    text = f"Here you go:\n{json.dumps([_ITEM])}\nHope it helps."
    assert len(_parse_findings(text)) == 1


def test_parse_findings_object_wrapper() -> None:
    assert len(_parse_findings(json.dumps({"findings": [_ITEM]}))) == 1


def test_parse_findings_coerces_string_line_numbers() -> None:
    raw = [
        {
            **_ITEM,
            "line": "10",
            "code_suggestion": {"replacement": "x", "end_line": "11"},
        },
        {**_ITEM, "line": "10-12"},
    ]
    a, b = _parse_findings(json.dumps(raw))
    assert (a.line, a.code_suggestion.end_line) == (10, 11)  # type: ignore[union-attr]
    assert b.line is None
