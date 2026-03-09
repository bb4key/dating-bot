import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = (
    [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    if os.getenv("ADMIN_IDS")
    else []
)
DB_PATH: str = os.getenv("DB_PATH", "dating.db")
