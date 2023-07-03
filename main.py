from asyncio import run

from arbety_double_bot.app import create_app
from arbety_double_bot.observer import SignalsObserver, Subscriber
from arbety_double_bot.repositories import get_strategies


async def main() -> None:
    app = create_app()
    async with app:
        observer = SignalsObserver()
        for strategy in get_strategies():
            observer.add_subscriber(Subscriber(app, strategy))
        await observer.run()


if __name__ == '__main__':
    run(main())
