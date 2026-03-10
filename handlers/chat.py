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
        try:
            sender = await db.get_user(message.from_user.id)
            await message._bot.send_message(
                partner_id,
                f"💔 {sender['name']} завершил(а) чат.",
                reply_markup=main_menu_kb(),
            )
        except Exception:
            pass

    await message.answer(
        "💔 Чат завершён. Возвращаю в главное меню.",
        reply_markup=main_menu_kb(),
    )


# ─── RELAY MESSAGES ──────────────────────────────────────────────────────────

@router.message(
    (F.text & ~F.text.startswith("/")) | F.photo | F.sticker |
    F.voice | F.video | F.video_note | F.audio | F.document | F.animation
)
async def relay_message(message: Message, bot: Bot, state: FSMContext):
    partner_id = await db.get_active_chat(message.from_user.id)
    if not partner_id:
        return

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
        # Для текста — добавляем имя отправителя
        if message.text:
            await bot.send_message(
                partner_id,
                f"💬 <b>{sender_name}</b>: {message.text}",
                parse_mode="HTML",
            )
        else:
            # Для всех медиа — copy_message сохраняет оригинальный формат
            # (видео не сжимается, кружочки остаются кружочками и т.д.)
            if not message.video_note and not message.sticker:
                # Шлём подпись с именем отдельным сообщением перед медиа
                await bot.send_message(partner_id, f"📨 <b>{sender_name}</b>:", parse_mode="HTML")

            await bot.copy_message(
                chat_id=partner_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )

        # Реакция-подтверждение
        try:
            await message.react([{"type": "emoji", "emoji": "👍"}])
        except Exception:
            pass

    except Exception as e:
        err = str(e).lower()
        if "blocked" in err or "deactivated" in err or "not found" in err:
            await db.clear_active_chat(message.from_user.id)
            await message.answer(
                "😔 Собеседник недоступен. Чат завершён.",
                reply_markup=main_menu_kb(),
            )
        else:
            await message.answer("⚠️ Не удалось доставить сообщение. Попробуй снова.")
