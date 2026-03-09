from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import main_menu_kb, cancel_kb
from states import Registration

router = Router()

WELCOME_TEXT = """
👋 Привет! Я — бот для знакомств.

Здесь ты можешь:
❤️ Находить интересных людей
💬 Общаться с теми, кто ответил взаимностью
✨ Создавать настоящие связи

Давай начнём! Для этого нужно заполнить анкету 📋
"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    await db.upsert_user(message.from_user.id, message.from_user.username or "")

    if user and await db.is_profile_complete(message.from_user.id):
        if user.get("is_banned"):
            await message.answer("🚫 Ваш аккаунт заблокирован.")
            return
        await message.answer(
            f"👋 С возвращением, {user['name']}!\n\nЧто будем делать?",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(WELCOME_TEXT, reply_markup=cancel_kb())
        await message.answer(
            "📝 Как тебя зовут? Введи своё имя:",
            reply_markup=cancel_kb(),
        )
        await state.set_state(Registration.name)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user or not await db.is_profile_complete(message.from_user.id):
        await message.answer("Сначала заполни анкету. Напиши /start")
        return
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb())


@router.message(F.text == "🏠 Главное меню")
async def go_home(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb())
