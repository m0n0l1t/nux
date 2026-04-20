from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Тест health check эндпоинта"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Application is running"}


def test_read_main():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Restaurant" in response.text
    assert "<!doctype html>" in response.text.lower()


def test_static_files():
    """Тест доступности статических файлов"""
    response = client.get("/assets/css/main.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
