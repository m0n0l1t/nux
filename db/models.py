from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Float, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)  # nullable для регистрации через бота
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # nullable для регистрации через бота
    invite_code_used: Mapped[str | None] = mapped_column(String(36), nullable=True)  # UUID использованного инвайта
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    telegram_registered: Mapped[bool] = mapped_column(Boolean, default=False)  # зарегистрирован ли через бота
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_quota: Mapped[int] = mapped_column(Integer, default=5)
    balance_stars: Mapped[float] = mapped_column(Float, default=0.0)  # Баланс в звёздах Telegram
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    invites_created = relationship("Invite", foreign_keys="Invite.creator_user_id", back_populates="creator")
    invites_used = relationship("Invite", foreign_keys="Invite.used_by_user_id", back_populates="used_by")
    proxy_service = relationship("ProxyService", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wireguard_services = relationship("WireGuardService", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    creator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    used_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    creator = relationship("User", foreign_keys=[creator_user_id], back_populates="invites_created")
    used_by = relationship("User", foreign_keys=[used_by_user_id], back_populates="invites_used")

class ProxyService(Base):
    __tablename__ = "proxy_services"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Proxy Service")
    expiration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    proxy_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="proxy_service")

class WireGuardService(Base):
    __tablename__ = "wireguard_services"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uuid_api: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    expiration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активна ли услуга
    tariff_type: Mapped[str] = mapped_column(String(20), default="unlimited")  # unlimited или limited
    private_key: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    preshared_key: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    dns: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wireguard_services")

class Payment(Base):
    """История платежей"""
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    telegram_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ID платежа от Telegram
    amount_stars: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, failed
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")


class TelegramConnectCode(Base):
    """Коды для привязки Telegram к аккаунту"""
    __tablename__ = "telegram_connect_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", backref="connect_codes")