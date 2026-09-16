import logging
import time
from datetime import UTC, datetime

import httpx
import jwt

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _generate_jwt(app_id: int, private_key: str) -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": str(app_id),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


class GitHubAppAuth:
    def __init__(self, app_id: int, private_key: str) -> None:
        self._app_id = app_id
        self._private_key = private_key
        self._token_cache: dict[int, tuple[str, datetime]] = {}

    def get_jwt(self) -> str:
        return _generate_jwt(self._app_id, self._private_key)

    async def get_installation_token(self, installation_id: int) -> str:
        cached = self._token_cache.get(installation_id)
        if cached:
            token, expires_at = cached
            if expires_at > datetime.now(UTC):
                return token

        token_jwt = self.get_jwt()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {token_jwt}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()

        data: dict[str, str] = resp.json()
        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"])
        self._token_cache[installation_id] = (token, expires_at)
        return token
