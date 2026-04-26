from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator, validator, field_validator


# === Вспомогательные модели ===
class Traffic(BaseModel):
    received: int
    sent: int


class Peer(BaseModel):
    id: str = Field(description="Идентификатор (PublicKey)")
    name: Optional[str] = Field(None, description="Название peer'а")
    status: Literal["active", "disabled"] = Field(description="Статус ключа")
    allowedIps: List[str] = Field(description="Список разрешённых IP/подсетей")
    lastHandshake: int = Field(description="Время последнего рукопожатия")
    traffic: Traffic
    endpoint: Optional[str] = Field(None, description="Адрес и порт подключения")
    online: bool
    expiresAt: Optional[int] = Field(None, description="Дата окончания доступа")
    protocol: Literal["amneziawg", "amneziawg2", "xray"] = Field(description="Протокол подключения")


class Client(BaseModel):
    username: str = Field(description="Имя клиента")
    peers: List[Peer] = Field(description="Список peer'ов клиента")


class ClientsResponse(BaseModel):
    total: int = Field(description="Количество всех элементов")
    items: List[Client]


# === Модели для создания клиента ===
class CreateClientRequest(BaseModel):
    clientName: str = Field(description="Имя клиента")
    protocol: Literal["amneziawg", "amneziawg2", "xray"] = Field(default="amneziawg")
    expiresAt: Optional[int] = Field(None, description="Дата окончания доступа")

class ClientInfo(BaseModel):
    """Модель для валидации данных клиента."""
    id: str
    config: str
    protocol: str

    @field_validator('config')
    def config_must_start_with_vpn(cls, v: str) -> str:
        """Проверяет, что конфигурация начинается с 'vpn://'."""
        if not v.startswith('vpn://'):
            raise ValueError('config must start with "vpn://"')
        return v

    @field_validator('protocol')
    def protocol_must_be_allowed(cls, v: str) -> str:
        """Проверяет, что протокол входит в список допустимых."""
        allowed = {'amneziawg', 'wireguard'}  # можно расширить
        if v not in allowed:
            raise ValueError(f'protocol must be one of {allowed}')
        return v


class CreateClientResponse(BaseModel):
    message: str
    client: ClientInfo  # содержит id, config, protocol


# === Модели для обновления/удаления клиента ===
class UpdateClientRequest(BaseModel):
    clientId: str = Field(description="Идентификатор (PublicKey)")
    protocol: Optional[Literal["amneziawg", "amneziawg2", "xray"]] = None
    expiresAt: Optional[int] = None
    status: Optional[Literal["active", "disabled"]] = None


class DeleteClientRequest(BaseModel):
    clientId: str = Field(description="Идентификатор (PublicKey)")
    protocol: Literal["amneziawg", "amneziawg2", "xray"] = Field(default="amneziawg")


class ActionResponse(BaseModel):
    message: str


# === Модели для информации о сервере ===
class ServerInfo(BaseModel):
    id: str
    region: str
    weight: float
    maxPeers: int
    totalPeers: int
    protocols: List[Literal["amneziawg", "amneziawg2", "xray"]]


# === Модели для метрик нагрузки ===
class CpuInfo(BaseModel):
    cores: int


class MemoryInfo(BaseModel):
    totalBytes: int
    freeBytes: int
    usedBytes: int


class DiskInfo(BaseModel):
    totalBytes: int
    usedBytes: int
    availableBytes: int
    usedPercent: float


class NetworkInfo(BaseModel):
    rxBytes: int
    txBytes: int


class DockerContainerMetrics(BaseModel):
    name: str
    cpuPercent: Optional[float] = None
    memUsageBytes: Optional[int] = None
    memLimitBytes: Optional[int] = None
    netRxBytes: Optional[int] = None
    netTxBytes: Optional[int] = None
    pids: Optional[int] = None


class DockerInfo(BaseModel):
    containers: List[DockerContainerMetrics]


class ServerLoad(BaseModel):
    timestamp: str = Field(description="Время формирования ответа (ISO)")
    uptimeSec: float
    loadavg: List[float] = Field(..., min_length=3, max_length=3)
    cpu: CpuInfo
    memory: MemoryInfo
    disk: Optional[DiskInfo] = None
    network: Optional[NetworkInfo] = None
    docker: Optional[DockerInfo] = None


# === Модели для резервного копирования ===
class BackupClientInfo(BaseModel):
    clientId: str
    publicKey: str
    userData: Dict[str, Any] = Field(..., description="Содержит clientName, creationDate, expiresAt")


class BackupProtocolAmnezia(BaseModel):
    wgConfig: str
    presharedKey: str
    serverPublicKey: str
    clients: List[BackupClientInfo]


class BackupProtocolXray(BaseModel):
    serverConfig: str
    uuid: str
    publicKey: str
    privateKey: str
    shortId: str


class Backup(BaseModel):
    generatedAt: datetime
    serverId: Optional[str] = None
    protocols: List[Literal["amneziawg", "amneziawg2", "xray"]]
    amnezia: Optional[BackupProtocolAmnezia] = None
    amneziaWg2: Optional[BackupProtocolAmnezia] = None
    xray: Optional[BackupProtocolXray] = None

    @model_validator(mode="after")
    def validate_protocol_presence(self):
        for proto in self.protocols:
            if proto == "amneziawg" and self.amnezia is None:
                raise ValueError("amnezia must be provided when protocol 'amneziawg' is in protocols")
            if proto == "amneziawg2" and self.amneziaWg2 is None:
                raise ValueError("amneziaWg2 must be provided when protocol 'amneziawg2' is in protocols")
            if proto == "xray" and self.xray is None:
                raise ValueError("xray must be provided when protocol 'xray' is in protocols")
        return self


# Для POST запроса на импорт бэкапа используем ту же модель
BackupRequest = Backup


# === Модель ошибки ===
class ErrorResponse(BaseModel):
    message: str