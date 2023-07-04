from typing import Union

from sqlalchemy import select

from arbety_double_bot.database import Session
from arbety_double_bot.domain import Strategy, User
from arbety_double_bot.models import StrategyModel, UserModel


def create_user(user: User) -> None:
    with Session() as session:
        session.add(
            UserModel(
                name=user.name,
                email=user.email,
                password=user.password,
                gale=user.gale,
                stop_loss=user.stop_loss,
                stop_win=user.stop_win,
            ),
        )
        session.commit()


def edit_user(user: User) -> None:
    with Session() as session:
        model = session.get(UserModel, user.id)
        if model is not None:
            model.email = email
            model.password = password
            model.gale = user.gale
            model.stop_loss = user.stop_loss
            model.stop_win = user.stop_win
            session.commit()


def get_users() -> list[User]:
    with Session() as session:
        query = select(UserModel)
        return [
            user_model_to_dataclass(m) for m in session.scalars(query).all()
        ]


def get_user_by_name(name: str) -> Union[User, None]:
    with Session() as session:
        query = select(UserModel).where(UserModel.name == name)
        model = session.scalars(query).first()
        if model:
            return user_model_to_dataclass(model)


def user_model_to_dataclass(model: UserModel) -> User:
    return User(
        id=model.id,
        name=model.name,
        email=model.email,
        password=model.password,
        gale=model.gale,
        stop_loss=model.stop_loss,
        stop_win=model.stop_win,
    )


def create_strategy(strategy: Strategy) -> None:
    with Session() as session:
        session.add(
            StrategyModel(
                strategy=strategy.strategy,
                bet_color=strategy.bet_color,
                value=strategy.value,
                user_id=strategy.user_id,
            ),
        )
        session.commit()


def remove_strategy_by_id(strategy_id: int) -> None:
    with Session() as session:
        query = select(StrategyModel).where(StrategyModel.id == strategy_id)
        model = session.scalars(query).first()
        if model:
            session.delete(model)
            session.commit()


def get_strategies() -> list[Strategy]:
    with Session() as session:
        query = select(StrategyModel)
        return [
            strategy_model_to_dataclass(m)
            for m in session.scalars(query).all()
        ]


def get_strategies_from_user(user: User) -> list[Strategy]:
    with Session() as session:
        query = select(StrategyModel).where(StrategyModel.user_id == user.id)
        return [
            strategy_model_to_dataclass(m)
            for m in session.scalars(query).all()
        ]


def strategy_model_to_dataclass(model: StrategyModel) -> Strategy:
    return Strategy(
        id=strategy.id,
        strategy=strategy.strategy,
        bet_color=strategy.bet_color,
        value=strategy.value,
        user_id=user.id,
    )
