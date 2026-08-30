from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from db.models import Service, User

class ServiceRepository:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Service:
        service = Service(**kwargs)
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

    @staticmethod
    async def get_by_id(db: AsyncSession, service_id: int, user_id: int | None = None) -> Service | None:
        query = select(Service).where(Service.id == service_id)
        if user_id is not None:
            query = query.where(Service.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[Service]:
        result = await db.execute(
            select(Service)
            .where(Service.user_id == user_id)
            .order_by(Service.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: int) -> list[Service]:
        """Получить все сервисы пользователя по telegram_id."""
        result = await db.execute(
            select(Service)
            .join(User, Service.user_id == User.id)
            .where(User.telegram_id == telegram_id)
            .order_by(Service.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, service: Service, **kwargs) -> Service:
        for key, value in kwargs.items():
            if hasattr(service, key):
                setattr(service, key, value)
        service.updated_at = datetime.now()
        await db.commit()
        await db.refresh(service)
        return service

    @staticmethod
    async def deactivate(db: AsyncSession, service: Service) -> Service:
        service.is_active = False
        service.updated_at = datetime.now()
        await db.commit()
        await db.refresh(service)
        return service

    @staticmethod
    async def delete(db: AsyncSession, service: Service):
        await db.delete(service)
        await db.commit()

    @staticmethod
    async def get_by_user_name_type(
            db: AsyncSession,
            user_id: int,
            name: str,
            service_type: str
    ) -> Service | None:
        """
        Находит сервис по user_id, name и service_type.
        Возвращает Service или None.
        """
        result = await db.execute(
            select(Service)
            .where(
                and_(
                    Service.user_id == user_id,
                    Service.name == name,
                    Service.service_type == service_type
                )
            )
        )
        return result.scalar_one_or_none()