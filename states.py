from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    city = State()
    about = State()
    photo = State()


class EditProfile(StatesGroup):
    choosing_field = State()
    name = State()
    age = State()
    city = State()
    about = State()
    photo = State()


class Browse(StatesGroup):
    viewing = State()


class Chat(StatesGroup):
    choosing_partner = State()
    messaging = State()


class Complaint(StatesGroup):
    choosing_reason = State()
