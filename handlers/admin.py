from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import database as db
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    total = await db.get_all_users_count()
    await message.answer(
        f"🛠️ *Панель администратора*\n\n"
        f"👥 Пользователей: {total}\n\n"
        f"Команды:\n"
        f"/ban [user_id] — заблокировать\n"
        f"/unban [user_id] — разблокировать\n"
        f"/stats — статистика\n"
        f"/complaints — жалобы",
        parse_mode="Markdown",
    )


@router.message(Command("ban"))
async def ban_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: /ban [user_id]")
        return
    user_id = int(args[1])
    await db.ban_user(user_id)
    await message.answer(f"✅ Пользователь {user_id} заблокирован.")


@router.message(Command("unban"))
async def unban_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: /unban [user_id]")
        return
    user_id = int(args[1])
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db_conn:
        await db_conn.execute(
            "UPDATE users SET is_banned=0, is_active=1 WHERE user_id=?", (user_id,)
        )
        await db_conn.commit()
    await message.answer(f"✅ Пользователь {user_id} разблокирован.")


@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db_conn:
        async with db_conn.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db_conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as cur:
            banned = (await cur.fetchone())[0]
        async with db_conn.execute("SELECT COUNT(*) FROM matches") as cur:
            matches = (await cur.fetchone())[0]
        async with db_conn.execute("SELECT COUNT(*) FROM likes") as cur:
            likes = (await cur.fetchone())[0]

    await message.answer(
        f"📊 *Статистика*\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"🚫 Заблокировано: {banned}\n"
        f"❤️ Всего лайков: {likes}\n"
        f"💕 Взаимных совпадений: {matches}",
        parse_mode="Markdown",
    )


@router.message(Command("complaints"))
async def complaints_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    complaints = await db.get_complaints()
    if not complaints:
        await message.answer("Жалоб нет.")
        return
    text = "🚩 *Последние жалобы:*\n\n"
    for c in complaints[:20]:
        text += f"От {c['from_user']} → {c['to_user']} ({c.get('target_name', '?')}): {c['reason']}\n"
    await message.answer(text, parse_mode="Markdown")
