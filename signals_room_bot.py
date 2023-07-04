from asyncio import create_task, gather
import os
import re

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyrogram.client import Client

from arbety_double_bot.browser import get_signals, to_bet
from arbety_double_bot.constants import COLORS
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.repositories import get_strategies_from_user, get_users

load_dotenv()






app = Client(
    os.environ['SIGNALS_ROOM_BOT_NAME'],
    api_id=os.environ['API_ID'],
    api_hash=os.environ['API_HASH'],
    bot_token=os.environ['SIGNALS_ROOM_BOT_TOKEN'],
)


async def main() -> None:
    await app.start()
    tasks = []
    for user in get_users():
        tasks.append(create_task(create_browser(app, user)))
    await gather(*tasks)
    await app.stop()


if __name__ == '__main__':
    app.run(main())
