import requests
import yaml

def get_routes_from_config() -> list[str]:
    # Читаем конфигурационный файл
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    # Возвращаем список всех роутов из конфигурационного файла
    return [route["url"] for route in config["routes"]]

def check_all_routes(db) -> None:
    # Получаем список всех роутов из конфигурационного файла (имплицитно подразумевается)
    routes = get_routes_from_config()
    for route in routes:
        # Проверяем, работает ли роут корректно
        response = requests.get(route)
        if response.status_code != 200:
            print(f"Роут {route} не работает корректно. Статус код: {response.status_code}")

def test_health_check():
    """Тест health check эндпоинта"""
    response = requests.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Application is running"}

def test_read_main():
    """Тест главной страницы"""
    response = requests.get("/")
    assert response.status_code == 200
    assert "Restaurant" in response.text
    assert "<!doctype html>" in response.text.lower()

def test_static_files():
    """Тест доступности статических файлов"""
    response = requests.get("/assets/css/main.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]

def main():
    # Проверяем все роуты без базы данных (сессия)
    check_all_routes(None)

if __name__ == "__main__":
    test_health_check()
    test_read_main()
    test_static_files()

# def create_db_session() -> None:
#     # Создаём сессию БД
#     return None  # в данный момент не используется

def main():
    print("Тесты выполнены успешно.")
