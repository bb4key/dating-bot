import aiosqlite
from config import DB_PATH
from typing import Optional


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                name        TEXT,
                age         INTEGER,
                gender      TEXT,
                looking_for TEXT,
                city        TEXT,
                about       TEXT,
                photo_id    TEXT,
                is_active   INTEGER DEFAULT 1,
                is_banned   INTEGER DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS likes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user   INTEGER NOT NULL,
                to_user     INTEGER NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            );

            CREATE TABLE IF NOT EXISTS dislikes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user   INTEGER NOT NULL,
                to_user     INTEGER NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            );

            CREATE TABLE IF NOT EXISTS matches (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id    INTEGER NOT NULL,
                user2_id    INTEGER NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id)
            );

            CREATE TABLE IF NOT EXISTS active_chats (
                user_id     INTEGER PRIMARY KEY,
                partner_id  INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user   INTEGER NOT NULL,
                to_user     INTEGER NOT NULL,
                reason      TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()


# ─── USER ───────────────────────────────────────────────────────────────────

async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def upsert_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, username)
               VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET username=excluded.username""",
            (user_id, username),
        )
        await db.commit()


async def update_user_field(user_id: int, field: str, value):
    allowed = {
        "name", "age", "gender", "looking_for", "city",
        "about", "photo_id", "is_active", "last_active",
    }
    if field not in allowed:
        raise ValueError(f"Unknown field: {field}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id)
        )
        await db.commit()


async def is_profile_complete(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user:
        return False
    return all(user.get(f) for f in ("name", "age", "gender", "looking_for", "city", "photo_id"))


async def get_all_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=0") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ─── BROWSE ─────────────────────────────────────────────────────────────────

async def get_next_profile(viewer_id: int) -> Optional[dict]:
    """Return one unseen profile matching viewer's preferences."""
    viewer = await get_user(viewer_id)
    if not viewer:
        return None

    looking_for = viewer["looking_for"]  # male / female / any
    viewer_gender = viewer["gender"]

    if looking_for == "any":
        gender_filter = "1=1"
        params = (viewer_id, viewer_id, viewer_id, viewer_id)
    else:
        gender_filter = "u.gender = ?"
        params = (looking_for, viewer_id, viewer_id, viewer_id, viewer_id)

    query = f"""
        SELECT u.* FROM users u
        WHERE u.user_id != ?
          AND u.is_active = 1
          AND u.is_banned = 0
          AND u.name IS NOT NULL
          AND u.photo_id IS NOT NULL
          AND {gender_filter}
          AND (u.looking_for = ? OR u.looking_for = 'any')
          AND u.user_id NOT IN (SELECT to_user FROM likes WHERE from_user = ?)
          AND u.user_id NOT IN (SELECT to_user FROM dislikes WHERE from_user = ?)
        ORDER BY RANDOM()
        LIMIT 1
    """

    if looking_for == "any":
        final_params = (viewer_id, viewer_gender, viewer_id, viewer_id)
    else:
        final_params = (viewer_id, looking_for, viewer_gender, viewer_id, viewer_id)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT u.* FROM users u
            WHERE u.user_id != ?
              AND u.is_active = 1
              AND u.is_banned = 0
              AND u.name IS NOT NULL
              AND u.photo_id IS NOT NULL
              AND (? = 'any' OR u.gender = ?)
              AND (u.looking_for = ? OR u.looking_for = 'any')
              AND u.user_id NOT IN (SELECT to_user FROM likes WHERE from_user = ?)
              AND u.user_id NOT IN (SELECT to_user FROM dislikes WHERE from_user = ?)
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (
                viewer_id,
                looking_for, looking_for,
                viewer_gender,
                viewer_id,
                viewer_id,
            ),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ─── LIKES / DISLIKES ────────────────────────────────────────────────────────

async def add_like(from_user: int, to_user: int) -> bool:
    """Returns True if it's a mutual match."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Save like
        await db.execute(
            "INSERT OR IGNORE INTO likes (from_user, to_user) VALUES (?, ?)",
            (from_user, to_user),
        )
        # Check mutual
        async with db.execute(
            "SELECT 1 FROM likes WHERE from_user=? AND to_user=?",
            (to_user, from_user),
        ) as cur:
            mutual = await cur.fetchone() is not None

        if mutual:
            u1, u2 = sorted([from_user, to_user])
            await db.execute(
                "INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)",
                (u1, u2),
            )

        await db.commit()
        return mutual


async def add_dislike(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO dislikes (from_user, to_user) VALUES (?, ?)",
            (from_user, to_user),
        )
        await db.commit()


# ─── MATCHES ─────────────────────────────────────────────────────────────────

async def get_matches(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT u.* FROM matches m
            JOIN users u ON (
                CASE WHEN m.user1_id = ? THEN m.user2_id ELSE m.user1_id END = u.user_id
            )
            WHERE m.user1_id = ? OR m.user2_id = ?
            ORDER BY m.created_at DESC
            """,
            (user_id, user_id, user_id),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def are_matched(user1: int, user2: int) -> bool:
    u1, u2 = sorted([user1, user2])
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM matches WHERE user1_id=? AND user2_id=?", (u1, u2)
        ) as cur:
            return await cur.fetchone() is not None


async def remove_match(user1: int, user2: int):
    u1, u2 = sorted([user1, user2])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM matches WHERE user1_id=? AND user2_id=?", (u1, u2)
        )
        await db.commit()


# ─── ACTIVE CHAT ─────────────────────────────────────────────────────────────

async def set_active_chat(user_id: int, partner_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)",
            (user_id, partner_id),
        )
        await db.commit()


async def get_active_chat(user_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT partner_id FROM active_chats WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def clear_active_chat(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active_chats WHERE user_id=?", (user_id,))
        await db.commit()


# ─── COMPLAINTS ──────────────────────────────────────────────────────────────

async def add_complaint(from_user: int, to_user: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO complaints (from_user, to_user, reason) VALUES (?, ?, ?)",
            (from_user, to_user, reason),
        )
        await db.commit()


async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned=1, is_active=0 WHERE user_id=?", (user_id,)
        )
        await db.commit()


async def get_complaints() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT c.*, u.name as target_name FROM complaints c "
            "LEFT JOIN users u ON c.to_user = u.user_id "
            "ORDER BY c.created_at DESC LIMIT 50"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
