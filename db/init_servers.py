from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Server
from core.config import SERVERS_IP_LIST

# async def init_servers(db: AsyncSession):
#     """
#     Синхронизирует таблицу servers с настройками из .env.
#     Добавляет новые серверы, обновляет max_services, если изменилось.
#     Не удаляет серверы, которые есть в БД, но отсутствуют в .env (на случай, если они используются).
#     """
#     ips = [ip.strip() for ip in SERVERS_IP_LIST.split(",") if ip.strip()]
#     env_servers = [{"ip": ip, "max_services": 100} for ip in ips]
#
#     if not env_servers:
#         return
#
#     ip = env_servers[0]
#         max_services = ip.get("max_services", 100)
#
#         # Ищем существующий сервер
#         result = await db.execute(select(Server).where(Server.ip == ip))
#         server = result.scalar_one_or_none()
#
#         if server:
#             # Обновляем лимит, если изменился
#             if server.max_services != max_services:
#                 server.max_services = max_services
#         else:
#             # Создаём новый
#             new_server = Server(ip=ip, max_services=max_services, is_active=True)
#             db.add(new_server)
#
#     await db.commit()