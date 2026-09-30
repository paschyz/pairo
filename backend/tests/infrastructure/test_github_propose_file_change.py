import base64
import json

import httpx
import pytest
import respx

from pairo.infrastructure.github.client import GitHubClient

API = "https://api.github.com/repos/o/r"
PR_URL = "https://github.com/o/r/pull/9"

_ARGS = {
    "default_branch": "main",
    "branch": "pairo/context",
    "path": ".pairo.md",
    "content": "# Pairo context\n- Use Vue\n",
    "message": "docs: update .pairo.md",
    "title": "Add Pairo context rule",
    "body": "body",
}


def _client() -> GitHubClient:
    return GitHubClient(token="fake-token")


@respx.mock
async def test_creates_branch_file_and_pr() -> None:
    respx.get(f"{API}/git/ref/heads/pairo/context").respond(404)
    respx.get(f"{API}/git/ref/heads/main").respond(200, json={"object": {"sha": "abc"}})
    create_ref = respx.post(f"{API}/git/refs").respond(201, json={})
    respx.get(f"{API}/contents/.pairo.md").respond(404)
    put = respx.put(f"{API}/contents/.pairo.md").respond(201, json={})
    respx.get(f"{API}/pulls").respond(200, json=[])
    create_pr = respx.post(f"{API}/pulls").respond(201, json={"html_url": PR_URL})

    url = await _client().propose_file_change("o", "r", **_ARGS)

    assert url == PR_URL
    assert json.loads(create_ref.calls[0].request.content) == {
        "ref": "refs/heads/pairo/context",
        "sha": "abc",
    }
    put_body = json.loads(put.calls[0].request.content)
    assert "sha" not in put_body
    assert put_body["branch"] == "pairo/context"
    assert base64.b64decode(put_body["content"]).decode() == _ARGS["content"]
    pr_body = json.loads(create_pr.calls[0].request.content)
    assert pr_body["head"] == "pairo/context"
    assert pr_body["base"] == "main"


@respx.mock
async def test_reuses_existing_branch_and_open_pr() -> None:
    respx.get(f"{API}/git/ref/heads/pairo/context").respond(200, json={})
    create_ref = respx.post(f"{API}/git/refs").respond(201, json={})
    respx.get(f"{API}/contents/.pairo.md").respond(200, json={"sha": "filesha"})
    put = respx.put(f"{API}/contents/.pairo.md").respond(200, json={})
    respx.get(f"{API}/pulls").respond(200, json=[{"html_url": PR_URL}])
    create_pr = respx.post(f"{API}/pulls").respond(201, json={})

    url = await _client().propose_file_change("o", "r", **_ARGS)

    assert url == PR_URL
    assert not create_ref.called
    assert not create_pr.called
    assert json.loads(put.calls[0].request.content)["sha"] == "filesha"


@respx.mock
async def test_missing_permissions_raise() -> None:
    respx.get(f"{API}/git/ref/heads/pairo/context").respond(200, json={})
    respx.get(f"{API}/contents/.pairo.md").respond(404)
    respx.put(f"{API}/contents/.pairo.md").respond(403, json={"message": "forbidden"})

    with pytest.raises(httpx.HTTPStatusError):
        await _client().propose_file_change("o", "r", **_ARGS)
