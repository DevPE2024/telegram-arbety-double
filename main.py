from asyncio import create_task, gather, run

from pyrogram import idle

from arbety_double_bot.app import create_app
from arbety_double_bot.bot import create_browser
from arbety_double_bot.repositories import get_users

app = create_app()


async def main():
    await app.start()
    tasks = []
    for user in get_users():
        tasks.append(create_task(create_browser(app, user)))
    await gather(*tasks)
    await app.stop()


if __name__ == '__main__':
    if get_users():
        app.run(main())
    else:
        app.run()
