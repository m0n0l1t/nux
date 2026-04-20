from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from db.database import get_db
from core.auth import get_current_user
from db.models import User
from db import crud
from core.schemas import WireGuardCreateRequest, WireGuardResponse, WireGuardListResponse

router = APIRouter(prefix="/wireguard", tags=["WireGuard"])

@router.post("", response_model=WireGuardResponse)
async def create_wireguard(
    request: WireGuardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = await crud.create_wireguard_service(db, current_user.id, request.name)
    days_left = (svc.expiration_date - datetime.utcnow()).days
    return WireGuardResponse(
        id=svc.id,
        name=svc.name,
        expiration_date=svc.expiration_date,
        days_left=days_left,
        address=svc.address,
        public_key=svc.public_key
    )

@router.get("", response_model=list[WireGuardListResponse])
async def list_wireguard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    services = await crud.get_wireguard_services_by_user(db, current_user.id)
    result = []
    for s in services:
        days_left = (s.expiration_date - datetime.utcnow()).days
        result.append(WireGuardListResponse(
            id=s.id,
            name=s.name,
            expiration_date=s.expiration_date,
            days_left=days_left,
            address=s.address,
            public_key=s.public_key,
        ))
    return result

def generate_wireguard_config(svc) -> str:
    """Генерирует конфигурацию WireGuard"""
    return f"""[Interface]
Address = {svc.address}
DNS = {svc.dns}
PrivateKey = {svc.private_key}
Jc = 2
Jmin = 10
Jmax = 50
S1 = 28
S2 = 17
H1 = 1428878524
H2 = 1643968564
H3 = 54841605
H4 = 988008980

[Peer]
PublicKey = {svc.public_key}
PresharedKey = {svc.preshared_key}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = {svc.endpoint}
PersistentKeepalive = 25
"""

@router.get("/{service_id}/config")
async def download_wireguard_config(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = await crud.get_wireguard_service(db, service_id, current_user.id)
    if not svc:
        raise HTTPException(404, "Service not found")
    
    config = generate_wireguard_config(svc)
    return PlainTextResponse(content=config, media_type="text/plain", headers={
        "Content-Disposition": f"attachment; filename=wireguard_{svc.name}.conf"
    })

@router.delete("/{service_id}")
async def delete_wireguard(service_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = await crud.get_wireguard_service(db, service_id, current_user.id)
    if not svc:
        raise HTTPException(404, "Service not found")
    await crud.delete_wireguard_service(db, svc)
    return {"ok": True}
