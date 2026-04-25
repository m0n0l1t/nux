from httpx import AsyncClient
from db import models


async def test_create_wireguard_service(client: AsyncClient, db_session):
    user = models.User(username="wguser")  # Создайте пользователя через db_session
    db_session.add(user)
    await db_session.commit()

    ws_data = {"name": "My WG Server", "user_id": user.id}
    response = await client.post("/wireguard/create", json=ws_data)
    assert response.status_code == 200
    assert "config" in response.json()
    assert "private_key" in response.json()["config"]