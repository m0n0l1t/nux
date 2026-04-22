from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from db import crud
from db.database import init_db, AsyncSessionLocal
from routers import (
    auth_router,
    proxy_router,
    wireguard_router,
    invites_router,
    admin_router,
    billing_router,
    telegram_connect_router
)

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/") or request.url.path == "/":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    import logging
    logger = logging.getLogger(__name__)

    await init_db()
    logger.info("✅ Database initialized")

    # Запускаем бота в фоновой задаче
    import asyncio
    from services.bot import bot as tg_bot, dp

    # Создаём задачу для polling бота
    bot_task = asyncio.create_task(dp.start_polling(tg_bot))
    logger.info("✅ Telegram bot started")

    # Запускаем фоновую задачу для проверки просроченных услуг
    async def check_expired_services():
        """Фоновая задача для проверки и продления просроченных услуг"""


        while True:
            try:
                async with AsyncSessionLocal() as session:
                    expired_services = await crud.get_expired_wireguard_services(session)
                    for service in expired_services:
                        logger.info(f"Checking expired service {service.id} for user {service.user_id}")
                        renewed = await crud.check_and_renew_wireguard(session, service)
                        if renewed:
                            logger.info(f"Service {service.id} renewed")
                        else:
                            logger.info(f"Service {service.id} deactivated (insufficient balance)")
            except Exception as e:
                logger.error(f"Error in expired services check: {e}")

            # Проверяем каждые 6 часов
            await asyncio.sleep(6 * 60 * 60)

    expired_check_task = asyncio.create_task(check_expired_services())
    logger.info("✅ Expired services checker started")

    yield

    # Shutdown
    logger.info("🛑 Shutting down background tasks...")
    expired_check_task.cancel()
    try:
        await expired_check_task
    except asyncio.CancelledError:
        pass

    logger.info("🛑 Shutting down Telegram bot...")
    tg_bot.session.close()
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    logger.info("✅ All background tasks stopped")


app = FastAPI(
    title="Nux Service API",
    description="API для управления Nux сервисами",
    version="1.0.0",
    lifespan=lifespan
)

# Указываем папку, где лежат наши HTML-файлы
templates = Jinja2Templates(directory="templates")

# Монтируем статические файлы (CSS, JS, изображения)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(NoCacheMiddleware)

# Подключаем роутеры
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(proxy_router, tags=["Proxy"])
app.include_router(wireguard_router, tags=["WireGuard"])
app.include_router(invites_router, tags=["Invites"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(billing_router, tags=["Billing"])
app.include_router(telegram_connect_router, tags=["Telegram"])

@app.get("/health")
async def health_check():
    """Health check эндпоинт для проверки работоспособности приложения"""
    return {"status": "ok", "message": "Application is running"}

@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/config/bot")
async def get_bot_config():
    """Возвращает конфиг для фронтенда (username бота)"""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    bot_username = os.getenv("BOT_USERNAME", "your_bot")
    return {"bot_username": bot_username}
