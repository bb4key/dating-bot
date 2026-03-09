from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import settings_kb, settings_looking_kb, settings_gender_kb, main_menu_kb

router = Router()


def _settings_text(user: dict) -> str:
    gender_text = "Парень 👨" if user.get("gender") == "male" else "Девушка 👩"
    looking_map = {"male": "Парней 👨", "female": "Девушек 👩", "any": "Всех 💫"}
    looking_text = looking_map.get(user.get("looking_for", "any"), "Всех")
    status = "🟢 Активна" if user.get("is_active") else "🔴 Скрыта"
    district = user.get("city", "не указан")
    return (
        "⚙️ *Настройки*\n\n"
        f"👤 Пол: {gender_text}\n"
        f"🔍 Ищу: {looking_text}\n"
        f"🗺️ Район: {district}, Oslo\n"
        f"📋 Анкета: {status}\n"
    )


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала создай анкету! /start")
        return
    await message.answer(
        _settings_text(user),
        parse_mode="Markdown",
        reply_markup=settings_kb(),
    )


# ─── CHANGE LOOKING FOR ──────────────────────────────────────────────────────

@router.callback_query(F.data == "settings_looking")
async def settings_change_looking(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 Кого ты хочешь искать?",
        reply_markup=settings_looking_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_looking:"))
async def save_looking(callback: CallbackQuery):
    value = callback.data.split(":")[1]
    await db.update_user_field(callback.from_user.id, "looking_for", value)
    label = {"male": "Парней 👨", "female": "Девушек 👩", "any": "Всех 💫"}.get(value, value)
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        _settings_text(user),
        parse_mode="Markdown",
        reply_markup=settings_kb(),
    )
    await callback.answer(f"✅ Теперь ищешь: {label}")


# ─── CHANGE GENDER ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings_gender")
async def settings_change_gender(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 Кто ты?",
        reply_markup=settings_gender_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_gender:"))
async def save_gender(callback: CallbackQuery):
    value = callback.data.split(":")[1]
    await db.update_user_field(callback.from_user.id, "gender", value)
    label = {"male": "Парень 👨", "female": "Девушка 👩"}.get(value, value)
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        _settings_text(user),
        parse_mode="Markdown",
        reply_markup=settings_kb(),
    )
    await callback.answer(f"✅ Пол изменён: {label}")


# ─── BACK ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        _settings_text(user),
        parse_mode="Markdown",
        reply_markup=settings_kb(),
    )
    await callback.answer()
