from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from arbety_double_bot.database import db


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password: Mapped[str]
    strategies: Mapped[List['StrategyModel']] = relationship(
        back_populates='user'
    )


class StrategyModel(Base):
    __tablename__ = 'strategies'
    id: Mapped[int] = mapped_column(primary_key=True)
    strategy: Mapped[str]
    value: Mapped[float]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['UserModel'] = relationship(back_populates='strategies')


Base.metadata.create_all(db)
