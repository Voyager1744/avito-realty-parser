import json
import re
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from bs4 import BeautifulSoup

from parser.core.base_sync_parser import BaseSyncParser


class AvitoParser(BaseSyncParser):
    """Парсер объявлений с avito"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse_listing_page(self, url: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Парсинг страницы со списком объявлений

        Возвращает:
            - Список объявлений (каждое - dict с данными)
            - Общее число страниц
        """

        content = self.goto(url)
        if not content:
            return [], 0

        self.page.wait_for_timeout(5000)

        logger.debug("Начал парсить bs4")

        soup = BeautifulSoup(content, "html.parser")

        listings = self._extract_json_ld_offers(soup)
        if not listings:
            logger.debug("JSON-LD не найден, пробую собрать ссылки")
            links = soup.find_all("a", href=True, attrs={"data-marker": "item-title"})
            listings = [{"url": link.get("href")} for link in links]
        pagination_links = soup.find_all("a", href=True, attrs={"data-value": True})

        if pagination_links:
            logger.debug(f"Найдено {len(pagination_links)} страниц пагинации")
            total_pages = int(pagination_links[-1].get("href").split("=")[-1])
        else:
            total_pages = 1
        logger.debug(f"всего страниц {total_pages}")

        return listings, total_pages

    def parse_item_page(self, url: str) -> Optional[dict]:
        """Парсинг страницы конкретного объявления"""
        content = self.goto(url)
        if not content:
            return None

        soup = BeautifulSoup(content, "html.parser")

        # Пример парсинга деталей объявления
        # Реализуйте согласно структуре страницы
        return {
            "title": self._extract_title(soup),
            "description": self._extract_description(soup),
            "price": self._extract_price(soup),
            "seller_info": self._extract_seller_info(soup),
            # ... другие поля
        }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        # Реализация извлечения заголовка
        pass

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        # Реализация извлечения описания
        pass

    def _extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        # Реализация извлечения цены
        pass

    def _extract_seller_info(self, soup: BeautifulSoup) -> Optional[dict]:
        # Реализация извлечения информации о продавце
        pass

    def _extract_json_ld_offers(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        listings: List[Dict[str, Any]] = []
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except Exception:
                continue
            offers = self._find_offers_in_jsonld(data)
            for offer in offers:
                url = offer.get("url")
                name = offer.get("name")
                price_raw = offer.get("price")
                currency = offer.get("priceCurrency", "RUB")
                price = self._parse_price(price_raw)
                if not url:
                    continue
                listings.append(
                    {
                        "url": url,
                        "title": name,
                        "price": price,
                        "currency": currency,
                    }
                )
        if listings:
            logger.debug(f"Извлечено {len(listings)} объявлений из JSON-LD")
        return listings

    def _find_offers_in_jsonld(self, data: Any) -> List[Dict[str, Any]]:
        offers: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            if data.get("@type") == "AggregateOffer" and "offers" in data:
                raw = data.get("offers", [])
                if isinstance(raw, dict):
                    raw = [raw]
                for item in raw:
                    if isinstance(item, dict):
                        offers.append(item)
            for value in data.values():
                offers.extend(self._find_offers_in_jsonld(value))
        elif isinstance(data, list):
            for item in data:
                offers.extend(self._find_offers_in_jsonld(item))
        return offers

    def _parse_price(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            digits = re.sub(r"[^\d]", "", value)
            if digits:
                return int(digits)
        return None
