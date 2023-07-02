from threading import Thread

from arbety_double_bot.app import create_app
from arbety_double_bot.observer import SignalsObserver, Subscriber
from arbety_double_bot.repositories import get_strategies

if __name__ == '__main__':
    app = create_app()
    with app:
        observer = SignalsObserver()
        for strategy in get_strategies():
            observer.add_subscriber(Subscriber(app, strategy))
        Thread(target=observer.run).start()
