from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import (
    gender_kb, looking_for_kb, skip_cancel_kb,
    cancel_kb, main_menu_kb, district_kb, OSLO_DISTRICTS,
)
from states import Registration

router = Router()

GENDER_MAP = {"👨 Парень": "male", "👩 Девушка": "female"}
LOOKING_MAP = {"👨 Парней": "male", "👩 Девушек": "female", "💫 Всех": "any"}


# ─── CANCEL ──────────────────────────────────────────────────────────────────

@router.message(F.text == "❌ Отмена", Registration())
async def cancel_registration(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user and await db.is_profile_complete(message.from_user.id):
        await message.answer("Отмена. Возвращаю в главное меню.", reply_markup=main_menu_kb())
    else:
        await message.answer(
            "Отмена. Чтобы начать заново, напиши /start",
            reply_markup=cancel_kb(),
        )


# ─── NAME ────────────────────────────────────────────────────────────────────

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введи имя текстом.")
        return
    name = message.text.strip()
    if len(name) < 2 or len(name) > 30:
        await message.answer("Имя должно быть от 2 до 30 символов. Попробуй ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer(
        f"Отлично, {name}! 🎉\n\n🎂 Сколько тебе лет?",
        reply_markup=cancel_kb(),
    )
    await state.set_state(Registration.age)


# ─── AGE ─────────────────────────────────────────────────────────────────────

@router.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введи возраст числом, например: 22")
        return
    age = int(message.text.strip())
    if age < 16 or age > 80:
        await message.answer("Возраст должен быть от 16 до 80 лет.")
        return
    await state.update_data(age=age)
    await message.answer("Кто ты?", reply_markup=gender_kb())
    await state.set_state(Registration.gender)


# ─── GENDER ──────────────────────────────────────────────────────────────────

@router.message(Registration.gender, F.text.in_(GENDER_MAP))
async def reg_gender(message: Message, state: FSMContext):
    gender = GENDER_MAP[message.text]
    await state.update_data(gender=gender)
    await message.answer("Кого ты ищешь? 💫", reply_markup=looking_for_kb())
    await state.set_state(Registration.looking_for)


@router.message(Registration.gender)
async def reg_gender_invalid(message: Message):
    await message.answer("Выбери вариант с кнопки 👇", reply_markup=gender_kb())


# ─── LOOKING FOR ─────────────────────────────────────────────────────────────

@router.message(Registration.looking_for, F.text.in_(LOOKING_MAP))
async def reg_looking(message: Message, state: FSMContext):
    looking = LOOKING_MAP[message.text]
    await state.update_data(looking_for=looking)
    await message.answer(
        "🗺️ В каком районе Осло ты живёшь?\n\nВыбери из списка:",
        reply_markup=district_kb(),
    )
    await state.set_state(Registration.city)


@router.message(Registration.looking_for)
async def reg_looking_invalid(message: Message):
    await message.answer("Выбери вариант с кнопки 👇", reply_markup=looking_for_kb())


# ─── DISTRICT (was city) ─────────────────────────────────────────────────────

@router.message(Registration.city)
async def reg_district(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Выбери район из кнопок ниже 👇", reply_markup=district_kb())
        return
    district = message.text.strip()
    if district not in OSLO_DISTRICTS:
        await message.answer("Выбери район из кнопок ниже 👇", reply_markup=district_kb())
        return
    await state.update_data(city=district)
    await message.answer(
        "💬 Расскажи немного о себе! (необязательно)\n\n"
        "Это увидят другие пользователи. Можно пропустить.",
        reply_markup=skip_cancel_kb(),
    )
    await state.set_state(Registration.about)


# ─── ABOUT ───────────────────────────────────────────────────────────────────

@router.message(Registration.about, F.text == "⏭ Пропустить")
async def reg_about_skip(message: Message, state: FSMContext):
    await state.update_data(about="")
    await message.answer(
        "📸 Загрузи своё лучшее фото!\n\nФото должно быть хорошего качества.",
        reply_markup=cancel_kb(),
    )
    await state.set_state(Registration.photo)


@router.message(Registration.about)
async def reg_about(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введи текст или нажми «Пропустить».")
        return
    about = message.text.strip()
    if len(about) > 300:
        await message.answer(f"Слишком длинно ({len(about)}/300 символов). Сократи чуть-чуть:")
        return
    await state.update_data(about=about)
    await message.answer("📸 Загрузи своё фото!", reply_markup=cancel_kb())
    await state.set_state(Registration.photo)


# ─── PHOTO ───────────────────────────────────────────────────────────────────

@router.message(Registration.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    user_id = message.from_user.id
    await db.update_user_field(user_id, "name", data["name"])
    await db.update_user_field(user_id, "age", data["age"])
    await db.update_user_field(user_id, "gender", data["gender"])
    await db.update_user_field(user_id, "looking_for", data["looking_for"])
    await db.update_user_field(user_id, "city", data["city"])
    await db.update_user_field(user_id, "about", data.get("about", ""))
    await db.update_user_field(user_id, "photo_id", photo_id)
    await db.update_user_field(user_id, "is_active", 1)

    await state.clear()

    gender_icon = "👨" if data["gender"] == "male" else "👩"
    looking_text = {"male": "парней", "female": "девушек", "any": "всех"}.get(
        data["looking_for"], "всех"
    )

    profile_text = (
        f"✅ Анкета создана!\n\n"
        f"{gender_icon} {data['name']}, {data['age']} лет\n"
        f"🗺️ {data['city']}, Oslo\n"
        f"🔍 Ищу: {looking_text}\n"
    )
    if data.get("about"):
        profile_text += f"💬 {data['about']}\n"

    await message.answer_photo(
        photo=photo_id,
        caption=profile_text,
        reply_markup=main_menu_kb(),
    )
    await message.answer(
        "🎉 Анкета готова! Теперь можешь искать людей поблизости.",
        reply_markup=main_menu_kb(),
    )


@router.message(Registration.photo)
async def reg_photo_invalid(message: Message):
    await message.answer(
        "Отправь именно фотографию 📸\n(не файл, не ссылку)",
        reply_markup=cancel_kb(),
    )
