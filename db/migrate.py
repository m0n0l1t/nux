"""
Скрипт для применения миграций Alembic.
Запускать при изменениях моделей.
"""

import subprocess
import sys
import os

# Путь к python в venv
VENV_PYTHON = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")

def run_migrations():
    """Применяет все ожидающие миграции Alembic"""
    print("🔄 Применяю миграции Alembic...")
    
    result = subprocess.run(
        [VENV_PYTHON, "-m", "alembic", "upgrade", "head"],
        cwd=os.path.dirname(__file__)
    )
    
    if result.returncode == 0:
        print("✅ Миграции применены успешно!")
    else:
        print("❌ Ошибка применения миграций")
        sys.exit(1)


def create_migration(message: str):
    """Создаёт новую миграцию с сообщением"""
    print(f"📝 Создаю миграцию: {message}")
    
    result = subprocess.run(
        [VENV_PYTHON, "-m", "alembic", "revision", "--autogenerate", "-m", message],
        cwd=os.path.dirname(__file__)
    )
    
    if result.returncode == 0:
        print("✅ Миграция создана!")
        print("💡 Теперь запусти: python migrate.py apply")
    else:
        print("❌ Ошибка создания миграции")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  {sys.argv[0]} apply              - применить миграции")
        print(f"  {sys.argv[0]} create <message>    - создать миграцию")
        print(f"\nПримеры:")
        print(f"  {sys.argv[0]} apply")
        print(f"  {sys.argv[0]} create \"add new field to user\"")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "apply":
        run_migrations()
    elif command == "create" and len(sys.argv) >= 3:
        message = " ".join(sys.argv[2:])
        create_migration(message)
    else:
        print("❌ Неверная команда")
        print(f"Использование: {sys.argv[0]} apply | create <message>")
