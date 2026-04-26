from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from services.amnezia.amnesia import AmnesiaAdminClient
from services.amnezia.wireguard_models import WireGuardConfig, transform_endpoint
from services.amnezia.decoder import decode_vpn_config
from services.amnezia.models_amnesia import CreateClientRequest
from services.telemt.telemt import TelemtClient
from services.telemt.models_telemt import CreateUserRequest
from db.models import User, Invite, ProxyService, WireGuardService
from core.auth import hash_password, verify_password
from core.config import AMNESIA_API_URL, AMNESIA_API_KEY, TELEMT_API_URL, TELEMT_AUTH_HEADER, DOMAIN_NAME, HOST_AMSTERDAM, HOST_MOSCOW

# ---- User ----
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_invite(db: AsyncSession, code: str) -> User | None:
    invite = await get_invite_by_code(db, code)
    result = await db.execute(select(User).where(User.id == invite.used_by_user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, username: str, password: str, invite_code: str = None) -> User:
    hashed = hash_password(password)
    user = User(username=username, hashed_password=hashed, invite_code_used=invite_code)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_user_from_telegram(db: AsyncSession, telegram_id: int, invite_code: str) -> User:
    """Создаёт пользователя при регистрации через Telegram бота (без логина/пароля)"""
    user = User(
        telegram_id=telegram_id,
        invite_code_used=invite_code,
        telegram_registered=True,
        username=f"user_{telegram_id}",  # временный username
        hashed_password=""  # пустой пароль, будет установлен при регистрации на сайте
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def link_credentials_to_telegram_user(db: AsyncSession, telegram_id: int, username: str, password: str, invite_code: str) -> User | None:
    """Привязывает логин/пароль к существующему пользователю из Telegram.
    Если пользователь с таким telegram_id существует, обновляем его данные.
    Если нет — возвращаем None."""
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user or not user.telegram_registered:
        return None
    
    # Проверяем, не занят ли username другим пользователем
    existing = await get_user_by_username(db, username)
    if existing and existing.id != user.id:
        return None  # username занят другим пользователем
    
    user.username = username
    user.hashed_password = hash_password(password)
    user.invite_code_used = invite_code  # подтверждаем инвайт
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | None:
    """Получить пользователя по telegram_id"""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ---- Invites ----
async def create_invite(db: AsyncSession, creator_id: int, expires_at: datetime = None) -> Invite:
    code = str(uuid.uuid4())
    invite = Invite(code=code, creator_user_id=creator_id, expires_at=expires_at)
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite

async def get_invite_by_code(db: AsyncSession, code: str) -> Invite | None:
    result = await db.execute(select(Invite).where(Invite.code == code))
    return result.scalar_one_or_none()

async def get_invites_by_creator(db: AsyncSession, creator_id: int) -> list[Invite]:
    result = await db.execute(select(Invite).where(Invite.creator_user_id == creator_id))
    return result.scalars().all()

async def use_invite(db: AsyncSession, code: str, user_id: int) -> bool:
    invite = await get_invite_by_code(db, code)
    if not invite or invite.used_by_user_id or (invite.expires_at and invite.expires_at < datetime.utcnow()):
        return False
    invite.used_by_user_id = user_id
    invite.used_at = datetime.utcnow()
    await db.commit()
    return True

# ---- ProxyService (одна на пользователя) ----
async def create_proxy_service(db: AsyncSession, user_id: int, expiration_days=30, proxy_link=None) -> ProxyService:
    # Проверяем, нет ли уже
    result = await db.execute(select(ProxyService).where(ProxyService.user_id == user_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    async with TelemtClient(
            base_url=TELEMT_API_URL,
            auth_header=TELEMT_AUTH_HEADER,  # если включён в конфиге
    ) as client:
        # Создать нового пользователя
        name = f'user_{user_id}'
        current = await client.get_user(name)
        if current:
            await client.delete_user(name)

        new_user = await client.create_user(
            CreateUserRequest(username=name, max_tcp_conns=100)
        )

        proxy_link = new_user.user.links.tls[0].replace(HOST_AMSTERDAM, DOMAIN_NAME)

        expiration = datetime.now() + timedelta(days=expiration_days)
        service = ProxyService(user_id=user_id, expiration_date=expiration, proxy_link=proxy_link)
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

async def get_proxy_service(db: AsyncSession, user_id: int) -> ProxyService | None:
    result = await db.execute(select(ProxyService).where(ProxyService.user_id == user_id))
    return result.scalar_one_or_none()


async def create_wireguard_service(db: AsyncSession, user_id: int, name: str, expiration_days=30) -> WireGuardService:

    async with AmnesiaAdminClient(
        base_url=AMNESIA_API_URL,
        api_key=AMNESIA_API_KEY,
    ) as client:

        # Создать нового клиента
        new_client = await client.create_client(
            CreateClientRequest(clientName=name, protocol="amneziawg")
        )
        config = WireGuardConfig.from_str(decode_vpn_config(new_client.client.config))
        
        # Трансформируем endpoint (заменяем хосты)
        endpoint_mapping = {}
        if HOST_AMSTERDAM and HOST_MOSCOW:
            endpoint_mapping[HOST_AMSTERDAM] = HOST_MOSCOW
        
        transformed_endpoint = transform_endpoint(config.peer.endpoint, endpoint_mapping) if endpoint_mapping else config.peer.endpoint
        
        expiration = datetime.now() + timedelta(days=expiration_days)
        service = WireGuardService(
            user_id=user_id,
            uuid_api=new_client.client.id,
            name=name,
            expiration_date=expiration,
            balance=0.0,
            private_key=config.interface.private_key,
            public_key=config.peer.public_key,
            preshared_key=config.peer.preshared_key,
            address=config.interface.address,
            dns=', '.join(config.interface.dns),
            endpoint=transformed_endpoint
        )
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

async def get_wireguard_services_by_user(db: AsyncSession, user_id: int) -> list[WireGuardService]:
    result = await db.execute(select(WireGuardService).where(WireGuardService.user_id == user_id))
    return result.scalars().all()

async def get_wireguard_service(db: AsyncSession, service_id: int, user_id: int) -> WireGuardService | None:
    result = await db.execute(select(WireGuardService).where(WireGuardService.id == service_id, WireGuardService.user_id == user_id))
    return result.scalar_one_or_none()

async def delete_wireguard_service(db: AsyncSession, service: WireGuardService):
    await db.delete(service)
    await db.commit()

async def link_telegram_id(db: AsyncSession, user_id: int, telegram_id: int):
    user = await get_user_by_id(user_id, db)
    if user and user.telegram_id is None:
        user.telegram_id = telegram_id
        await db.commit()
        return True
    return False

# ---- Balance ----
async def update_user_balance(db: AsyncSession, user_id: int, amount: float) -> float:
    """Обновляет баланс пользователя. amount может быть отрицательным для списания."""
    user = await get_user_by_id(user_id, db)
    if not user:
        raise ValueError("User not found")
    user.balance_stars += amount
    await db.commit()
    await db.refresh(user)
    return user.balance_stars

async def get_user_balance(db: AsyncSession, user_id: int) -> float:
    user = await get_user_by_id(user_id, db)
    return user.balance_stars if user else 0.0

# ---- Payments ----
from db.models import Payment

async def create_payment_record(
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

async def complete_payment(db: AsyncSession, payment_id: int, telegram_payment_id: str = None):
    payment = await db.get(Payment, payment_id)
    if payment:
        payment.status = "success"
        payment.telegram_payment_id = telegram_payment_id or payment.telegram_payment_id
        payment.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(payment)
        # Зачисляем на баланс
        await update_user_balance(db, payment.user_id, payment.amount_stars)
    return payment

async def fail_payment(db: AsyncSession, payment_id: int):
    payment = await db.get(Payment, payment_id)
    if payment:
        payment.status = "failed"
        await db.commit()
    return payment

async def get_payments_by_user(db: AsyncSession, user_id: int) -> list[Payment]:
    result = await db.execute(select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc()))
    return result.scalars().all()

# ---- WireGuard Service Expiration ----
async def get_expired_wireguard_services(db: AsyncSession) -> list[WireGuardService]:
    """Получает все просроченные услуги WireGuard"""
    result = await db.execute(
        select(WireGuardService)
        .where(WireGuardService.is_active == True)
        .where(WireGuardService.expiration_date < datetime.utcnow())
    )
    return result.scalars().all()

async def deactivate_wireguard_service(db: AsyncSession, service: WireGuardService):
    """Деактивирует услугу WireGuard"""
    service.is_active = False
    await db.commit()
    await db.refresh(service)
    return service

async def check_and_renew_wireguard(db: AsyncSession, service: WireGuardService) -> bool:
    """
    Проверяет баланс и автоматически продлевает услугу.
    Если баланс 0 — деактивирует услугу.
    Возвращает True если услуга продлена, False если деактивирована.
    """
    user = await get_user_by_id(service.user_id, db)
    if not user:
        await deactivate_wireguard_service(db, service)
        return False
    
    # Прокси бесплатен при наличии WireGuard, поэтому списываем только за WireGuard
    from core.config import WIREGUARD_PRICE_STARS
    
    if user.balance_stars >= WIREGUARD_PRICE_STARS:
        # Списываем средства и продлеваем
        user.balance_stars -= WIREGUARD_PRICE_STARS
        service.expiration_date = datetime.utcnow() + timedelta(days=30)
        service.is_active = True
        await db.commit()
        await db.refresh(user)
        await db.refresh(service)
        return True
    else:
        # Баланс недостаточен — деактивируем
        await deactivate_wireguard_service(db, service)
        return False
