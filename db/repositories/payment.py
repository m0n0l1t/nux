from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from db.models import Payment
from db.repositories.user import UserRepository


class PaymentRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        amount_stars: float,
        telegram_payment_id: str = None,
        status: str = "pending",
        description: str = None
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            telegram_payment_id=telegram_payment_id,
            amount_stars=amount_stars,
            status=status,
            description=description
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def complete(
        db: AsyncSession,
        payment_id: int,
        telegram_payment_id: str = None
    ) -> type[Payment] | None:
        payment = await db.get(Payment, payment_id)
        if payment:
            payment.status = "success"
            payment.telegram_payment_id = telegram_payment_id or payment.telegram_payment_id
            payment.completed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(payment)
            await UserRepository.update_balance(db, payment.user_id, payment.amount_stars)
        return payment

    @staticmethod
    async def fail(db: AsyncSession, payment_id: int) -> type[Payment] | None:
        payment = await db.get(Payment, payment_id)
        if payment:
            payment.status = "failed"
            await db.commit()
        return payment

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return result.scalars().all()