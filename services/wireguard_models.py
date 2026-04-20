import re
from typing import List, Optional, Union, Callable
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def transform_endpoint(endpoint: str, host_mapping: dict[str, str]) -> str:
    """
    Заменяет хосты в endpoint согласно mapping.
    
    :param endpoint: исходный endpoint (например, 'old-host.com:51820')
    :param host_mapping: словарь замен, например {'old-host.com': 'new-host.com'}
    :return: трансформированный endpoint
    """
    result = endpoint
    for old_host, new_host in host_mapping.items():
        if old_host in result:
            result = result.replace(old_host, new_host)
    return result


class InterfaceConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: Union[str, List[str]]
    dns: Optional[Union[str, List[str]]] = None
    private_key: Optional[str] = Field(None, alias='PrivateKey')
    jc: Optional[int] = None
    jmin: Optional[int] = None
    jmax: Optional[int] = None
    s1: Optional[int] = None
    s2: Optional[int] = None
    h1: Optional[int] = None
    h2: Optional[int] = None
    h3: Optional[int] = None
    h4: Optional[int] = None

    @field_validator('address', mode='before')
    def split_address(cls, v):
        if isinstance(v, str) and ',' in v:
            return [addr.strip() for addr in v.split(',')]
        return v

    @field_validator('dns', mode='before')
    def split_dns(cls, v):
        if v is not None and isinstance(v, str) and ',' in v:
            return [dns.strip() for dns in v.split(',')]
        return v

    @field_validator('private_key')
    def validate_private_key(cls, v):
        if v is not None and len(v) != 44:
            raise ValueError('PrivateKey must be 44 characters base64 string')
        return v


class PeerConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    public_key: str = Field(..., alias='PublicKey')
    preshared_key: Optional[str] = Field(None, alias='PresharedKey')
    allowed_ips: Union[str, List[str]] = Field(..., alias='AllowedIPs')
    endpoint: str = Field(..., alias='Endpoint')
    persistent_keepalive: Optional[int] = Field(None, alias='PersistentKeepalive')

    @field_validator('public_key', 'preshared_key')
    def validate_base64_key(cls, v):
        if v is not None and len(v) != 44:
            raise ValueError('Key must be 44 characters base64 string')
        return v

    @field_validator('allowed_ips', mode='before')
    def split_allowed_ips(cls, v):
        if isinstance(v, str) and ',' in v:
            return [ip.strip() for ip in v.split(',')]
        return v

    @field_validator('endpoint')
    def validate_endpoint(cls, v):
        if not re.match(r'^([a-zA-Z0-9.-]+|\d+\.\d+\.\d+\.\d+|\:[a-fA-F0-9:]+):\d+$', v):
            raise ValueError('Invalid endpoint format')
        return v

    @field_validator('persistent_keepalive')
    def validate_keepalive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('PersistentKeepalive must be positive integer')
        return v


class WireGuardConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    interface: InterfaceConfig
    peer: PeerConfig

    @classmethod
    def from_str(cls, config_str: str) -> 'WireGuardConfig':
        lines = config_str.strip().split('\n')
        sections = {}
        current_section = None
        current_data = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                if current_section is not None:
                    sections[current_section] = current_data
                current_section = line[1:-1]
                current_data = {}
            elif '=' in line:
                key, value = line.split('=', 1)
                current_data[key.strip()] = value.strip()

        if current_section is not None:
            sections[current_section] = current_data

        # Преобразование данных интерфейса
        interface_data = {}
        for key, value in sections.get('Interface', {}).items():
            key_lower = key.lower()
            if key_lower == 'address':
                interface_data['address'] = value
            elif key_lower == 'dns':
                interface_data['dns'] = value
            elif key_lower == 'privatekey':
                interface_data['private_key'] = value
            elif key_lower in ('jc', 'jmin', 'jmax', 's1', 's2', 'h1', 'h2', 'h3', 'h4'):
                try:
                    interface_data[key_lower] = int(value)
                except ValueError:
                    interface_data[key_lower] = None

        # Преобразование данных пира
        peer_data = {}
        for key, value in sections.get('Peer', {}).items():
            key_lower = key.lower()
            if key_lower == 'publickey':
                peer_data['public_key'] = value
            elif key_lower == 'presharedkey':
                peer_data['preshared_key'] = value
            elif key_lower == 'allowedips':
                peer_data['allowed_ips'] = value
            elif key_lower == 'endpoint':
                peer_data['endpoint'] = value
            elif key_lower == 'persistentkeepalive':
                try:
                    peer_data['persistent_keepalive'] = int(value)
                except ValueError:
                    peer_data['persistent_keepalive'] = None

        interface = InterfaceConfig(**interface_data)
        peer = PeerConfig(**peer_data)
        return cls(interface=interface, peer=peer)

    def to_config_str(self) -> str:
        """Преобразует объект в строку конфигурации WireGuard/AmneziaWG."""
        lines = []

        # Секция Interface
        lines.append("[Interface]")
        if isinstance(self.interface.address, list):
            lines.append(f"Address = {', '.join(self.interface.address)}")
        else:
            lines.append(f"Address = {self.interface.address}")

        if self.interface.dns is not None:
            if isinstance(self.interface.dns, list):
                lines.append(f"DNS = {', '.join(self.interface.dns)}")
            else:
                lines.append(f"DNS = {self.interface.dns}")

        if self.interface.private_key is not None:
            lines.append(f"PrivateKey = {self.interface.private_key}")

        # AmneziaWG дополнительные поля
        if self.interface.jc is not None:
            lines.append(f"Jc = {self.interface.jc}")
        if self.interface.jmin is not None:
            lines.append(f"Jmin = {self.interface.jmin}")
        if self.interface.jmax is not None:
            lines.append(f"Jmax = {self.interface.jmax}")
        if self.interface.s1 is not None:
            lines.append(f"S1 = {self.interface.s1}")
        if self.interface.s2 is not None:
            lines.append(f"S2 = {self.interface.s2}")
        if self.interface.h1 is not None:
            lines.append(f"H1 = {self.interface.h1}")
        if self.interface.h2 is not None:
            lines.append(f"H2 = {self.interface.h2}")
        if self.interface.h3 is not None:
            lines.append(f"H3 = {self.interface.h3}")
        if self.interface.h4 is not None:
            lines.append(f"H4 = {self.interface.h4}")

        lines.append("")  # пустая строка между секциями

        # Секция Peer
        lines.append("[Peer]")
        lines.append(f"PublicKey = {self.peer.public_key}")

        if self.peer.preshared_key is not None:
            lines.append(f"PresharedKey = {self.peer.preshared_key}")

        if isinstance(self.peer.allowed_ips, list):
            lines.append(f"AllowedIPs = {', '.join(self.peer.allowed_ips)}")
        else:
            lines.append(f"AllowedIPs = {self.peer.allowed_ips}")

        lines.append(f"Endpoint = {self.peer.endpoint}")

        if self.peer.persistent_keepalive is not None:
            lines.append(f"PersistentKeepalive = {self.peer.persistent_keepalive}")

        return "\n".join(lines)

    def save_to_file(self, filepath: str) -> None:
        """Сохраняет конфигурацию в файл с расширением .conf."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_config_str())