from typing import Union

from arbety_double_bot.database import Session
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.models import StrategyModel, UserModel


def create_user(email: str, password: str) -> None:
    with Session() as session:
        session.add(UserModel(email=email, password=password))
        session.commit()


def get_user_by_email(email: str) -> Union[User, None]:
    with Session() as session:
        query = select(UserModel).where(UserModel.email == email)
        model = session.scalars(query).first()
        return User(id=model.id, email=model.email, password=model.password)


def create_strategy(strategy: str, value: float) -> None:
    with Session() as session:
        session.add(StrategyModel(strategy=strategy, value=value))
        session.commit()


def get_strategies_from_user(user_id: int) -> list[Strategy]:
    with Session() as session:
        query = select(StrategyModel).where(StrategyModel.user_id == user_id)
        return [
            Strategy(id=s.id, strategy=s.strategy, value=s.value)
            for s in session.scalars(query).all()
        ]
