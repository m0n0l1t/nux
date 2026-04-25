import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, Update, User
from db import models
from datetime import datetime

# Все тесты в этом файле асинхронные
pytestmark = pytest.mark.asyncio

pytestmark = pytest.mark.skip(reason="Тесты бота требуют доработки для aiogram 3")

async def test_start_new_user(dispatcher, bot_mock, db_session):
    """
    Команда /start для нового пользователя.
    Ожидается: приветствие и предложение ввести инвайт-код.
    """
    # Создаём фейковое сообщение
    message = AsyncMock(spec=Message)
    message.text = "/start"
    message.from_user = User(id=123456, is_bot=False, first_name="Test")
    message.chat = AsyncMock(id=123456)
    message.answer = AsyncMock()

    # Передаём update в диспетчер
    update = Update(update_id=1, message=message)
    await dispatcher.feed_update(bot_mock, update)

    # Проверяем, что бот вызвал send_message с правильным текстом
    bot_mock.send_message.assert_awaited_once()
    call_args = bot_mock.send_message.call_args[1]
    assert "привет" in call_args["text"].lower() or "инвайт" in call_args["text"].lower()
    assert "reply_markup" in call_args  # проверяем, что есть клавиатура


async def test_valid_invite_register(dispatcher, bot_mock, db_session):
    """
    Регистрация по валидному инвайт-коду.
    """
    # 1. Создаём инвайт в БД
    admin = models.User(username="admin_bot", telegram_registered=False, is_active=True, invite_quota=1, balance_stars=0)
    db_session.add(admin)
    await db_session.commit()
    invite = models.Invite(code="TEST123", creator_user_id=admin.id, created_at=datetime.utcnow())
    db_session.add(invite)
    await db_session.commit()

    # 2. Имитируем /start
    message_start = AsyncMock(spec=Message)
    message_start.text = "/start"
    message_start.from_user = User(id=789, is_bot=False, first_name="Tester")
    message_start.chat = AsyncMock(id=789)
    update_start = Update(update_id=1, message=message_start)
    await dispatcher.feed_update(bot_mock, update_start)

    # 3. Имитируем ввод инвайт-кода
    message_code = AsyncMock(spec=Message)
    message_code.text = "TEST123"
    message_code.from_user = User(id=789, is_bot=False, first_name="Tester")
    message_code.chat = AsyncMock(id=789)
    update_code = Update(update_id=2, message=message_code)
    await dispatcher.feed_update(bot_mock, update_code)

    # 4. Проверяем, что в БД появился пользователь с telegram_id=789
    user = await db_session.execute(
        models.User.__table__.select().where(models.User.telegram_id == 789)
    )
    user = user.scalar_one_or_none()
    assert user is not None
    assert user.telegram_registered is True
    # Проверяем, что баланс пополнен (допустим, стартовый баланс 100)
    assert user.balance_stars == 100  # или другая сумма

    # 5. Проверяем, что бот отправил приветственное сообщение
    bot_mock.send_message.assert_awaited()
    # можно проверить последний вызов
    last_call = bot_mock.send_message.await_args_list[-1]
    assert "успешно" in last_call[1]["text"].lower() or "зарегистрирован" in last_call[1]["text"].lower()


async def test_create_nuxguard(dispatcher, bot_mock, db_session):
    """
    Создание NuxGuard (WireGuard) через бота.
    """
    # 1. Создаём уже зарегистрированного пользователя
    user = models.User(
        username="tgbotuser",
        telegram_id=999,
        telegram_registered=True,
        is_active=True,
        balance_stars=200  # достаточно для создания услуги
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Имитируем нажатие кнопки "➕ Создать" (callback)
    from aiogram.types import CallbackQuery
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "wg_create"
    callback.from_user = User(id=999, is_bot=False, first_name="TgUser")
    callback.message = AsyncMock()
    callback.message.chat = AsyncMock(id=999)
    callback.message.answer = AsyncMock()
    update_cb = Update(update_id=1, callback_query=callback)
    await dispatcher.feed_update(bot_mock, update_cb)

    # 3. Бот должен запросить название услуги; имитируем ввод имени
    message_name = AsyncMock(spec=Message)
    message_name.text = "Мой сервер"
    message_name.from_user = User(id=999, is_bot=False, first_name="TgUser")
    message_name.chat = AsyncMock(id=999)
    update_name = Update(update_id=2, message=message_name)
    await dispatcher.feed_update(bot_mock, update_name)

    # 4. Проверяем, что услуга создалась в БД
    from db import models
    service = await db_session.execute(
        models.WireGuardService.__table__.select().where(models.WireGuardService.user_id == user.id)
    )
    service = service.scalar_one_or_none()
    assert service is not None
    assert service.name == "Мой сервер"
    assert service.is_active is True

    # 5. Бот должен отправить конфиг-файл или сообщение об успехе
    bot_mock.send_message.assert_awaited()
    # доп. проверки: отправлен ли документ или текст с конфигом