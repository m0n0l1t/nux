from httpx import AsyncClient


# ---------- Тесты ----------
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data


async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    # Если корень возвращает что-то (редирект или HTML)
    assert response.headers["content-type"] == "text/html; charset=utf-8"


async def test_docs_available(client: AsyncClient):
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
