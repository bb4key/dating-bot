from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import settings_kb, looking_for_kb, gender_kb, main_menu_kb, cancel_kb

router = Router()


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала создай анкету! /start")
        return

    gender_text = "Парень 👨" if user.get("gender") == "male" else "Девушка 👩"
    looking_map = {"male": "Парней 👨", "female": "Девушек 👩", "any": "Всех 💫"}
    looking_text = looking_map.get(user.get("looking_for", "any"), "Всех")
    status = "🟢 Активна" if user.get("is_active") else "🔴 Скрыта"

    text = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пол: {gender_text}\n"
        f"🔍 Ищу: {looking_text}\n"
        f"📋 Анкета: {status}\n\n"
        "Для изменения пола/предпочтений — редактируй анкету.\n"
        "Чтобы изменить имя, фото и т.д. — зайди в «👤 Моя анкета» → «✏️ Редактировать»."
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=settings_kb())
