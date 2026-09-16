import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")

from pairo.app import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_webhook_state() -> None:
    from pairo.api.webhook import _seen_deliveries

    _seen_deliveries.clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
