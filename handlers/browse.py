from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import browse_actions_kb, notify_match_kb, complaint_reasons_kb, main_menu_kb
from states import Browse

router = Router()


def build_card(user: dict) -> str:
    gender_icon = "👨" if user.get("gender") == "male" else "👩"
    text = (
        f"{gender_icon} *{user['name']}*, {user.get('age', '?')} лет\n"
        f"🏙️ {user.get('city', '')}\n"
    )
    if user.get("about"):
        text += f"\n💬 {user['about']}"
    return text


@router.message(F.text == "👀 Смотреть анкеты")
async def start_browse(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user or not await db.is_profile_complete(message.from_user.id):
        await message.answer("Сначала создай анкету! Напиши /start")
        return
    if user.get("is_banned"):
        await message.answer("🚫 Вы заблокированы.")
        return

    await state.set_state(Browse.viewing)
    await send_next_profile(message, state)


async def send_next_profile(message: Message, state: FSMContext):
    viewer_id = message.from_user.id
    profile = await db.get_next_profile(viewer_id)

    if not profile:
        await state.clear()
        await message.answer(
            "😔 Пока что анкеты закончились.\n"
            "Возвращайся позже — появятся новые люди!",
            reply_markup=main_menu_kb(),
        )
        return

    await state.update_data(current_profile=profile["user_id"])
    caption = build_card(profile)

    await message.answer_photo(
        photo=profile["photo_id"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=browse_actions_kb(profile["user_id"]),
    )


# ─── LIKE ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("like:"))
async def handle_like(callback: CallbackQuery, state: FSMContext, bot: Bot):
    target_id = int(callback.data.split(":")[1])
    viewer_id = callback.from_user.id

    mutual = await db.add_like(viewer_id, target_id)

    if mutual:
        viewer = await db.get_user(viewer_id)
        target = await db.get_user(target_id)

        # Notify viewer
        await callback.message.answer(
            f"🎉 Взаимная симпатия с *{target['name']}*!\n\n"
            f"Теперь вы можете написать друг другу 💬",
            parse_mode="Markdown",
            reply_markup=notify_match_kb(target_id),
        )

        # Notify target
        try:
            await bot.send_photo(
                chat_id=target_id,
                photo=viewer["photo_id"],
                caption=(
                    f"🎉 *{viewer['name']}* лайкнул(а) тебя, и ты его тоже!\n\n"
                    f"У вас взаимная симпатия 💕"
                ),
                parse_mode="Markdown",
                reply_markup=notify_match_kb(viewer_id),
            )
        except Exception:
            pass
    else:
        await callback.answer("❤️ Лайк отправлен!")

    await callback.message.delete()
    await send_next_profile(callback.message, state)


# ─── DISLIKE ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("dislike:"))
async def handle_dislike(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split(":")[1])
    await db.add_dislike(callback.from_user.id, target_id)
    await callback.answer("👎")
    await callback.message.delete()
    await send_next_profile(callback.message, state)


# ─── SUPERLIKE ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("superlike:"))
async def handle_superlike(callback: CallbackQuery, state: FSMContext, bot: Bot):
    target_id = int(callback.data.split(":")[1])
    viewer_id = callback.from_user.id
    viewer = await db.get_user(viewer_id)

    mutual = await db.add_like(viewer_id, target_id)

    try:
        target = await db.get_user(target_id)
        await bot.send_photo(
            chat_id=target_id,
            photo=viewer["photo_id"],
            caption=(
                f"⚡ *{viewer['name']}* поставил(а) тебе суперлайк!\n"
                f"🏙️ {viewer.get('city', '')}, {viewer.get('age', '?')} лет\n"
                + (f"\n💬 {viewer['about']}" if viewer.get("about") else "")
            ),
            parse_mode="Markdown",
            reply_markup=notify_match_kb(viewer_id) if mutual else None,
        )
    except Exception:
        pass

    if mutual:
        target = await db.get_user(target_id)
        await callback.message.answer(
            f"⚡🎉 Взаимная симпатия с *{target['name']}*!",
            parse_mode="Markdown",
            reply_markup=notify_match_kb(target_id),
        )
    else:
        await callback.answer("⚡ Суперлайк отправлен!")

    await callback.message.delete()
    await send_next_profile(callback.message, state)


# ─── REPORT ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("report:"))
async def handle_report(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "🚩 По какой причине жалуетесь?",
        reply_markup=complaint_reasons_kb(target_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("complaint:"))
async def save_complaint(callback: CallbackQuery):
    parts = callback.data.split(":")
    to_user = int(parts[1])
    reason = parts[2]

    reason_map = {
        "obscene": "Непристойный контент",
        "spam": "Бот / Спам",
        "scam": "Мошенничество",
        "insults": "Оскорбления",
        "other": "Другое",
    }

    await db.add_complaint(callback.from_user.id, to_user, reason_map.get(reason, reason))
    await db.add_dislike(callback.from_user.id, to_user)

    await callback.message.delete()
    await callback.message.answer("✅ Жалоба принята. Спасибо!")
    await callback.answer()


@router.callback_query(F.data == "complaint_cancel")
async def cancel_complaint(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отмена")
