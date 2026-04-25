async def test_start_new_user(dispatcher, mock_bot, db_session):
    # Формируем fake-апдейт
    message = MockMessage(text="/start", from_user=MockUser(id=123))
    await dispatcher.feed_update(mock_bot, types.Update(update_id=1, message=message))

    # Проверяем, что бот ответил клавиатурой с инвайтом
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[1]
    assert "инвайт" in args["text"].lower()
    assert "reply_markup" in args


async def test_valid_invite_register(dispatcher, mock_bot, db_session):
    # 1. Имитируем /start и переход в состояние ожидания кода
    start_msg = MockMessage(text="/start", from_user=MockUser(id=456))
    await dispatcher.feed_update(mock_bot, types.Update(update_id=2, message=start_msg))

    # 2. Вводим валидный код
    invite_msg = MockMessage(text="TESTCODE123", from_user=MockUser(id=456))
    await dispatcher.feed_update(mock_bot, types.Update(update_id=3, message=invite_msg))

    # Проверяем, что пользователь зарегистрирован и баланс пополнен
    mock_bot.send_message.assert_called_with(
        text=unittest.mock.ANY,
        reply_markup=unittest.mock.ANY
    )
    # Дополнительная проверка: в БД появилась запись
    user = await crud.get_user_by_telegram_id(456, db_session)
    assert user is not None
    assert user.balance_stars == 100  # стартовый баланс


async def test_create_nuxguard(dispatcher, mock_bot, db_session):
    # Создаём в БД тестового пользователя
    user = models.User(username="testbot", telegram_id=789)
    db_session.add(user)
    await db_session.commit()

    # Имитируем нажатие кнопки "➕ Создать"
    callback = MockCallbackQuery(data="wg_create", from_user=MockUser(id=789))
    await dispatcher.feed_update(
        mock_bot,
        types.Update(update_id=4, callback_query=callback)
    )

    # Вводим название услуги
    name_msg = MockMessage(text="Мой сервер", from_user=MockUser(id=789))
    await dispatcher.feed_update(
        mock_bot,
        types.Update(update_id=5, message=name_msg)
    )

    # Проверяем, что услуга создалась и бот отправил конфиг
    service = await crud.get_wireguard_service_by_name(db_session, user.id, "Мой сервер")
    assert service is not None
    mock_bot.send_message.assert_any_call(
        text=unittest.mock.ANY,
        parse_mode="HTML",
        reply_markup=unittest.mock.ANY
    )