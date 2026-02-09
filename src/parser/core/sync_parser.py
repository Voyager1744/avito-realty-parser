import random
import time

from parser.core.base_parser import BaseParser
from loguru import logger
from playwright.sync_api import sync_playwright

from common.exceptions.parser_exceptions import PlaywrightTimeoutError
from services.browser_profiles import get_random_profile


class SyncParser(BaseParser):
    """Синхронный парсер"""

    def parse(self, url: str) -> str | None:
        """Основной метод парсинга"""

        profile = get_random_profile()

        try:
            with sync_playwright() as p:
                browser_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    f"--user-agent={profile['headers']['user-agent']}",
                ]
                browser = p.chromium.launch(headless=False, channel="chrome", args=browser_args)
                context = browser.new_context(
                    user_agent=profile["headers"]["user-agent"],
                    viewport=profile["viewport"],
                    locale="ru-RU",
                    timezone_id="Europe/Moscow",
                    # ВАЖНО: передаем только accept-language, остальное генерируется  # noqa
                    extra_http_headers={
                        "accept-language": profile["headers"]["accept-language"]  # noqa
                    },
                    # Дополнительные параметры для реалистичности
                    device_scale_factor=1.0,
                    has_touch=False,
                    is_mobile=False,
                )
                page = context.new_page()

                self._apply_stealth(page)
                self._pre_navigation_behavior(page)

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                logger.info(f"status code: {response.status}")

                if response and response.status == 429:
                    logger.error("[Playwright] HTTP 429 - Rate limit")
                    time.sleep(20)
                    browser.close()
                    return None

                # Дополнительное ожидание
                page.wait_for_timeout(random.randint(2000, 6000))

                content = page.content()

                browser.close()
                logger.success(f"[Playwright] Получено {len(content):,} байт")
                return content

        except PlaywrightTimeoutError:
            logger.error("[Playwright] Timeout загрузки")
            return None
        except Exception as e:
            logger.error(f"[Playwright] Ошибка: {e}")
            if "Executable not found" in str(e):
                logger.error("Выполните: playwright install chromium")
            return None

    def _apply_stealth(self, page):
        """Применяет продвинутые техники маскировки"""
        stealth_js = """
        // Убираем webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Правильные плагины для Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"}},  # noqa: E501
                {0: {type: "application/pdf", suffixes: "pdf"}}
            ]
        });

        // Правильный chrome объект
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {}
        };

        // Исправляем permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """  # noqa: E501

        page.add_init_script(stealth_js)
        logger.debug("[Playwright] Stealth скрипт применен")

    def _pre_navigation_behavior(self, page):
        """Эмулирует поведение перед переходом"""
        try:
            # Движение мыши от края
            page.mouse.move(0, 0)
            time.sleep(random.uniform(0.1, 0.3))
            page.mouse.move(
                random.randint(400, 800),
                random.randint(200, 400),
                steps=random.randint(10, 20),
            )
            logger.debug("[Playwright] Pre-navigation поведение выполнено")
        except Exception as e:
            logger.debug(f"[Playwright] Pre-navigation ошибка: {e}")


if __name__ == "__main__":
    parser = SyncParser()
    url = "https://www.avito.ru/stupino/nedvizhimost"  # Тестовый URL
    comtent = parser.parse(url)

    with open("test.html", "w", encoding="utf-8") as f:
        if comtent:
            f.write(comtent)
            logger.success("Файл сохранен")
