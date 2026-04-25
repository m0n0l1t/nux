import pytest
from httpx import AsyncClient
import asyncio


@pytest.fixture
async def auth_headers(client):
    # Уникальное имя, чтобы избежать конфликтов
    import uuid
    username = f"invite_user_{uuid.uuid4().hex[:8]}"
    reg_payload = {
        "username": username,
        "password": "StrongPass123",
        "invite_code": "VALID_INVITE"
    }
    reg_resp = await client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200, f"Register failed: {reg_resp.text}"

    login_resp = await client.post("/auth/token", json={"username": username, "password": "StrongPass123"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_list_invites(client, auth_headers):
    response = await client.get("/invites", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Может быть пустым, не проверяем длину