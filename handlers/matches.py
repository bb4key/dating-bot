from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import match_actions_kb, main_menu_kb

router = Router()


@router.message(F.text == "❤️ Мои совпадения")
async def show_matches(message: Message, state: FSMContext):
    await state.clear()
    matches = await db.get_matches(message.from_user.id)

    if not matches:
        await message.answer(
            "😔 Пока нет совпадений.\n\n"
            "Лайкай анкеты — и скоро появятся! 👀",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer(f"❤️ Твои совпадения ({len(matches)}):\n")

    for match in matches:
        gender_icon = "👨" if match.get("gender") == "male" else "👩"
        caption = (
            f"{gender_icon} *{match['name']}*, {match.get('age', '?')} лет\n"
            f"🏙️ {match.get('city', '')}\n"
        )
        if match.get("about"):
            caption += f"\n💬 {match['about']}"

        await message.answer_photo(
            photo=match["photo_id"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=match_actions_kb(match["user_id"]),
        )

    await message.answer("Выбери, кому написать 👆", reply_markup=main_menu_kb())


# ─── START CHAT FROM MATCH ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("chat_start:"))
async def start_chat_from_match(callback: CallbackQuery, state: FSMContext):
    partner_id = int(callback.data.split(":")[1])

    if not await db.are_matched(callback.from_user.id, partner_id):
        await callback.answer("Совпадение не найдено.", show_alert=True)
        return

    partner = await db.get_user(partner_id)
    if not partner:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await db.set_active_chat(callback.from_user.id, partner_id)
    await state.clear()

    from keyboards import chat_kb
    await callback.message.answer(
        f"💬 Чат с *{partner['name']}* открыт!\n\n"
        f"Пиши сообщения — я перешлю их. Нажми «Завершить чат» чтобы выйти.",
        parse_mode="Markdown",
        reply_markup=chat_kb(),
    )
    await callback.answer()


# ─── UNMATCH ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("unmatch:"))
async def unmatch(callback: CallbackQuery):
    partner_id = int(callback.data.split(":")[1])
    await db.remove_match(callback.from_user.id, partner_id)
    await db.clear_active_chat(callback.from_user.id)
    await db.clear_active_chat(partner_id)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("❌ Совпадение удалено.")
    await callback.answer()
