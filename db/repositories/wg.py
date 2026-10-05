from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from db.models import Service
from db.repositories.nux_service import ServiceRepository
from db.repositories.server import ServerRepository
from services.amnezia.amnesia import AmnesiaAdminClient
from services.amnezia.models_amnesia import CreateClientRequest, DeleteClientRequest
from services.amnezia.decoder import logger
from core.config import AMNESIA_API_KEY, AMNESIA_URL

class WireGuardRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        name: str,
        expiration_days: int = 30
    ) -> Service:
        # 1. Выбираем сервер с минимальной нагрузкой
        server_ip = await ServerRepository.select_best_server(db)

        # 2. Формируем URL API для этого сервера (шаблон из конфига)
        api_url = AMNESIA_URL

        async with AmnesiaAdminClient(base_url=api_url, api_key=AMNESIA_API_KEY) as client:
            logger.info(f"Создание WireGuard на сервере {server_ip}")
            new_client = await client.create_client(
                CreateClientRequest(clientName=name, protocol="amneziawg2")
            )

            expiration = datetime.now() + timedelta(days=expiration_days)
            service = await ServiceRepository.create(
                db,
                user_id=user_id,
                service_type='wireguard',
                name=name,
                link=new_client.client.config,        # или декодированный конфиг
                external_id=new_client.client.id,     # для удаления/обновления
                server_ip=server_ip,
                expiration_date=expiration,
                is_active=True
            )
            return service

    @staticmethod
    async def delete(db: AsyncSession, service: Service):
        if service.server_ip and service.external_id:
            api_url = AMNESIA_URL
            async with AmnesiaAdminClient(base_url=api_url, api_key=AMNESIA_API_KEY) as client:
                try:
                    await client.delete_client(
                        DeleteClientRequest(clientId=service.external_id, protocol="amneziawg2")
                    )
                    logger.info(f"Удалён клиент {service.external_id} с сервера {service.server_ip}")
                except Exception as e:
                    logger.error(f"Ошибка удаления клиента: {e}")
        # Удаляем запись из БД
        await ServiceRepository.delete(db, service)