import json
from unittest.mock import AsyncMock, Mock

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.gemini import GeminiReviewer, _parse_findings
from pairo.infrastructure.llm.rate_limiter import RateLimiter


def _make_response(findings_json: list[dict[str, object]]) -> Mock:
    resp = Mock()
    resp.text = json.dumps(findings_json)
    resp.usage_metadata = Mock()
    resp.usage_metadata.prompt_token_count = 100
    resp.usage_metadata.candidates_token_count = 50
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


async def test_gemini_reviewer_calls_api() -> None:
    mock_client = Mock()
    mock_client.aio = Mock()
    mock_client.aio.models = Mock()
    mock_client.aio.models.generate_content = AsyncMock(
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

    reviewer = GeminiReviewer(
        client=mock_client,
        model="gemini-2.0-flash",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    findings = await reviewer.review(files, [], ["crafts"], "fr")

    assert len(findings) == 1
    assert findings[0].source == Source.LLM
    mock_client.aio.models.generate_content.assert_called_once()


async def test_gemini_reviewer_tracks_tokens() -> None:
    mock_client = Mock()
    mock_client.aio = Mock()
    mock_client.aio.models = Mock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_make_response([])
    )

    reviewer = GeminiReviewer(
        client=mock_client,
        model="gemini-2.0-flash",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    await reviewer.review(files, [], ["crafts"], "fr")

    assert reviewer.last_input_tokens == 100
    assert reviewer.last_output_tokens == 50


async def test_gemini_reviewer_returns_empty_on_error() -> None:
    mock_client = Mock()
    mock_client.aio = Mock()
    mock_client.aio.models = Mock()
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    reviewer = GeminiReviewer(
        client=mock_client,
        model="gemini-2.0-flash",
        rate_limiter=RateLimiter(rpm=15),
    )
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    findings = await reviewer.review(files, [], ["crafts"], "fr")

    assert findings == []
