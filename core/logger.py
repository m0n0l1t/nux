import logging
import sys


def setup_logging():
    # Принудительно устанавливаем UTF-8 для вывода
    if sys.platform == 'win32':
        # Для Windows используем UTF-8
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log", encoding='utf-8'),  # Явно указываем UTF-8
            logging.StreamHandler(sys.stdout)  # Используем stdout с UTF-8
        ]
    )
    return logging.getLogger("nux_bot")
# ОДИН ГЛОБАЛЬНЫЙ ЛОГГЕР
logger = setup_logging()