import pytest
from httpx import AsyncClient
from db import models

async def test_create_wireguard_service(client: AsyncClient, db_session):
    # 1. Регистрация
    reg_payload = {
        "username": "wguser",
        "password": "strongpass",
        "invite_code": "VALID_INVITE"
    }
    reg_resp = await client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200

    # 2. Логин (эндпоинт /auth/token)
    login_resp = await client.post("/auth/token", json={
        "username": "wguser",
        "password": "strongpass"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Создание WireGuard-услуги
    headers = {"Authorization": f"Bearer {token}"}
    service_data = {"name": "My WG Server"}
    response = await client.post("/wireguard", json=service_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My WG Server"
    assert "id" in data
    assert "expiration_date" in data