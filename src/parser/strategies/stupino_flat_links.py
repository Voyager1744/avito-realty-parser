from typing import Any, Dict, List, Set
from loguru import logger

from parser.core.avito_flat_parser import AvitoParser
from config.settings import settings


class AvitoFlatLinksCollector:
    """Сборщик ссылок на объявления с пагинацией"""

    def __init__(self, base_url: str, max_pages: int = 10):
        self.base_url = base_url
        self.max_pages = max_pages
        self.parser = AvitoParser(
            headless=settings.HEADLESS_BROWSER,
            stealth_enabled=True,
            random_delay=True,
        )
        self.collected_urls: Set[str] = set()
        self.collected_listings: List[Dict[str, Any]] = []

    def collect_all_listings(self) -> List[Dict[str, Any]]:
        """Сбор всех объявлений"""
        try:
            self.parser.start_browser()

            current_url = self.base_url

            current_listings, total_pages = self.parser.parse_listing_page(current_url)

            if total_pages > 1:
                for page in range(2, min(total_pages + 1, self.max_pages + 1)):
                    next_url = f"{current_url}?p={page}"
                    next_listings, _ = self.parser.parse_listing_page(next_url)
                    current_listings.extend(next_listings)

            for item in current_listings:
                url = item.get("url")
                if not url or url in self.collected_urls:
                    continue
                self.collected_urls.add(url)
                self.collected_listings.append(item)
            logger.info(f"Собрано {len(self.collected_listings)} объявлений")

        except Exception as e:
            logger.error(f"Ошибка при сборе объявлений: {e}")
        finally:
            self.parser.close_browser()

        return self.collected_listings

    def save_links_to_file(self, filename: str = "collected_links2.txt"):
        """Сохранение собранных ссылок в файл"""
        links = list(self.collected_urls)
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                f.write(f"{link}\n")
        logger.success(f"Ссылки сохранены в файл: {filename}, всего {len(links)} ссылок")
