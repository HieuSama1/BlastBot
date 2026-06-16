import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Cấu hình tập trung cho bot."""

    TOKEN = os.getenv("DISCORD_TOKEN")
    DEFAULT_PREFIX = os.getenv("BOT_PREFIX", "!")
    DB_PATH = os.getenv("DB_PATH", "./data/bot.db")
    GUILD_ID = os.getenv("GUILD_ID") or None
    OWNER_ID = os.getenv("OWNER_ID") or None