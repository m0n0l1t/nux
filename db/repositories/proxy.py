from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from db.models import Service
from db.repositories.nux_service import ServiceRepository
from db.repositories.user import UserRepository
from services.telemt.telemt import TelemtClient
from services.telemt.models_telemt import CreateUserRequest
from core.config import TELEMT_API_URL, TELEMT_AUTH_HEADER, DOMAIN_NAME, HOST_AMSTERDAM

class ProxyRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        name: str = "Proxy Service",
        expiration_days: int = 30
    ) -> Service:

        async with TelemtClient(
            base_url=TELEMT_API_URL,
            auth_header=TELEMT_AUTH_HEADER,
        ) as client:
            user = await UserRepository.get_by_id(db, user_id)
            username = user.username or f'user_{user_id}'
            try:
                current = await client.get_user(username)
                if current:
                    await client.delete_user(username)
            except Exception:
                pass

            new_user = await client.create_user(CreateUserRequest(username=username))
            proxy_link = new_user.user.links.tls[0].replace(HOST_AMSTERDAM, DOMAIN_NAME)

            expiration = datetime.now() + timedelta(days=expiration_days)
            service = await ServiceRepository.create(
                db,
                user_id=user_id,
                service_type='proxy',
                name=name,
                link=proxy_link,
                external_id=None,  # Telemt не требует external_id для удаления? Можно использовать username.
                server_ip=None,
                expiration_date=expiration,
                is_active=True
            )
            return service

    @staticmethod
    async def delete(db: AsyncSession, service: Service):
        # Удаляем внешний ресурс (если нужно)
        # Например, через TelemtClient.delete_user(service.name)
        # Для простоты пропускаем, но можно реализовать.
        await ServiceRepository.delete(db, service)