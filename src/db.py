import hashlib
import re
from typing import Any, Dict, Optional, Tuple

import asyncpg


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS listings (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    price BIGINT,
    currency TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS listings_unique
ON listings (source, source_id, url);
"""


async def init_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)


def extract_source_id(url: str) -> str:
    match = re.search(r"_(\d+)(?:\\?|$)", url)
    if match:
        return match.group(1)
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def upsert_listing(
    pool: asyncpg.Pool,
    listing: Dict[str, Any],
    source: str = "avito",
) -> Tuple[str, Optional[int], Optional[int]]:
    url = listing.get("url")
    if not url:
        return "skipped", None, None

    source_id = extract_source_id(url)
    title = listing.get("title")
    price = listing.get("price")
    currency = listing.get("currency")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, price
            FROM listings
            WHERE source = $1 AND source_id = $2 AND url = $3
            """,
            source,
            source_id,
            url,
        )

        if row is None:
            await conn.execute(
                """
                INSERT INTO listings (source, source_id, url, title, price, currency)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                source,
                source_id,
                url,
                title,
                price,
                currency,
            )
            return "new", None, price

        old_price = row["price"]
        if old_price != price:
            await conn.execute(
                """
                UPDATE listings
                SET title = $1,
                    price = $2,
                    currency = $3,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = $4
                """,
                title,
                price,
                currency,
                row["id"],
            )
            return "price_changed", old_price, price

        await conn.execute(
            """
            UPDATE listings
            SET title = $1,
                currency = $2,
                last_seen_at = NOW()
            WHERE id = $3
            """,
            title,
            currency,
            row["id"],
        )
        return "unchanged", old_price, price
