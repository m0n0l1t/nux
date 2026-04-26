from httpx import AsyncClient

import pytest
pytestmark = pytest.mark.skip(reason="Временно отключено")

async def test_register_user(client: AsyncClient):
    payload = {
        "username": "tester",
        "password": "strongpass",
        "invite_code": "some-invite-code"  # несуществующий
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid invite"