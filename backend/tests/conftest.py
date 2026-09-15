from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from pairo.app import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
