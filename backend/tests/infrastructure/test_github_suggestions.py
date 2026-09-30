import json

import httpx
import respx

from pairo.domain.finding import Axis, CodeSuggestion, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.github.client import GitHubClient, render_review_comment

API = "https://api.github.com"


def _finding(
    suggestion: CodeSuggestion | None, line: int | None = 5
) -> Finding:
    return Finding(
        axis=Axis.CRAFTS,
        file="a.py",
        line=line,
        issue="Bad",
        suggestion="Do better",
        source=Source.LLM,
        code_suggestion=suggestion,
    )


def test_no_suggestion_plain_comment() -> None:
    c = render_review_comment(_finding(None))
    assert "suggestion\n" not in c["body"]
    assert c == {
        "path": "a.py",
        "line": 5,
        "side": "RIGHT",
        "body": "🔧 **crafts** : Bad\n\nDo better",
    }


def test_single_line_suggestion() -> None:
    c = render_review_comment(_finding(CodeSuggestion("x = 1")))
    assert c["body"].endswith("\n\n```suggestion\nx = 1\n```")
    assert "start_line" not in c


def test_multi_line_suggestion_range() -> None:
    c = render_review_comment(_finding(CodeSuggestion("a\n\nb\nc", end_line=7)))
    assert c["body"].endswith("```suggestion\na\n\nb\nc\n```")
    assert (c["start_line"], c["start_side"]) == (5, "RIGHT")
    assert (c["line"], c["side"]) == (7, "RIGHT")


def test_empty_suggestion_plain_comment() -> None:
    c = render_review_comment(_finding(CodeSuggestion("  ")))
    assert "```" not in c["body"]


def test_backticks_in_replacement_widen_fence() -> None:
    c = render_review_comment(_finding(CodeSuggestion("s = '''\n```\n'''")))
    assert "````suggestion\n" in c["body"]
    assert c["body"].endswith("\n````")


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
