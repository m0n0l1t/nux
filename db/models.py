from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Float, Text, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invite_code_used: Mapped[str | None] = mapped_column(String(36), nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    telegram_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_quota: Mapped[int] = mapped_column(Integer, default=5)
    balance_stars: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Связи
    services = relationship("Service", back_populates="user", cascade="all, delete-orphan")
    invites_created = relationship("Invite", foreign_keys="Invite.creator_user_id", back_populates="creator")
    invites_used = relationship("Invite", foreign_keys="Invite.used_by_user_id", back_populates="used_by")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    creator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    used_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    creator = relationship("User", foreign_keys=[creator_user_id], back_populates="invites_created")
    used_by = relationship("User", foreign_keys=[used_by_user_id], back_populates="invites_used")

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    telegram_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount_stars: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")

class Server(Base):
    """Таблица для учёта серверов и их лимитов"""
    __tablename__ = "servers"
    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    max_services: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Опционально: можно добавить регион, тип и т.д.

class Service(Base):
    """Единая таблица для всех видов сервисов (прокси, wireguard, remnawave)"""
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'proxy', 'wireguard', 'remnawave'
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Service")
    link: Mapped[str | None] = mapped_column(String(2000), nullable=True)   # Основная ссылка/конфиг
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ID во внешней системе (для удаления/обновления)
    server_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)     # IP сервера, где размещён сервис
    expiration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    user = relationship("User", back_populates="services")