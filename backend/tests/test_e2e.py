import hashlib
import hmac
import json

import httpx
import pytest
import respx

from pairo.config import settings

_TEST_PRIVATE_KEY = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEA0/A+6DQrqUjYLZoiWMX/aP8ETSUna3JlsmyXd8fMdLg+tdbg
2Hys0q7Hh/idN3w9Nr3Lp8fhZAnJlWrCEN8biNbFOQRnJknZiqz+mD3wcm0JI9TE
4CsxlNteUhWTmkjDLd11CSLHY1FLnTMRTMoBh0k18SwaU27GO22/OIweetTTPpom
KOrk+p/fQmGatu56tom/5pKDEER/z8oQuFAM1jea3GSRPNw6zC2DXrSRouTWX2/B
MEBQ3FHgoJZChYpyjW5no18bLRrVLdysC9C+RPw5wx+CESG1vGJLyhdlrNzJFSJ7
KOoxRNFVkmDLi/uaG6Z9c6T3OZzUNKhFVW+TcQIDAQABAoIBABVCoyjbfOrDLC5s
6RejKxMvC9EqUjlA1UtQAeTJ5exqhB3tI4qL/TE4R7tP2QOVIrXgVbLrxeQpaC+l
MTkMjIBOXSPyWV+Zpmk3H+YJRprP7cwKnsJHCvb+B4jv8anXNT8fWUt0kfBYWh+3
nPtpQzx9P1xFWpG2icux324Ofks/agLExVaKF4AuGvEjzzUrdCoCZRVlVZ3GnnMK
8NXtPK1VIbMvOksJf+b7A9+QyvGBximS2+C1hhSeBUQyAtFpMaDfwYodINfPxhke
oBIK3ChKpzkws6XQlisQS5UXQhi/eMe8DnMcGw8bcYJI+yWzfzjMyse68fZ2mg0r
FC8BPdECgYEA6g2fiCqHalq+ygbAm0tTNDSLUJyx62gWBFvJ+T5f/1tCN+Y1BtwJ
UnVFEleRUgFb+1tppWU4BBAjy1KrKk2SVBuymH0pTkWQmbN70xbdlT9z6Q+ba4Y6
em39nVTz37ft5EhQFyJUbJAHO2mJXh87qJPAJP99NKw9hc4crAO9eikCgYEA58/D
t7YKifdJBKyI6OAARbODZpp55d98hMDhrLpe2hE8FJy5bWCRr45o/0qTML6Lx3bR
TGCplkz6rW8LmV2TKnvXz21Jyba28s+PZwCxYhT9Pbvhlr3Tz6Q8zSqB0YTrkDR+
5Yh09HyeY0KXQd0Q5v7tsTnTDvIqW3bOrbDtCAkCgYBxX/wBN6i06hQ1RKQUFZ7O
UQ2TFPRSde8EWXoy0/YoegpPjaHuGrQhT1EQG373XFU0Iwm/5pIF1dOg8ACd00mo
mGog17AkjCoJahn3HMJlQ4FgSgEdSr4VBCawCbDAlBYWWLkDG8wNco8uRmcWQsbh
WADhayk5VJ3QrRDSelVUUQKBgEkUifo/zMDEEeQEVME95TgUKOfO6YEb3NCpUjw3
ITIUXuGMqzSdTjCPb/CT3SVv3PdMMR2oF67Ho/vLV1fJVVz+YAIHzUxnavPPlcD+
Se3G+jNdKPhx7fW3LGft77FS+0SiGCNayqxNIU3fr3nXLL32Po8x0KUUmV/ua6f8
cC2pAoGATY6AnzbXO+sC04dMH03eAlsPRUzDAx/AsJxTUVLWFb0BmmNo18j+0TKz
ZnEAtU/Mhuts/GkMPjqTWBYtkwtNzjWOZ8MvmEdlK8kwNWIqBMoArJsbRu9pf4ZI
gXSOyTZy1yz1mkbNY1Uuvl4nRKtQXxq9ttMuo8k2GNzAGHOddDA=
-----END RSA PRIVATE KEY-----"""

GH = "https://api.github.com"


@pytest.fixture(autouse=True)
def _e2e_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "github_app_id", 12345)
    monkeypatch.setattr(settings, "github_private_key", _TEST_PRIVATE_KEY)


def _sign(body: bytes) -> str:
    sig = hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _pr_payload(
    action: str = "opened", before: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "action": action,
        "number": 1,
        "installation": {"id": 123},
        "repository": {"full_name": "owner/repo"},
        "pull_request": {"draft": False, "head": {"sha": "abc123"}},
    }
    if before:
        payload["before"] = before
    return payload


def _mock_github_api() -> respx.Route:
    respx.post(f"{GH}/app/installations/123/access_tokens").mock(
        return_value=httpx.Response(
            201,
            json={"token": "ghs_test", "expires_at": "2099-01-01T00:00:00Z"},
        )
    )
    respx.get(f"{GH}/repos/owner/repo/pulls/1/files").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "filename": "App.vue",
                    "status": "added",
                    "patch": (
                        "@@ -0,0 +1,3 @@\n"
                        "+<template>\n"
                        '+  <img src="logo.png">\n'
                        "+</template>"
                    ),
                }
            ],
        )
    )
    respx.get(f"{GH}/repos/owner/repo/contents/.pairo.yml").mock(
        return_value=httpx.Response(404)
    )
    return respx.post(f"{GH}/repos/owner/repo/pulls/1/reviews").mock(
        return_value=httpx.Response(200, json={})
    )


@respx.mock
async def test_run_review_posts_findings() -> None:
    """E2E: _run_review → auth → fetch files → rules + LLM → post review."""
    from pairo.api.webhook import _run_review

    review_route = _mock_github_api()
    await _run_review(_pr_payload())
    assert review_route.called


@respx.mock
async def test_webhook_to_review(client: httpx.AsyncClient) -> None:
    """Full path: webhook POST → background task → review posted."""
    review_route = _mock_github_api()

    payload = _pr_payload()
    body = json.dumps(payload).encode()

    resp = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Delivery": "e2e-1",
        },
    )

    assert resp.status_code == 202
    assert review_route.called
