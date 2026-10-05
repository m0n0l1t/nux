from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Service
from db.repositories.nux_service import ServiceRepository
from db.repositories.server import ServerRepository
from services.amnezia.amnesia import AmnesiaAdminClient
from services.amnezia.models_amnesia import (
    CreateClientRequest,
    DeleteClientRequest,
)
from core.logger import logger
from core.config import AMNESIA_API_KEY, AMNESIA_URL


# Единственный источник истины для протокола — чтобы не забыть поменять в трёх местах
DEFAULT_PROTOCOL = "amneziawg3"


class WireGuardRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        name: str,
        expiration_days: int = 30,
    ) -> Service:
        # 1. Выбираем сервер с минимальной нагрузкой
        server_ip = await ServerRepository.select_best_server(db)

        # 2. Определяем URL API.
        #    Если у вас несколько серверов — здесь должна быть логика
        #    выбора URL по server_ip (например, из таблицы servers).
        api_url = AMNESIA_URL

        async with AmnesiaAdminClient(
            base_url=api_url, api_key=AMNESIA_API_KEY
        ) as client:
            logger.info(
                "Создание WireGuard-клиента '%s' на сервере %s", name, server_ip
            )

            new_client = await client.create_client(
                CreateClientRequest(
                    clientName=name,
                    protocol=DEFAULT_PROTOCOL,
                )
            )

            expiration = datetime.now(timezone.utc) + timedelta(
                days=expiration_days
            )

            service = await ServiceRepository.create(
                db,
                user_id=user_id,
                service_type="wireguard",
                name=name,
                link=new_client.client.config,      # vpn://-конфиг
                external_id=new_client.client.id,   # для PATCH/DELETE
                server_ip=server_ip,
                expiration_date=expiration,
                is_active=True,
            )

            logger.info(
                "Создан клиент %s (id=%s), срок до %s",
                name,
                new_client.client.id,
                expiration.isoformat(),
            )
            return service

    @staticmethod
    async def delete(db: AsyncSession, service: Service) -> None:
        if service.server_ip and service.external_id:
            api_url = AMNESIA_URL
            async with AmnesiaAdminClient(
                base_url=api_url, api_key=AMNESIA_API_KEY
            ) as client:
                try:
                    await client.delete_client(
                        DeleteClientRequest(
                            clientId=service.external_id,
                            protocol=DEFAULT_PROTOCOL,
                        )
                    )
                    logger.info(
                        "Удалён клиент %s с сервера %s",
                        service.external_id,
                        service.server_ip,
                    )
                except httpx.HTTPStatusError as e:
                    # 404 — клиента уже нет на сервере, это не ошибка
                    if e.response.status_code == 404:
                        logger.warning(
                            "Клиент %s не найден на сервере %s, пропускаем",
                            service.external_id,
                            service.server_ip,
                        )
                    else:
                        logger.error(
                            "Ошибка удаления клиента %s: %s",
                            service.external_id,
                            e,
                        )
                        raise
                except httpx.HTTPError as e:
                    logger.error(
                        "Сетевая ошибка при удалении клиента %s: %s",
                        service.external_id,
                        e,
                    )
                    raise

        # Удаляем запись из БД
        await ServiceRepository.delete(db, service)