from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import Server, Service

class ServerRepository:
    @staticmethod
    async def get_active_servers(db: AsyncSession) -> list[Server]:
        result = await db.execute(select(Server).where(Server.is_active == True))
        return result.scalars().all()

    @staticmethod
    async def get_by_ip(db: AsyncSession, ip: str) -> Server | None:
        result = await db.execute(select(Server).where(Server.ip == ip))
        return result.scalar_one_or_none()

    @staticmethod
    async def select_best_server(db: AsyncSession) -> str:
        """
        Выбирает IP сервера с наименьшим количеством активных сервисов.
        Возвращает IP-адрес.
        """
        servers = await ServerRepository.get_active_servers(db)
        if not servers:
            raise ValueError("Нет доступных серверов")

        # Подсчёт нагрузки для каждого сервера
        load = {}
        for server in servers:
            result = await db.execute(
                select(func.count(Service.id))
                .where(Service.server_ip == server.ip)
                .where(Service.is_active == True)
            )
            count = result.scalar() or 0
            load[server.ip] = count

        # Выбираем сервер с минимальной нагрузкой
        best_ip = min(load, key=load.get)
        return best_ip