import pytest

pytestmark = pytest.mark.skip(reason="Требуется настройка административных прав")

@pytest.fixture
def admin_headers():
    return {"X-Admin-UUID": "test-admin-uuid-12345"}  # должен соответствовать тому, что проверяет приложение

async def test_admin_create_invite(client, admin_headers):
    payload = {"expires_at": None}
    response = await client.post("/admin/invites", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "code" in data

async def test_admin_topup(client, admin_headers, db_session):
    # Сначала создадим обычного пользователя через регистрацию
    reg_payload = {"username": "topup_user", "password": "pass123", "invite_code": "VALID_INVITE"}
    await client.post("/auth/register", json=reg_payload)

    payload = {"username": "topup_user", "amount_stars": 50}
    response = await client.post("/admin/topup", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["balance_stars"] >= 50
    assert data["username"] == "topup_user"