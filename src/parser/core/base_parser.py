from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Базовый класс парсера"""

    @abstractmethod
    def parse(self, url: str) -> str | None:
        pass

    def check_blocking(self, content: str) -> bool:
        """Проверка на блокировку"""
        if not content:
            return True

        block_keywords = [
            "Проблема с IP",
            "Доступ с Вашего IP временно ограничен",
            "captcha",
            "cloudflare",
        ]

        content_lower = content.lower()
        return any(kw.lower() in content_lower for kw in block_keywords)
