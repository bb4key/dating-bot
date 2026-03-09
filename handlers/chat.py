from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import main_menu_kb, chat_kb

router = Router()


# ─── END CHAT ────────────────────────────────────────────────────────────────

@router.message(F.text == "🚪 Завершить чат")
async def end_chat(message: Message, state: FSMContext):
    partner_id = await db.get_active_chat(message.from_user.id)
    await db.clear_active_chat(message.from_user.id)

    if partner_id:
        await db.clear_active_chat(partner_id)

    await message.answer(
        "💔 Чат завершён. Возвращаю в главное меню.",
        reply_markup=main_menu_kb(),
    )


# ─── RELAY MESSAGES ──────────────────────────────────────────────────────────

@router.message(F.text | F.photo | F.sticker | F.voice | F.video | F.video_note)
async def relay_message(message: Message, bot: Bot, state: FSMContext):
    partner_id = await db.get_active_chat(message.from_user.id)
    if not partner_id:
        return  # Let other handlers handle it

    if not await db.are_matched(message.from_user.id, partner_id):
        await db.clear_active_chat(message.from_user.id)
        await message.answer(
            "Совпадение было удалено. Чат завершён.",
            reply_markup=main_menu_kb(),
        )
        return

    sender = await db.get_user(message.from_user.id)
    sender_name = sender["name"] if sender else "Аноним"

    try:
        if message.text:
            await bot.send_message(
                partner_id,
                f"💬 *{sender_name}*: {message.text}",
                parse_mode="Markdown",
            )
        elif message.photo:
            caption = f"📸 *{sender_name}*"
            if message.caption:
                caption += f": {message.caption}"
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=caption, parse_mode="Markdown")
        elif message.sticker:
            await bot.send_message(partner_id, f"🎭 *{sender_name}* прислал(а) стикер:")
            await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.voice:
            await bot.send_message(partner_id, f"🎤 *{sender_name}* прислал(а) голосовое:")
            await bot.send_voice(partner_id, message.voice.file_id)
        elif message.video:
            caption = f"🎥 *{sender_name}*"
            if message.caption:
                caption += f": {message.caption}"
            await bot.send_video(partner_id, message.video.file_id, caption=caption, parse_mode="Markdown")
        elif message.video_note:
            await bot.send_message(partner_id, f"📹 *{sender_name}* прислал(а) кружочек:")
            await bot.send_video_note(partner_id, message.video_note.file_id)

        await message.react([{"type": "emoji", "emoji": "👍"}])

    except Exception as e:
        if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
            await db.clear_active_chat(message.from_user.id)
            await message.answer(
                "😔 Собеседник недоступен. Чат завершён.",
                reply_markup=main_menu_kb(),
            )
        else:
            await message.answer("⚠️ Не удалось доставить сообщение. Попробуй снова.")
