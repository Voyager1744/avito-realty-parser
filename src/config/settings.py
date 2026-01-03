"""Settings."""

from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""

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

    class Config:
        env_file = ".env"


settings = Settings()
