"""Settings."""

import os
from typing import Optional

from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Settings:
    """Настройки приложения"""

    target_url: str = os.getenv("TARGET_URL", "")
    max_pages: int = int(os.getenv("MAX_PAGES", "10"))

    # расписание
    daily_run_at: str = os.getenv("DAILY_RUN_AT", "09:00")  # HH:MM
    timezone: str = os.getenv("TIMEZONE", "")  # если пусто, берем локальную
    run_mode: str = os.getenv("RUN_MODE", "once")  # once|loop

    # база данных
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "avito_user"
    POSTGRES_PASSWORD: str = "avito_password"
    POSTGRES_DB: str = "avito_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = "redis_password"

    # Playwright
    HEADLESS_BROWSER: bool = True

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    class Config:
        env_file = ".env"


settings = Settings()
