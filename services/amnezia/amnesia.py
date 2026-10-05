import httpx

from services.amnezia.models_amnesia import (
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
from core.logger import logger


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

    async def __aenter__(self) -> "AmnesiaAdminClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Явное закрытие HTTP-клиента."""
        await self._client.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        """
        Проверяет статус ответа.
        Если ответ ошибочный — пытается извлечь message из ErrorResponse
        и выбрасывает HTTPStatusError с этим сообщением.
        """
        if not response.is_error:
            return

        message = response.text
        try:
            err = ErrorResponse.model_validate(response.json())
            message = err.message
        except Exception:
            # Тело не JSON или не соответствует ErrorResponse — оставляем сырой текст
            logger.warning(
                "Non-standard error response from API: status=%s body=%r",
                response.status_code,
                response.text,
            )

        logger.error(
            "Amnezia API error: %s %s -> %s %s",
            response.request.method,
            response.request.url,
            response.status_code,
            message,
        )

        raise httpx.HTTPStatusError(
            f"{response.status_code}: {message}",
            request=response.request,
            response=response,
        )

    # === Клиенты ===

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
        payload = request.model_dump(exclude_unset=True)
        logger.info("Creating client with payload: %s", payload)
        resp = await self._client.post("/clients", json=payload)
        self._raise_for_status(resp)
        return CreateClientResponse.model_validate(resp.json())

    async def update_client(
        self, request: UpdateClientRequest
    ) -> ActionResponse:
        """Обновить данные клиента (статус, expiresAt)."""
        payload = request.model_dump(exclude_unset=True)
        logger.info("Updating client with payload: %s", payload)
        resp = await self._client.patch("/clients", json=payload)
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())

    async def delete_client(
        self, request: DeleteClientRequest
    ) -> ActionResponse:
        """Удалить клиента."""
        payload = request.model_dump(exclude_unset=True)
        logger.info("Deleting client with payload: %s", payload)
        resp = await self._client.request("DELETE", "/clients", json=payload)
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())

    # === Сервер ===

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

    # === Бэкапы ===

    async def get_backup(self) -> Backup:
        """Экспортировать резервную копию конфигурации сервера."""
        resp = await self._client.get("/server/backup")
        self._raise_for_status(resp)
        return Backup.model_validate(resp.json())

    async def restore_backup(self, backup: BackupRequest) -> ServerInfo:
        """Восстановить сервер из резервной копии."""
        resp = await self._client.post(
            "/server/backup",
            json=backup.model_dump(exclude_unset=True, mode="json"),
        )
        self._raise_for_status(resp)
        return ServerInfo.model_validate(resp.json())

    async def reboot_server(self) -> ActionResponse:
        """Перезагрузить сервер."""
        logger.warning("Rebooting Amnezia server via API")
        resp = await self._client.post("/server/reboot")
        self._raise_for_status(resp)
        return ActionResponse.model_validate(resp.json())

    # === Служебное ===

    async def healthcheck(self) -> bool:
        """
        Проверка живости API. Не требует авторизации.
        Возвращает True, если сервис отвечает 200.
        """
        try:
            resp = await self._client.get("/healthz")
            return resp.status_code == 200
        except httpx.HTTPError as e:
            logger.warning("Healthcheck failed: %s", e)
            return False