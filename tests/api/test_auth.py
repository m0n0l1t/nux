from httpx import AsyncClient


async def test_register_user(client: AsyncClient):
    payload = {
        "username": "tester",
        "password": "strongpass",
        "invite": "some-invite-code"  # В реальности нужно заранее создать инвайт в БД
    }
    response = await client.post("/auth/register", json=payload)
    # Ожидаем, что invite невалиден — вернёт 400
    assert response.status_code == 400
    assert "Invalid invite code" in response.text