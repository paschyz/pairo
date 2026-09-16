import time

import httpx
import jwt
import pytest
import respx

from pairo.infrastructure.github.auth import (
    GitHubAppAuth,
    _generate_jwt,
)

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

_DECODE_OPTS = {"verify_signature": False, "algorithms": ["RS256"]}


def test_generate_jwt() -> None:
    token = _generate_jwt(app_id=12345, private_key=_TEST_PRIVATE_KEY)
    decoded = jwt.decode(token, options=_DECODE_OPTS)
    assert decoded["iss"] == "12345"
    assert "iat" in decoded
    assert "exp" in decoded
    assert decoded["exp"] - decoded["iat"] <= 660


def test_jwt_iat_is_backdated() -> None:
    before = int(time.time())
    token = _generate_jwt(app_id=1, private_key=_TEST_PRIVATE_KEY)
    decoded = jwt.decode(token, options=_DECODE_OPTS)
    assert decoded["iat"] <= before


@pytest.fixture
def auth() -> GitHubAppAuth:
    return GitHubAppAuth(app_id=12345, private_key=_TEST_PRIVATE_KEY)


def test_auth_generates_jwt(auth: GitHubAppAuth) -> None:
    token = auth.get_jwt()
    decoded = jwt.decode(token, options=_DECODE_OPTS)
    assert decoded["iss"] == "12345"


@respx.mock
async def test_auth_get_installation_token(auth: GitHubAppAuth) -> None:
    respx.post("https://api.github.com/app/installations/999/access_tokens").mock(
        return_value=httpx.Response(
            201,
            json={
                "token": "ghs_fake_token",
                "expires_at": "2099-01-01T00:00:00Z",
            },
        )
    )
    token = await auth.get_installation_token(999)
    assert token == "ghs_fake_token"


@respx.mock
async def test_auth_caches_installation_token(auth: GitHubAppAuth) -> None:
    route = respx.post(
        "https://api.github.com/app/installations/999/access_tokens"
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "token": "ghs_cached",
                "expires_at": "2099-01-01T00:00:00Z",
            },
        )
    )
    t1 = await auth.get_installation_token(999)
    t2 = await auth.get_installation_token(999)
    assert t1 == t2 == "ghs_cached"
    assert route.call_count == 1
