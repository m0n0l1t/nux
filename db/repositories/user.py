from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import User
from core.auth import hash_password, verify_password


class UserRepository:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_invite(db: AsyncSession, code: str) -> User | None:
        from db.repositories.invite import InviteRepository  # избегаем циклического импорта
        invite = await InviteRepository.get_by_code(db, code)
        if not invite:
            return None
        result = await db.execute(select(User).where(User.id == invite.used_by_user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | None:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        password: str,
        invite_code: str = None
    ) -> User:
        hashed = hash_password(password)
        user = User(username=username, hashed_password=hashed, invite_code_used=invite_code)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def create_from_telegram(
        db: AsyncSession,
        username: str,
        telegram_id: int,
        invite_code: str
    ) -> User:
        """Создаёт пользователя при регистрации через Telegram бота (без логина/пароля)."""
        user = User(
            telegram_id=telegram_id,
            invite_code_used=invite_code,
            telegram_registered=True,
            username=username,
            hashed_password=""  # пустой пароль, будет установлен при регистрации на сайте
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def link_credentials_to_telegram_user(
        db: AsyncSession,
        telegram_id: int,
        username: str,
        password: str,
        invite_code: str
    ) -> User | None:
        """Привязывает логин/пароль к существующему пользователю из Telegram."""
        user = await UserRepository.get_by_telegram_id(db, telegram_id)
        if not user or not user.telegram_registered:
            return None

        # Проверяем, не занят ли username
        existing = await UserRepository.get_by_username(db, username)
        if existing and existing.id != user.id:
            return None

        user.username = username
        user.hashed_password = hash_password(password)
        user.invite_code_used = invite_code
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
        user = await UserRepository.get_by_username(db, username)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def update_balance(db: AsyncSession, user_id: int, amount: float) -> float:
        """Обновляет баланс пользователя. amount может быть отрицательным."""
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        user.balance_stars += amount
        await db.commit()
        await db.refresh(user)
        return user.balance_stars

    @staticmethod
    async def get_balance(db: AsyncSession, user_id: int) -> float:
        user = await UserRepository.get_by_id(db, user_id)
        return user.balance_stars if user else 0.0

    @staticmethod
    async def link_telegram_id(db: AsyncSession, user_id: int, telegram_id: int) -> bool:
        user = await UserRepository.get_by_id(db, user_id)
        if user and user.telegram_id is None:
            user.telegram_id = telegram_id
            await db.commit()
            return True
        return False