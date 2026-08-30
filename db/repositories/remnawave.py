from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from db.models import Service
from db.repositories.nux_service import ServiceRepository
from remnawave import RemnawaveSDK
from remnawave.models import CreateUserRequestDto
from core.config import REMNAWAVE_BASE_URL, REMNAWAVE_API, REMNAWAVE_SUB_URL, SQUAD


class RemnawaveRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        name: str,
        expiration_days: int = 30
    ) -> Service:
        remnawave = RemnawaveSDK(base_url=REMNAWAVE_BASE_URL, token=REMNAWAVE_API)
        new_user_data = CreateUserRequestDto(
            username=name,
            expire_at=datetime.now(timezone.utc) + timedelta(days=expiration_days),
            active_internal_squads=[SQUAD]
        )
        created_user = await remnawave.users.create_user(new_user_data)

        expiration = datetime.now() + timedelta(days=expiration_days)
        service = await ServiceRepository.create(
            db,
            user_id=user_id,
            service_type='remnawave',
            name=name,
            link=f"{REMNAWAVE_SUB_URL}{created_user.uuid}",
            external_id=created_user.uuid,
            server_ip=REMNAWAVE_BASE_URL,
            expiration_date=expiration,
            is_active=True
        )
        return service

    @staticmethod
    async def delete(db: AsyncSession, service: Service):
        if service.server_ip and service.external_id:
            remnawave = RemnawaveSDK(base_url=REMNAWAVE_BASE_URL, token=REMNAWAVE_API)
            try:
                await remnawave.users.delete_user(service.external_id)
            except Exception as e:
                print(f"Ошибка удаления в Remnawave: {e}")
        await ServiceRepository.delete(db, service)