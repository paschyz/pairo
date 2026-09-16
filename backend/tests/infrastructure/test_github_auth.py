import time

import jwt
import pytest

from pairo.infrastructure.github.auth import (
    GitHubAppAuth,
    _generate_jwt,
)

# RSA key pair for tests only — not a real secret
_TEST_PRIVATE_KEY = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWep4PATsYCaJSJMqSClDoVFHdMsWzT
hBamLLGjSMExoDBhxJFkXqAWBMGSdYJzTb8NLRaRKNBEJsDFBA4CLAY3NAsEhPmT
UfFNErFHSGHOCPh+kXmJSdGW35gRPUgGONFH4K0Kq0S/vXO64bMJ3MSJXGWBQD3
MAejhH8g0OaBCPjxlOjGC+InJoIlQMFMvonblGMLDaGMcG8V8AjhIVGasoACSjRN
hAkHITmGOPSzqvV3GD0wYJj4bu3DedbqGIcLFmxJg5zzSwkz5AEkm0MYdBMPBd/P
OyZGQK8K4klROmBGTJcXIhLmfWH8f88J/V0FEQIDAQABAoIBAC5RgZ+hBx7xHNaM
pPgwGMnCd1gBnOoB2WkH0KFMjNFFfD7P/SMs3hE1f+fMdDVOFWFNh/L5gB+NRM7D
nKFMtRSGJQhtK2bMF/vfIDJdEXIXP2YY/A0L1p9YvfjjKwU7Gxb5EKrFEWOLNMBG
OaJMfr93iEGzAHMNwKCViz3TzI1nd8CwdZqAMDVzPHrBaFaE4YE8mZw7JqYRv3N8
L2Fvy1k+t0y3Dty9qVEPiVfN0bJ68IkfpKstdD1P+D44yTi0HrGzcaDTVAS7+xsF
LoF1+c5NV5OjaGMkR4M/m3mNiF7xSFllADHxbRVgyUnreZcgEkiJKMcuKLj/aN3C
kY0W3gECgYEA6N7sJ9utI2h26t78D/+NyiLIhR85l3wiItw5oGkIY7WnyNNrPlBR
hGMri9XcYNy0srVQ3+QULp6sW3FbEdP+oas9Z+mDq/PEGs2u4K4IO7K7g33BWJbR
xtbAFgjLKFcluH6MRrDlizjknKxp2EiCqPh2MFSq6i+K1cMlZlEeJECgYEA5edK
S5oF55bfiGz+gVNPzlGRisnvh/KC9vlX9CKq4NkJXkGk9bSS1c8Nf3Kf0pOJRFGG
TYBKknioJhGJPenugalMfJgaLP7w6sDEH8NJz3gB5pI5cWaVJDaQkfyTag2QeXnM
nDGPOIMBu7q4O8VKBT1dTMgPa4+V7h/q+zzXN+ECgYEA1A/LVr1r+HcG6g+SCUG8
QPpHXlXCZLhaKQAb5yCHaWlLNx/sMEv0xBHXLCFNqKVKaMS+3M3K9TNMSR/JN55S
REm3gGM3cOQx3YFnOKOQ0QJ7S38Bq1X+NR33Ga4QF5WWahd9MdxVR7T4b+qPp9xp
5qF5REXFNl1JLW6+CZqiGlECgYB7fRzh3R+olgPMyjmBRjI3sMkZqISVsBM+5ckU
qfMnEDEWxwMQ2s7SCoEVPq/FNhCfq39OBS/BPWXG4/TI8N0P72bPhAi33DzC+rKJ
c4jS9hB0b+RfXfRnTU3q0GpLJD5xXBs/kCIOonQ4TL+myqjxS+I45/ss5NM1MWLD
N1ShIQKBgQC5NVD4ToGOVGEyKjtSy+Xl4EbNJIJ9sC4j0/14u/A4q/bT1+XtURk8
aXM+i0JzEKCJ3hN2YPGFkN0jMGCMIbA0rl7J+3eDpvbWJHIHSiWsmoC+BDqII5h8
6gCdPHnL0F2QYNgCtqp/7JFo3xo8esPGFVMr1fPw+cAOlck+Ag7EaQ==
-----END RSA PRIVATE KEY-----"""


def test_generate_jwt() -> None:
    token = _generate_jwt(app_id=12345, private_key=_TEST_PRIVATE_KEY)
    decoded = jwt.decode(
        token,
        _TEST_PRIVATE_KEY,
        algorithms=["RS256"],
        options={"verify_exp": False},
    )
    assert decoded["iss"] == "12345"
    assert "iat" in decoded
    assert "exp" in decoded
    assert decoded["exp"] - decoded["iat"] <= 600


def test_jwt_iat_is_backdated() -> None:
    before = int(time.time())
    token = _generate_jwt(app_id=1, private_key=_TEST_PRIVATE_KEY)
    decoded = jwt.decode(
        token,
        _TEST_PRIVATE_KEY,
        algorithms=["RS256"],
        options={"verify_exp": False, "verify_iat": False},
    )
    assert decoded["iat"] <= before


@pytest.fixture
def auth() -> GitHubAppAuth:
    return GitHubAppAuth(app_id=12345, private_key=_TEST_PRIVATE_KEY)


def test_auth_generates_jwt(auth: GitHubAppAuth) -> None:
    token = auth.get_jwt()
    assert token
    decoded = jwt.decode(
        token,
        _TEST_PRIVATE_KEY,
        algorithms=["RS256"],
        options={"verify_exp": False},
    )
    assert decoded["iss"] == "12345"


async def test_auth_get_installation_token(
    auth: GitHubAppAuth,
) -> None:
    import httpx
    import respx

    respx.post(
        "https://api.github.com/app/installations/999/access_tokens"
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "token": "ghs_fake_token",
                "expires_at": "2099-01-01T00:00:00Z",
            },
        )
    )
    with respx.mock:
        token = await auth.get_installation_token(999)
    assert token == "ghs_fake_token"


async def test_auth_caches_installation_token(
    auth: GitHubAppAuth,
) -> None:
    import httpx
    import respx

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
    with respx.mock:
        t1 = await auth.get_installation_token(999)
        t2 = await auth.get_installation_token(999)
    assert t1 == t2 == "ghs_cached"
    assert route.call_count == 1
