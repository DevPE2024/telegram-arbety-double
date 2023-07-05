from datetime import date
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from arbety_double_bot.database import db


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    strategies: Mapped[List['StrategyModel']] = relationship(
        back_populates='user'
    )
    gale: Mapped[int]


class StrategyModel(Base):
    __tablename__ = 'strategies'
    id: Mapped[int] = mapped_column(primary_key=True)
    strategy: Mapped[str]
    bet_color: Mapped[str]
    value: Mapped[float]
    bets: Mapped[List['BetModel']] = relationship(back_populates='strategy')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['UserModel'] = relationship(back_populates='strategies')


class BetModel(Base):
    __tablename__ = 'bets'
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float]
    strategy_id: Mapped[int] = mapped_column(ForeignKey('strategies.id'))
    strategy: Mapped['StrategyModel'] = relationship(back_populates='bets')


class TokenModel(Base):
    __tablename__ = 'tokens'
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str]
    expiration_date: Mapped[date]


Base.metadata.create_all(db)
