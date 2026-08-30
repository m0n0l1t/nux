from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.auth import get_current_user
from db.models import User
from core.schemas import ProxyServiceResponse
from db.repositories import ServiceRepository

router = APIRouter(prefix="/proxy", tags=["Proxy"])

@router.get("", response_model=ProxyServiceResponse)
async def get_proxy(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    proxys = await ServiceRepository.get_by_user_name_type(db, current_user.id, f'{current_user.username}_proxy', 'proxy')
    if not proxys:
        raise HTTPException(404, "Proxy service not found")
    proxy = proxys[0]
    return {
        "id": proxy.id,
        "name": proxy.name,
        "expiration_date": proxy.expiration_date,
        "proxy_link": proxy.proxy_link,
        "days_left": 0
    }
