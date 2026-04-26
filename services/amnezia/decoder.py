import json
import base64
import zlib
import gzip
import logging

logger = logging.getLogger(__name__)


def decode_vpn_config(vpn_uri: str, debug: bool = False) -> str:
    """
    Декодирует vpn:// ссылку:
    - base64 (URL-safe) -> zlib/gzip распаковка -> utf-8
    - Если результат — JSON, ищет конфигурацию в поле "config",
      которое может находиться внутри вложенных структур:
        containers[].awg.last_config.config
    Возвращает текст конфигурации WireGuard/AmneziaWG.
    """
    if not vpn_uri.startswith("vpn://"):
        # Если это не ссылка, возвращаем как есть (например, уже конфиг)
        return vpn_uri

    encoded = vpn_uri[6:]
    # Восстанавливаем корректный base64 (URL-safe -> стандартный)
    encoded = encoded.replace('-', '+').replace('_', '/')
    missing = len(encoded) % 4
    if missing:
        encoded += '=' * (4 - missing)

    try:
        # Декодируем base64
        data = base64.b64decode(encoded)
        if debug:
            logger.debug(f"Raw data length: {len(data)}, first 20: {data[:20]}")

        # Пытаемся распаковать zlib или gzip
        # 1. Поиск сигнатуры zlib (0x78 0x9c/0xda/0x01)
        zlib_pos = -1
        for i in range(len(data) - 1):
            if data[i] == 0x78 and data[i+1] in (0x9c, 0xda, 0x01):
                zlib_pos = i
                break
        if zlib_pos != -1:
            if debug:
                logger.debug(f"Found zlib at pos {zlib_pos}")
            try:
                data = zlib.decompress(data[zlib_pos:])
            except Exception as e:
                if debug:
                    logger.debug(f"zlib error: {e}")

        # 2. Поиск сигнатуры gzip (0x1f 0x8b)
        gzip_pos = -1
        for i in range(len(data) - 1):
            if data[i] == 0x1f and data[i+1] == 0x8b:
                gzip_pos = i
                break
        if gzip_pos != -1:
            if debug:
                logger.debug(f"Found gzip at pos {gzip_pos}")
            try:
                data = gzip.decompress(data[gzip_pos:])
            except Exception as e:
                if debug:
                    logger.debug(f"gzip error: {e}")

        # Если сигнатуры не нашли, пробуем распаковать всё как zlib/gzip
        if zlib_pos == -1 and gzip_pos == -1:
            try:
                data = zlib.decompress(data)
            except:
                try:
                    data = gzip.decompress(data)
                except:
                    pass

        # Декодируем в текст
        text = data.decode('utf-8')
        if debug:
            logger.debug(f"Decoded text length: {len(text)}, first 200: {text[:200]}")

        # Если текст начинается с '{', пробуем извлечь конфигурацию из JSON
        if text.strip().startswith('{'):
            try:
                root = json.loads(text)

                # 1. Ищем стандартный путь AmneziaWG: containers[].awg.last_config.config
                if "containers" in root and isinstance(root["containers"], list):
                    for cont in root["containers"]:
                        if cont.get("container") == "amnezia-awg" and "awg" in cont:
                            awg = cont["awg"]
                            if "last_config" in awg:
                                last_config_str = awg["last_config"]
                                # last_config — это JSON строка
                                try:
                                    last_config = json.loads(last_config_str)
                                    if "config" in last_config:
                                        if debug:
                                            logger.debug("Extracted config from containers[].awg.last_config.config")
                                        return last_config["config"]
                                except:
                                    pass
                # 2. Альтернатива: прямой ключ "config" на верхнем уровне
                if "config" in root:
                    if debug:
                        logger.debug("Extracted config from root.config")
                    return root["config"]

                # 3. Может быть, сам текст уже является конфигурацией?
                # Ничего не нашли — возвращаем исходный текст
                if debug:
                    logger.debug("No config field found, returning full JSON")
                return text
            except json.JSONDecodeError:
                # Не JSON — возвращаем как есть
                return text
        else:
            # Это не JSON, скорее всего уже конфигурация
            return text
    except Exception as e:
        logger.error(f"Decoding error: {e}")
        return vpn_uri
