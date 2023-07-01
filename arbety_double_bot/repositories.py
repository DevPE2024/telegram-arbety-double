from sqlalchemy import select

from arbety_double_bot.database import Session
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.models import StrategyModel, UserModel


def create_user(email: str, password: str) -> None:
    with Session() as session:
        session.add(UserModel(email=email, password=password))
        session.commit()


def create_strategy(user_id: int, strategy: str, value: float) -> None:
    with Session() as session:
        session.add(
            StrategyModel(strategy=strategy, value=value, user_id=user_id),
        )
        session.commit()


def get_strategies() -> list[Strategy]:
    with Session() as session:
        result = []
        query = select(StrategyModel)
        for model in session.scalars(query).all():
            user = User(
                id=model.user_id,
                name=model.user.name,
                email=model.user.email,
                password=model.user.password
            )
            result.append(
                Strategy(strategy=model.strategy, value=model.value, user=user)
            )
        return result
