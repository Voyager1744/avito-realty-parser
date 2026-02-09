import asyncio

import requests
from loguru import logger


def _post_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    if response.status_code >= 400:
        logger.error(f"Telegram error: {response.status_code} {response.text}")


async def send_message(token: str, chat_id: str, text: str) -> None:
    if not token or not chat_id:
        logger.error("Telegram token/chat_id не заданы")
        return
    await asyncio.to_thread(_post_message, token, chat_id, text)
