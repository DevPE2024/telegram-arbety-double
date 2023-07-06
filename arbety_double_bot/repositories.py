from datetime import date, timedelta
from typing import Union
from uuid import uuid4

from sqlalchemy import select

from arbety_double_bot.database import Session
from arbety_double_bot.domain import Bet, Strategy, User, Token
from arbety_double_bot.models import (
    BetModel,
    StrategyModel,
    UserModel,
    TokenModel,
)


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
                is_betting=user.is_betting,
            ),
        )
        session.commit()


def edit_user(user: User) -> None:
    with Session() as session:
        model = session.get(UserModel, user.id)
        if model is not None:
            model.email = user.email
            model.password = user.password
            model.gale = user.gale
            model.stop_loss = user.stop_loss
            model.stop_win = user.stop_win
            model.is_betting = user.is_betting
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
        is_betting=model.is_betting,
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
        id=model.id,
        strategy=model.strategy,
        bet_color=model.bet_color,
        value=model.value,
        user=user_model_to_dataclass(model.user),
    )


def create_bet(bet: Bet) -> None:
    with Session() as session:
        session.add(BetModel(value=bet.value, user_id=bet.user_id))
        session.commit()


def get_bets_from_user(user: User) -> list[Bet]:
    with Session() as session:
        query = select(BetModel).where(BetModel.user_id == user.id)
        return [
            bet_model_to_dataclass(m) for m in session.scalars(query).all()
        ]


def bet_model_to_dataclass(model: BetModel) -> Bet:
    return Bet(
        id=model.id,
        value=model.value,
        user=user_model_to_dataclass(model.user),
    )


def create_token(days: int) -> str:
    with Session() as session:
        token = TokenModel(
            value=str(uuid4()),
            expiration_date=date.today() + timedelta(days=days)
        )
        session.add(token)
        session.commit()
        return token.value


def get_token(token: str) -> Union[Token, None]:
    with Session() as session:
        query = select(TokenModel).where(TokenModel.value == token)
        model = session.scalars(query).first()
        if model:
            return Token(
                value=model.value,
                expiration_date=model.expiration_date,
            )
