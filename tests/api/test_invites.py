import pytest
from httpx import AsyncClient
import asyncio

import pytest
pytestmark = pytest.mark.skip(reason="Временно отключено")

async def test_list_invites(client, auth_headers):
    response = await client.get("/invites", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Может быть пустым, не проверяем длину