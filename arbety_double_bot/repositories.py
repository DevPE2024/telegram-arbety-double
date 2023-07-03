from typing import Union

from sqlalchemy import select

from arbety_double_bot.database import Session
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.models import StrategyModel, UserModel


def create_user(name: str, email: str, password: str) -> None:
    with Session() as session:
        session.add(UserModel(name=name, email=email, password=password))
        session.commit()


def edit_user(user_id: int, email: str, password: str) -> None:
    with Session() as session:
        model = session.get(UserModel, user_id)
        if model is not None:
            model.email = email
            model.password = password
            session.commit()


def get_users() -> list[User]:
    with Session() as session:
        query = select(UserModel)
        return [
            User(id=m.id, name=m.name, email=m.email, password=m.password)
            for m in session.scalars(query).all()
        ]


def get_user_by_name(name: str) -> Union[User, None]:
    with Session() as session:
        query = select(UserModel).where(UserModel.name == name)
        model = session.scalars(query).first()
        if model is not None:
            return User(
                id=model.id,
                name=model.name,
                email=model.email,
                password=model.password,
            )


def create_strategy(
    user_id: int, strategy: str, bet_color: str, value: float
) -> None:
    with Session() as session:
        session.add(
            StrategyModel(
                strategy=strategy,
                bet_color=bet_color,
                value=value,
                user_id=user_id,
            ),
        )
        session.commit()


def get_strategies() -> list[Strategy]:
    with Session() as session:
        result = []
        query = select(StrategyModel)
        for strategy in session.scalars(query).all():
            user = get_user_by_name(strategy.user.name)
            result.append(
                Strategy(
                    id=strategy.id,
                    strategy=strategy.strategy,
                    bet_color=strategy.bet_color,
                    value=strategy.value,
                    user=user,
                )
            )
        return result


def get_strategies_from_user(user: User) -> list[Strategy]:
    with Session() as session:
        result = []
        query = select(StrategyModel).where(StrategyModel.user_id == user.id)
        for strategy in session.scalars(query).all():
            result.append(
                Strategy(
                    id=strategy.id,
                    strategy=strategy.strategy,
                    bet_color=strategy.bet_color,
                    value=strategy.value,
                    user=user,
                )
            )
        return result
