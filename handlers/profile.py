from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import (
    profile_active_kb, edit_profile_kb, gender_kb,
    looking_for_kb, cancel_kb, main_menu_kb, confirm_delete_kb,
)
from states import EditProfile

router = Router()


def build_profile_caption(user: dict) -> str:
    gender_icon = "👨" if user.get("gender") == "male" else "👩"
    looking_map = {"male": "парней 👨", "female": "девушек 👩", "any": "всех 💫"}
    looking_text = looking_map.get(user.get("looking_for", "any"), "всех")

    text = (
        f"{gender_icon} *{user['name']}*, {user.get('age', '?')} лет\n"
        f"🏙️ {user.get('city', 'Не указан')}\n"
        f"🔍 Ищу: {looking_text}\n"
    )
    if user.get("about"):
        text += f"\n💬 {user['about']}"
    return text


# ─── MY PROFILE ──────────────────────────────────────────────────────────────

@router.message(F.text == "👤 Моя анкета")
async def show_my_profile(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user or not await db.is_profile_complete(message.from_user.id):
        await message.answer("Сначала создай анкету! Напиши /start")
        return

    caption = build_profile_caption(user)
    status = "🟢 Анкета активна" if user.get("is_active") else "🔴 Анкета скрыта"
    caption += f"\n\n{status}"

    await message.answer_photo(
        photo=user["photo_id"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=profile_active_kb(bool(user.get("is_active"))),
    )


# ─── TOGGLE ACTIVE ───────────────────────────────────────────────────────────

@router.message(F.text.in_(["🔴 Скрыть анкету", "🟢 Показывать анкету"]))
async def toggle_active(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    new_status = 0 if user.get("is_active") else 1
    await db.update_user_field(message.from_user.id, "is_active", new_status)
    status_text = "🟢 Анкета снова видна другим!" if new_status else "🔴 Анкета скрыта."
    await message.answer(status_text, reply_markup=profile_active_kb(bool(new_status)))


# ─── EDIT PROFILE ────────────────────────────────────────────────────────────

@router.message(F.text == "✏️ Редактировать")
async def edit_profile_menu(message: Message, state: FSMContext):
    await state.set_state(EditProfile.choosing_field)
    await message.answer("Что хочешь изменить?", reply_markup=edit_profile_kb())


@router.message(EditProfile.choosing_field, F.text == "◀️ Назад")
async def edit_back(message: Message, state: FSMContext):
    await state.clear()
    await show_my_profile(message, state)


@router.message(EditProfile.choosing_field, F.text == "📝 Имя")
async def edit_name_start(message: Message, state: FSMContext):
    await state.set_state(EditProfile.name)
    await message.answer("Введи новое имя:", reply_markup=cancel_kb())


@router.message(EditProfile.choosing_field, F.text == "🎂 Возраст")
async def edit_age_start(message: Message, state: FSMContext):
    await state.set_state(EditProfile.age)
    await message.answer("Введи новый возраст:", reply_markup=cancel_kb())


@router.message(EditProfile.choosing_field, F.text == "🏙️ Город")
async def edit_city_start(message: Message, state: FSMContext):
    await state.set_state(EditProfile.city)
    await message.answer("Введи новый город:", reply_markup=cancel_kb())


@router.message(EditProfile.choosing_field, F.text == "💬 О себе")
async def edit_about_start(message: Message, state: FSMContext):
    await state.set_state(EditProfile.about)
    await message.answer(
        "Напиши новый текст о себе (до 300 символов):",
        reply_markup=cancel_kb(),
    )


@router.message(EditProfile.choosing_field, F.text == "📸 Фото")
async def edit_photo_start(message: Message, state: FSMContext):
    await state.set_state(EditProfile.photo)
    await message.answer("Отправь новое фото 📸", reply_markup=cancel_kb())


# ─── EDIT CANCEL ─────────────────────────────────────────────────────────────

@router.message(F.text == "❌ Отмена", EditProfile())
async def edit_cancel(message: Message, state: FSMContext):
    await state.set_state(EditProfile.choosing_field)
    await message.answer("Отмена. Что ещё хочешь изменить?", reply_markup=edit_profile_kb())


# ─── SAVE EDITS ──────────────────────────────────────────────────────────────

@router.message(EditProfile.name)
async def save_name(message: Message, state: FSMContext):
    if not message.text:
        return
    name = message.text.strip()
    if len(name) < 2 or len(name) > 30:
        await message.answer("Имя от 2 до 30 символов.")
        return
    await db.update_user_field(message.from_user.id, "name", name)
    await state.set_state(EditProfile.choosing_field)
    await message.answer(f"✅ Имя обновлено: {name}", reply_markup=edit_profile_kb())


@router.message(EditProfile.age)
async def save_age(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введи возраст числом.")
        return
    age = int(message.text.strip())
    if age < 16 or age > 80:
        await message.answer("Возраст от 16 до 80.")
        return
    await db.update_user_field(message.from_user.id, "age", age)
    await state.set_state(EditProfile.choosing_field)
    await message.answer(f"✅ Возраст обновлён: {age}", reply_markup=edit_profile_kb())


@router.message(EditProfile.city)
async def save_city(message: Message, state: FSMContext):
    if not message.text:
        return
    city = message.text.strip()
    if len(city) < 2 or len(city) > 50:
        await message.answer("Название города от 2 до 50 символов.")
        return
    await db.update_user_field(message.from_user.id, "city", city)
    await state.set_state(EditProfile.choosing_field)
    await message.answer(f"✅ Город обновлён: {city}", reply_markup=edit_profile_kb())


@router.message(EditProfile.about)
async def save_about(message: Message, state: FSMContext):
    if not message.text:
        return
    about = message.text.strip()
    if len(about) > 300:
        await message.answer(f"Слишком длинно ({len(about)}/300).")
        return
    await db.update_user_field(message.from_user.id, "about", about)
    await state.set_state(EditProfile.choosing_field)
    await message.answer("✅ Текст о себе обновлён!", reply_markup=edit_profile_kb())


@router.message(EditProfile.photo, F.photo)
async def save_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await db.update_user_field(message.from_user.id, "photo_id", photo_id)
    await state.set_state(EditProfile.choosing_field)
    await message.answer_photo(
        photo=photo_id,
        caption="✅ Фото обновлено!",
        reply_markup=edit_profile_kb(),
    )


@router.message(EditProfile.photo)
async def save_photo_invalid(message: Message):
    await message.answer("Отправь именно фотографию 📸")


# ─── DELETE PROFILE ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "delete_profile")
async def delete_profile_prompt(callback: CallbackQuery):
    await callback.message.answer(
        "⚠️ Ты уверен? Анкета будет удалена безвозвратно.",
        reply_markup=confirm_delete_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "delete_profile_confirm")
async def delete_profile_confirm(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    import aiosqlite
    from config import DB_PATH

    async with aiosqlite.connect(DB_PATH) as db_conn:
        await db_conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        await db_conn.execute(
            "DELETE FROM likes WHERE from_user=? OR to_user=?", (user_id, user_id)
        )
        await db_conn.execute(
            "DELETE FROM dislikes WHERE from_user=? OR to_user=?", (user_id, user_id)
        )
        await db_conn.execute(
            "DELETE FROM matches WHERE user1_id=? OR user2_id=?", (user_id, user_id)
        )
        await db_conn.commit()

    await state.clear()
    await callback.message.answer(
        "🗑️ Анкета удалена. Напиши /start чтобы создать новую."
    )
    await callback.answer()


@router.callback_query(F.data == "delete_profile_cancel")
async def delete_profile_cancel(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отмена ✅")
