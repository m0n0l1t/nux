
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.nux_service import ServiceRepository
from db.repositories.wg import WireGuardRepository
from db.repositories.proxy import ProxyRepository
from db.repositories.remnawave import RemnawaveRepository


class ServiceManager:
    @staticmethod
    async def delete_service_by_params(
        db: AsyncSession,
        user_id: int,
        name: str,
        service_type: str
    ) -> bool:
        """
        Находит сервис по user_id, name, service_type и удаляет его (внешний ресурс + запись).
        Возвращает True, если сервис найден и удалён, иначе False.
        """
        service = await ServiceRepository.get_by_user_name_type(db, user_id, name, service_type)
        if not service:
            return False

        # Выбираем нужный репозиторий в зависимости от типа
        if service_type == 'wireguard':
            await WireGuardRepository.delete(db, service)
        elif service_type == 'proxy':
            await ProxyRepository.delete(db, service)
        elif service_type == 'remnawave':
            await RemnawaveRepository.delete(db, service)
        else:
            # Если тип неизвестен – просто удаляем запись из БД
            await ServiceRepository.delete(db, service)

        return True