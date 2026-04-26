from aiogram.fsm.state import State, StatesGroup

class AuthState(StatesGroup):
    waiting_for_invite_code = State()
    waiting_for_username = State()
    waiting_for_password = State()

class CreateWGState(StatesGroup):
    waiting_for_name = State()

class ConnectState(StatesGroup):
    waiting_for_code = State()