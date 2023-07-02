from threading import Thread

from sqlalchemy import select

from arbety_double_bot.app import create_app
from arbety_double_bot.database import Session
from arbety_double_bot.models import UserModel
from arbety_double_bot.observer import SignalsObserver, Subscriber
from arbety_double_bot.repositories import get_user_by_name

if __name__ == '__main__':
    app = create_app()
    observer = SignalsObserver()
    with Session() as session:
        query = select(UserModel)
        models = session.scalars(query).all()
    for model in models:
        observer.add_subscriber(Subscriber(app, get_user_by_name(model.name)))
    Thread(target=observer.run)
    app.run()
