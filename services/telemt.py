import httpx
from typing import Optional, List, Dict, Any, Union
from services.models_telemt import (
    SuccessResponse,
    ErrorResponse,
    HealthData,
    SystemInfoData,
    RuntimeGatesData,
    RuntimeInitializationData,
    EffectiveLimitsData,
    SecurityPostureData,
    SecurityWhitelistData,
    SummaryData,
    ZeroAllData,
    UpstreamsData,
    MinimalAllData,
    MeWritersData,
    DcStatusData,
    RuntimeMePoolStateData,
    RuntimeMeQualityData,
    RuntimeUpstreamQualityData,
    RuntimeNatStunData,
    RuntimeMeSelftestData,
    RuntimeEdgeConnectionsSummaryData,
    RuntimeEdgeEventsData,
    UserInfo,
    CreateUserRequest,
    PatchUserRequest,
    CreateUserResponse,
    RotateSecretRequest,
)


class TelemtClient:
    """Асинхронный клиент для Telemt Control API."""

    def __init__(self, base_url: str, auth_header: Optional[str] = None, timeout: float = 30.0):
        """
        :param base_url: базовый URL сервера (например, http://127.0.0.1:9091)
        :param auth_header: значение заголовка Authorization (если требуется)
        :param timeout: таймаут запросов
        """
        self.base_url = base_url.rstrip("/")
        self.auth_header = auth_header
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    def _build_headers(self, if_match: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if self.auth_header:
            headers["Authorization"] = self.auth_header
        if if_match:
            headers["If-Match"] = if_match
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        if_match: Optional[str] = None,
    ) -> Any:
        """Отправляет запрос, парсит ответ (data из успешного ответа)."""
        headers = self._build_headers(if_match)
        resp = await self._client.request(
            method,
            path,
            json=json,
            params=params,
            headers=headers,
        )
        data = resp.json()
        if not data.get("ok", False):
            # Обработка ошибки
            error = ErrorResponse.model_validate(data)
            raise httpx.HTTPStatusError(
                f"{resp.status_code}: {error.error.code} - {error.error.message}",
                request=resp.request,
                response=resp,
            )
        # Успешный ответ
        success = SuccessResponse.model_validate(data)
        return success.data

    # === Health ===
    async def health(self) -> HealthData:
        """GET /v1/health"""
        data = await self._request("GET", "/v1/health")
        return HealthData.model_validate(data)

    # === System ===
    async def system_info(self) -> SystemInfoData:
        """GET /v1/system/info"""
        data = await self._request("GET", "/v1/system/info")
        return SystemInfoData.model_validate(data)

    # === Runtime ===
    async def runtime_gates(self) -> RuntimeGatesData:
        """GET /v1/runtime/gates"""
        data = await self._request("GET", "/v1/runtime/gates")
        return RuntimeGatesData.model_validate(data)

    async def runtime_initialization(self) -> RuntimeInitializationData:
        """GET /v1/runtime/initialization"""
        data = await self._request("GET", "/v1/runtime/initialization")
        return RuntimeInitializationData.model_validate(data)

    async def me_pool_state(self) -> RuntimeMePoolStateData:
        """GET /v1/runtime/me_pool_state"""
        data = await self._request("GET", "/v1/runtime/me_pool_state")
        return RuntimeMePoolStateData.model_validate(data)

    async def me_quality(self) -> RuntimeMeQualityData:
        """GET /v1/runtime/me_quality"""
        data = await self._request("GET", "/v1/runtime/me_quality")
        return RuntimeMeQualityData.model_validate(data)

    async def upstream_quality(self) -> RuntimeUpstreamQualityData:
        """GET /v1/runtime/upstream_quality"""
        data = await self._request("GET", "/v1/runtime/upstream_quality")
        return RuntimeUpstreamQualityData.model_validate(data)

    async def nat_stun(self) -> RuntimeNatStunData:
        """GET /v1/runtime/nat_stun"""
        data = await self._request("GET", "/v1/runtime/nat_stun")
        return RuntimeNatStunData.model_validate(data)

    async def me_selftest(self) -> RuntimeMeSelftestData:
        """GET /v1/runtime/me-selftest"""
        data = await self._request("GET", "/v1/runtime/me-selftest")
        return RuntimeMeSelftestData.model_validate(data)

    async def connections_summary(self) -> RuntimeEdgeConnectionsSummaryData:
        """GET /v1/runtime/connections/summary"""
        data = await self._request("GET", "/v1/runtime/connections/summary")
        return RuntimeEdgeConnectionsSummaryData.model_validate(data)

    async def events_recent(self, limit: int = 50) -> RuntimeEdgeEventsData:
        """GET /v1/runtime/events/recent
        :param limit: максимальное количество событий (1-1000)
        """
        params = {"limit": limit} if limit is not None else {}
        data = await self._request("GET", "/v1/runtime/events/recent", params=params)
        return RuntimeEdgeEventsData.model_validate(data)

    # === Limits ===
    async def effective_limits(self) -> EffectiveLimitsData:
        """GET /v1/limits/effective"""
        data = await self._request("GET", "/v1/limits/effective")
        return EffectiveLimitsData.model_validate(data)

    # === Security ===
    async def security_posture(self) -> SecurityPostureData:
        """GET /v1/security/posture"""
        data = await self._request("GET", "/v1/security/posture")
        return SecurityPostureData.model_validate(data)

    async def security_whitelist(self) -> SecurityWhitelistData:
        """GET /v1/security/whitelist"""
        data = await self._request("GET", "/v1/security/whitelist")
        return SecurityWhitelistData.model_validate(data)

    # === Stats ===
    async def stats_summary(self) -> SummaryData:
        """GET /v1/stats/summary"""
        data = await self._request("GET", "/v1/stats/summary")
        return SummaryData.model_validate(data)

    async def stats_zero_all(self) -> ZeroAllData:
        """GET /v1/stats/zero/all"""
        data = await self._request("GET", "/v1/stats/zero/all")
        return ZeroAllData.model_validate(data)

    async def stats_upstreams(self) -> UpstreamsData:
        """GET /v1/stats/upstreams"""
        data = await self._request("GET", "/v1/stats/upstreams")
        return UpstreamsData.model_validate(data)

    async def stats_minimal_all(self) -> MinimalAllData:
        """GET /v1/stats/minimal/all"""
        data = await self._request("GET", "/v1/stats/minimal/all")
        return MinimalAllData.model_validate(data)

    async def stats_me_writers(self) -> MeWritersData:
        """GET /v1/stats/me-writers"""
        data = await self._request("GET", "/v1/stats/me-writers")
        return MeWritersData.model_validate(data)

    async def stats_dcs(self) -> DcStatusData:
        """GET /v1/stats/dcs"""
        data = await self._request("GET", "/v1/stats/dcs")
        return DcStatusData.model_validate(data)

    # === Users ===
    async def list_users(self) -> List[UserInfo]:
        """GET /v1/users (и /v1/stats/users)"""
        data = await self._request("GET", "/v1/users")
        # data может быть списком пользователей или объектом? По документации это список
        if isinstance(data, list):
            return [UserInfo.model_validate(item) for item in data]
        # На всякий случай, если обёрнуто в data
        raise TypeError("Unexpected response format for /v1/users")

    async def create_user(
        self, request: CreateUserRequest, if_match: Optional[str] = None
    ) -> CreateUserResponse:
        """POST /v1/users"""
        data = await self._request("POST", "/v1/users", json=request.model_dump(exclude_unset=True), if_match=if_match)
        return CreateUserResponse.model_validate(data)

    async def get_user(self, username: str) -> UserInfo:
        """GET /v1/users/{username}"""
        data = await self._request("GET", f"/v1/users/{username}")
        return UserInfo.model_validate(data)

    async def patch_user(
        self, username: str, request: PatchUserRequest, if_match: Optional[str] = None
    ) -> UserInfo:
        """PATCH /v1/users/{username}"""
        data = await self._request(
            "PATCH", f"/v1/users/{username}", json=request.model_dump(exclude_unset=True), if_match=if_match
        )
        return UserInfo.model_validate(data)

    async def delete_user(self, username: str, if_match: Optional[str] = None) -> str:
        """DELETE /v1/users/{username}
        Возвращает имя удалённого пользователя (из data).
        """
        data = await self._request("DELETE", f"/v1/users/{username}", if_match=if_match)
        # data — строка с именем
        return data

    async def rotate_secret(
        self, username: str, request: Optional[RotateSecretRequest] = None, if_match: Optional[str] = None
    ) -> Any:
        """
        POST /v1/users/{username}/rotate-secret
        ВНИМАНИЕ: согласно документации, этот эндпоинт в текущей версии возвращает 404.
        Метод оставлен для совместимости, но при вызове, скорее всего, вызовет ошибку.
        """
        json_body = request.model_dump(exclude_unset=True) if request else None
        return await self._request(
            "POST", f"/v1/users/{username}/rotate-secret", json=json_body, if_match=if_match
        )