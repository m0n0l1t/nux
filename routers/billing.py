from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.auth import get_current_user
from db.models import User
from db import crud
from core.schemas import BalanceResponse, PaymentRecord
from core.config import WIREGUARD_PRICE_STARS, TARIFF_TYPES

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получить текущий баланс пользователя"""
    balance = await crud.get_user_balance(db, current_user.id)
    return BalanceResponse(balance_stars=balance, username=current_user.username)

@router.get("/payments", response_model=list[PaymentRecord])
async def get_payments(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получить историю платежей пользователя"""
    payments = await crud.get_payments_by_user(db, current_user.id)
    return payments

@router.get("/tariffs")
async def get_tariffs():
    """Получить доступные тарифы"""
    return {
        "wireguard": {
            "price_stars": WIREGUARD_PRICE_STARS,
            "period_days": 30,
            "tariff_types": TARIFF_TYPES
        },
        "proxy": {
            "price_stars": 0,
            "description": "Бесплатно при наличии активной услуги WireGuard"
        }
    }
