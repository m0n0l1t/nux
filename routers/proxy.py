from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from db.database import get_db
from core.auth import get_current_user
from db.models import User
from db import crud
from core.schemas import ProxyServiceResponse

router = APIRouter(prefix="/proxy", tags=["Proxy"])

@router.get("", response_model=ProxyServiceResponse)
async def get_proxy(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proxy = await crud.get_proxy_service(db, current_user.id)
    if not proxy:
        raise HTTPException(404, "Proxy service not found")

    return {
        "id": proxy.id,
        "name": proxy.name,
        "expiration_date": proxy.expiration_date,
        "proxy_link": proxy.proxy_link,
        "days_left": 0
    }
