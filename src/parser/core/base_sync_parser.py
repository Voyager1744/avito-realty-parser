import random
import time
from typing import Dict, Any, Optional
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from common.exceptions.parser_exceptions import PlaywrightTimeoutError
from services.browser_profiles import get_random_profile


class BaseSyncParser:
    """Базовый синхронный парсер с настройками"""

    def __init__(
        self,
        headless: bool = False,
        stealth_enabled: bool = True,
        random_delay: bool = True,
        default_timeout: int = 60000,
        browser_args: Optional[list] = None,
        profile: Optional[Dict[str, Any]] = None,
    ):
        self.headless = headless
        self.stealth_enabled = stealth_enabled
        self.random_delay = random_delay
        self.default_timeout = default_timeout
        self.browser_args = browser_args or [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]

        self.profile = profile or get_random_profile()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        if self.profile.get("headers", {}).get("user-agent"):
            self.browser_args.append(f"--user-agent={self.profile['headers']['user-agent']}")

    def start_browser(self):
        """Запуск браузера и создание контекста"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, channel="chrome", args=self.browser_args
        )

        self.context = self.browser.new_context(
            user_agent=self.profile.get("headers", {}).get("user-agent"),
            viewport=self.profile.get("viewport", {"width": 1920, "height": 1080}),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            extra_http_headers={
                "accept-language": self.profile.get("headers", {}).get(
                    "accept-language", "ru-RU,ru;q=0.9"
                )
            },
            device_scale_factor=1.0,
            has_touch=False,
            is_mobile=False,
        )

        self.page = self.context.new_page()

        if self.stealth_enabled:
            self._apply_stealth()

    def close_browser(self):
        """Закрытие браузера"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def __enter__(self):
        """Контекстный менеджер для использования with"""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекста"""
        self.close_browser()

    def _apply_stealth(self):
        """Применение техник маскировки"""
        if not self.page:
            return

        stealth_js = """
        // Убираем webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Правильные плагины для Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"}},
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
        self.page.add_init_script(stealth_js)
        logger.debug("[Playwright] Stealth скрипт применен")

    def _pre_navigation_behavior(self):
        """Эмуляция поведения пользователя"""
        if not self.page:
            return

        try:
            self.page.mouse.move(0, 0)
            time.sleep(random.uniform(0.1, 0.3))
            self.page.mouse.move(
                random.randint(400, 800),
                random.randint(200, 400),
                steps=random.randint(10, 20),
            )
            logger.debug("[Playwright] Pre-navigation поведение выполнено")
        except Exception as e:
            logger.debug(f"[Playwright] Pre-navigation ошибка: {e}")

    def goto(self, url: str, wait_until: str = "domcontentloaded") -> Optional[str]:
        """Переход на URL и получение контента"""
        if not self.page:
            return None

        try:
            if self.random_delay:
                time.sleep(random.uniform(0.5, 2.0))

            self._pre_navigation_behavior()

            response = self.page.goto(
                url,
                wait_until=wait_until,
                timeout=self.default_timeout,
            )

            logger.info(
                f"status code: {response.status if response else 'No response'}"  # noqa: E501
            )

            if response and response.status == 429:
                logger.error("[Playwright] HTTP 429 - Rate limit")
                time.sleep(20)
                return None

            if self.random_delay:
                self.page.wait_for_timeout(random.randint(2000, 6000))

            content = self.page.content()
            logger.success(f"[Playwright] Получено {len(content):,} байт")
            return content

        except PlaywrightTimeoutError:
            logger.error("[Playwright] Timeout загрузки")
            return None
        except Exception as e:
            logger.error(f"[Playwright] Ошибка: {e}")
            return None

    def click(self, selector: str, delay: Optional[int] = None):
        """Клик по элементу"""
        if not self.page:
            return

        if delay is None and self.random_delay:
            delay = random.randint(100, 1000)

        if delay:
            self.page.wait_for_timeout(delay)

        self.page.click(selector)

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """Ожидание элемента"""
        if not self.page:
            return None

        timeout = timeout or self.default_timeout
        return self.page.wait_for_selector(selector, timeout=timeout)
