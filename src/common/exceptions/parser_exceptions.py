from playwright.sync_api import TimeoutError


class PlaywrightTimeoutError(TimeoutError):
    pass
