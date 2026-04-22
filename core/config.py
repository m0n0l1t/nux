import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


def get_required_env(key: str, default: Optional[str] = None) -> str:
    """Получение обязательной переменной окружения"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


# API URLs и ключи
HOST_MOSCOW = os.getenv("HOST_MOSCOW")
HOST_AMSTERDAM = os.getenv("HOST_AMSTERDAM")

AMNESIA_API_URL = f"http://{HOST_AMSTERDAM}:4001" if HOST_AMSTERDAM else None
AMNESIA_API_KEY = os.getenv("AMNESIA_API_KEY")
TELEMT_API_URL = f"http://{HOST_AMSTERDAM}:9091" if HOST_AMSTERDAM else None
TELEMT_AUTH_HEADER = os.getenv("TELEMT_AUTH_HEADER")

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bot.db")
CLIENTS_DIR = os.path.join(BASE_DIR, "data", "clients")
INSTRUCTION_PATH = os.path.join(BASE_DIR, "data", "instruction.pdf")
QR_IMAGE_PATH = os.path.join(BASE_DIR, "qr.png")

# Создаём папки, если их нет
os.makedirs(CLIENTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(INSTRUCTION_PATH), exist_ok=True)

# JWT настройки
import os
# В режиме разработки используемdefault значения, но с предупреждением
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY_DEV", "dev-secret-key-change-in-prod")
if "SECRET_KEY" not in os.environ and "SECRET_KEY_DEV" not in os.environ:
    print("⚠️  WARNING: SECRET_KEY не установлен. Используется insecure default!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

# Домен
DOMAIN_NAME = os.getenv("DOMAIN_NAME")

# Токен бота (может использоваться в bot.py)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ========== ТАРИФЫ И ЦЕНЫ ==========
# Цена WireGuard в звёздах за месяц
WIREGUARD_PRICE_STARS = 3

# Прокси бесплатен при наличии WireGuard
PROXY_PRICE_STARS = 0  # Бесплатно

# Типы тарифов: unlimited (безлимит) и limited (лимитный)
# Для limited можно настроить ограничения по трафику
TARIFF_TYPES = {
    "unlimited": {
        "name": "Безлимитный",
        "description": "Без ограничений по трафику",
        "price_stars": WIREGUARD_PRICE_STARS
    },
    "limited": {
        "name": "Лимитный", 
        "description": "С ограничением по трафику (в разработке)",
        "price_stars": WIREGUARD_PRICE_STARS  # Пока та же цена
    }
}

# Период оплаты (дней)
SUBSCRIPTION_PERIOD_DAYS = 30


def validate_config():
    """Проверка критичных настроек"""
    warnings = []
    errors = []
    
    if SECRET_KEY == "default-secret-change-me-in-production":
        warnings.append("⚠️  SECRET_KEY использует значение по умолчанию!")
    
    if not BOT_TOKEN:
        warnings.append("⚠️  BOT_TOKEN не установлен (бот не будет работать)")
    
    if not DOMAIN_NAME:
        warnings.append("⚠️  DOMAIN_NAME не установлен")
    
    if not AMNESIA_API_KEY:
        warnings.append("⚠️  AMNESIA_API_KEY не установлен (WireGuard не будет работать)")
    
    return {"warnings": warnings, "errors": errors}
