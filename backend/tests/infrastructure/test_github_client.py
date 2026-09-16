import httpx
import respx

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.github.client import GitHubClient

API = "https://api.github.com"


def _client() -> GitHubClient:
    return GitHubClient(token="fake-token")


@respx.mock
async def test_get_pull_request_files() -> None:
    respx.get(f"{API}/repos/o/r/pulls/1/files").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "filename": "src/main.py",
                    "status": "modified",
                    "patch": "@@ -1,2 +1,3 @@\n line1\n+added\n line2",
                },
                {
                    "filename": "deleted.py",
                    "status": "removed",
                },
            ],
        )
    )
    files = await _client().get_pull_request_files("o", "r", 1)
    assert len(files) == 1
    assert files[0].path == "src/main.py"
    assert len(files[0].added_lines) == 1
    assert files[0].added_lines[0].content == "added"


@respx.mock
async def test_get_pull_request_files_ignores_lockfiles() -> None:
    respx.get(f"{API}/repos/o/r/pulls/1/files").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "filename": "package-lock.json",
                    "status": "modified",
                    "patch": "@@ -1 +1 @@\n+x",
                },
                {
                    "filename": "yarn.lock",
                    "status": "modified",
                    "patch": "@@ -1 +1 @@\n+x",
                },
            ],
        )
    )
    files = await _client().get_pull_request_files("o", "r", 1)
    assert files == []


@respx.mock
async def test_get_compare_files() -> None:
    respx.get(f"{API}/repos/o/r/compare/abc...def").mock(
        return_value=httpx.Response(
            200,
            json={
                "files": [
                    {
                        "filename": "new.ts",
                        "status": "added",
                        "patch": "@@ -0,0 +1 @@\n+export const x = 1;",
                    }
                ]
            },
        )
    )
    files = await _client().get_compare_files("o", "r", "abc", "def")
    assert len(files) == 1
    assert files[0].path == "new.ts"


@respx.mock
async def test_get_file_size_kb() -> None:
    respx.get(f"{API}/repos/o/r/contents/img.png?ref=abc").mock(
        return_value=httpx.Response(200, json={"size": 204800})
    )
    size = await _client().get_file_size_kb("o", "r", "img.png", "abc")
    assert size == 200


@respx.mock
async def test_get_repo_file() -> None:
    import base64

    content = base64.b64encode(b"axes: [crafts]").decode()
    respx.get(f"{API}/repos/o/r/contents/.pairo.yml?ref=abc").mock(
        return_value=httpx.Response(200, json={"content": content})
    )
    raw = await _client().get_repo_file("o", "r", ".pairo.yml", "abc")
    assert raw == "axes: [crafts]"


@respx.mock
async def test_get_repo_file_returns_none_on_404() -> None:
    respx.get(f"{API}/repos/o/r/contents/.pairo.yml?ref=abc").mock(
        return_value=httpx.Response(404)
    )
    raw = await _client().get_repo_file("o", "r", ".pairo.yml", "abc")
    assert raw is None


@respx.mock
async def test_post_review() -> None:
    route = respx.post(f"{API}/repos/o/r/pulls/1/reviews").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    review = Review(
        findings=[
            Finding(
                axis=Axis.A11Y,
                file="App.vue",
                line=5,
                issue="Missing alt",
                suggestion="Add alt",
                source=Source.RULE,
            )
        ]
    )
    await _client().post_review("o", "r", 1, review)
    assert route.called
    body = route.calls[0].request.content
    import json

    payload = json.loads(body)
    assert payload["event"] == "COMMENT"
    assert len(payload["comments"]) == 1
    assert payload["comments"][0]["path"] == "App.vue"
    assert payload["comments"][0]["line"] == 5


@respx.mock
async def test_post_review_no_findings() -> None:
    route = respx.post(f"{API}/repos/o/r/pulls/1/reviews").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    review = Review(findings=[])
    await _client().post_review("o", "r", 1, review)
    assert route.called
    import json

    payload = json.loads(route.calls[0].request.content)
    assert "rien à signaler" in payload["body"].lower()
    assert payload["comments"] == []
