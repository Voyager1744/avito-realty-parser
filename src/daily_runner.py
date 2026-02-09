import asyncio
import time as time_module
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import asyncpg
from loguru import logger

from config.settings import settings
from db import init_db, upsert_listing
from parser.strategies.stupino_flat_links import AvitoFlatLinksCollector
from telegram import send_message


def _get_timezone():
    if settings.timezone:
        return ZoneInfo(settings.timezone)
    return datetime.now().astimezone().tzinfo


def _parse_run_at(value: str) -> time:
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return time(hour=hour, minute=minute)


async def run_once() -> None:
    if not settings.target_url:
        logger.error("TARGET_URL не задан")
        return

    pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=1,
        max_size=5,
    )

    await init_db(pool)

    collector = AvitoFlatLinksCollector(
        base_url=settings.target_url,
        max_pages=settings.max_pages,
    )
    listings = collector.collect_all_listings()

    new_listings: List[Dict[str, object]] = []
    price_changes: List[Tuple[Dict[str, object], Optional[int], Optional[int]]] = []

    for listing in listings:
        status, old_price, new_price = await upsert_listing(pool, listing)
        if status == "new":
            new_listings.append(listing)
        elif status == "price_changed":
            price_changes.append((listing, old_price, new_price))

    await pool.close()

    digest = build_digest(new_listings, price_changes)
    if digest:
        await send_message(
            settings.TELEGRAM_BOT_TOKEN,
            settings.TELEGRAM_CHAT_ID,
            digest,
        )


def build_digest(
    new_listings: List[Dict[str, object]],
    price_changes: List[Tuple[Dict[str, object], Optional[int], Optional[int]]],
    max_items: int = 20,
) -> str:
    if not new_listings and not price_changes:
        return ""

    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"Ежедневный дайджест за {today}"]

    if new_listings:
        lines.append(f"Новые объявления: {len(new_listings)}")
        for item in new_listings[:max_items]:
            title = item.get("title") or "Без названия"
            price = item.get("price")
            url = item.get("url")
            price_str = f"{price} ₽" if price is not None else "цена не указана"
            lines.append(f"- {price_str} | {title}")
            lines.append(f"  {url}")
    else:
        lines.append("Новые объявления: 0")

    if price_changes:
        lines.append(f"Изменения цены: {len(price_changes)}")
        for item, old_price, new_price in price_changes[:max_items]:
            title = item.get("title") or "Без названия"
            url = item.get("url")
            old_str = f"{old_price} ₽" if old_price is not None else "?"
            new_str = f"{new_price} ₽" if new_price is not None else "?"
            lines.append(f"- {old_str} → {new_str} | {title}")
            lines.append(f"  {url}")
    else:
        lines.append("Изменения цены: 0")

    return "\n".join(lines)


def run_forever() -> None:
    tz = _get_timezone()
    run_at = _parse_run_at(settings.daily_run_at)

    while True:
        now = datetime.now(tz)
        next_run = datetime.combine(now.date(), run_at, tzinfo=tz)
        if next_run <= now:
            next_run += timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        logger.info(f"Следующий запуск: {next_run.isoformat()}")
        if sleep_seconds > 0:
            time_module.sleep(sleep_seconds)

        asyncio.run(run_once())
