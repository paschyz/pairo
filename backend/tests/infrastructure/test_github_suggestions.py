import json

import httpx
import respx

from pairo.domain.finding import Axis, CodeSuggestion, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.github.client import GitHubClient, render_review_comment

API = "https://api.github.com"


def _finding(suggestion: CodeSuggestion | None, line: int | None = 5) -> Finding:
    return Finding(
        axis=Axis.CRAFTS,
        file="a.py",
        line=line,
        issue="Bad",
        suggestion="Do better",
        source=Source.LLM,
        code_suggestion=suggestion,
    )


def _no_marker(c: dict) -> str:
    return c["body"].rsplit("\n\n", 1)[0]


def test_no_suggestion_plain_comment() -> None:
    c = render_review_comment(_finding(None))
    assert "suggestion\n" not in c["body"]
    assert _no_marker(c) == "🔧 **crafts** : Bad\n\nDo better"
    assert (c["path"], c["line"], c["side"]) == ("a.py", 5, "RIGHT")
    assert c["body"].endswith(" -->")


def test_single_line_suggestion() -> None:
    c = render_review_comment(_finding(CodeSuggestion("x = 1")))
    assert _no_marker(c).endswith("\n\n```suggestion\nx = 1\n```")
    assert "start_line" not in c


def test_multi_line_suggestion_range() -> None:
    c = render_review_comment(_finding(CodeSuggestion("a\n\nb\nc", end_line=7)))
    assert _no_marker(c).endswith("```suggestion\na\n\nb\nc\n```")
    assert (c["start_line"], c["start_side"]) == (5, "RIGHT")
    assert (c["line"], c["side"]) == (7, "RIGHT")


def test_empty_suggestion_plain_comment() -> None:
    c = render_review_comment(_finding(CodeSuggestion("  ")))
    assert "```" not in c["body"]


def test_backticks_in_replacement_widen_fence() -> None:
    c = render_review_comment(_finding(CodeSuggestion("s = '''\n```\n'''")))
    assert "````suggestion\n" in c["body"]
    assert _no_marker(c).endswith("\n````")


def _review(*findings: Finding) -> Review:
    return Review(findings=list(findings))


@respx.mock
async def test_github_rejection_retries_without_suggestions() -> None:
    route = respx.post(f"{API}/repos/o/r/pulls/1/reviews").mock(
        side_effect=[
            httpx.Response(422, json={"message": "Unprocessable"}),
            httpx.Response(200, json={"id": 1}),
        ]
    )
    await GitHubClient("t").post_review(
        "o", "r", 1, _review(_finding(CodeSuggestion("x = 1")))
    )
    first, second = (json.loads(c.request.content) for c in route.calls)
    assert "```suggestion" in first["comments"][0]["body"]
    assert "```" not in second["comments"][0]["body"]
    assert "start_line" not in second["comments"][0]


@respx.mock
async def test_422_without_suggestions_still_raises() -> None:
    respx.post(f"{API}/repos/o/r/pulls/1/reviews").mock(
        return_value=httpx.Response(422, json={})
    )
    try:
        await GitHubClient("t").post_review("o", "r", 1, _review(_finding(None)))
    except httpx.HTTPStatusError:
        return
    raise AssertionError("expected HTTPStatusError")


def test_marker_matches_memory_fingerprint() -> None:
    from pairo.domain.fingerprint import fingerprint_for
    from pairo.domain.marker import parse_marker

    f = _finding(CodeSuggestion("x = 1"))
    marker = parse_marker(render_review_comment(f)["body"])
    assert marker is not None
    assert marker["fp"] == fingerprint_for(f)
    assert marker["axis"] == "crafts"
