
import httpx

from services.models_amnesia import (
    ClientsResponse,
    CreateClientRequest,
    CreateClientResponse,
    UpdateClientRequest,
    DeleteClientRequest,
    ActionResponse,
    ServerInfo,
    ServerLoad,
    Backup,
    BackupRequest,
    ErrorResponse,
)


class AmnesiaAdminClient:
    """Асинхронный клиент для административного API AmneziaVPN."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"x-api-key": self.api_key},
            timeout=self.timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Проверяет статус ответа и выбрасывает исключение с сообщением из ErrorResponse."""
        if response.is_error:
            try:
                err = ErrorResponse.model_validate(response.json())
                raise httpx.HTTPStatusError(
                    f"{response.status_code}: {err.message}",
                    request=response.request,
                    response=response,
                )
            except Exception:
                response.raise_for_status()

    async def get_clients(
        self, skip: int = 0, limit: int = 100
    ) -> ClientsResponse:
        """Получить список клиентов с пагинацией."""
        params = {"skip": skip, "limit": limit}
        resp = await self._client.get("/clients", params=params)
        self._raise_for_status(resp)
        return ClientsResponse.model_validate(resp.json())

    async def create_client(
        self, request: CreateClientRequest
    ) -> CreateClientResponse:
        """Создать нового клиента."""
        resp = await self._client.post("/clients", json=request.model_dump(exclude_unset=True))
        self._raise_for_status(resp)
        return CreateClientResponse.model_validate(resp.json())

    async def update_client(
        self, request: UpdateClientRequest
    ) -> ActionResponse:
        """Обновить данные клиента."""
        resp = await self._client.patch("/clients", json=request.model_dump(exclude_unset=True))
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())

    async def delete_client(
        self, request: DeleteClientRequest
    ) -> ActionResponse:
        """Удалить клиента."""
        resp = await self._client.request(
            "DELETE", "/clients", json=request.model_dump(exclude_unset=True)
        )
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())

    async def get_server_info(self) -> ServerInfo:
        """Получить информацию о сервере."""
        resp = await self._client.get("/server")
        self._raise_for_status(resp)
        return ServerInfo.model_validate(resp.json())

    async def get_server_load(self) -> ServerLoad:
        """Получить метрики нагрузки сервера."""
        resp = await self._client.get("/server/load")
        self._raise_for_status(resp)
        return ServerLoad.model_validate(resp.json())

    async def get_backup(self) -> Backup:
        """Экспортировать резервную копию конфигурации сервера."""
        resp = await self._client.get("/server/backup")
        self._raise_for_status(resp)
        return Backup.model_validate(resp.json())

    async def restore_backup(self, backup: BackupRequest) -> ServerInfo:
        """Восстановить сервер из резервной копии. Возвращает информацию о сервере после восстановления."""
        resp = await self._client.post(
            "/server/backup",
            json=backup.model_dump(exclude_unset=True, mode="json"),
        )
        self._raise_for_status(resp)
        return ServerInfo.model_validate(resp.json())

    async def reboot_server(self) -> ActionResponse:
        """Перезагрузить сервер."""
        resp = await self._client.post("/server/reboot")
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())