from sqlalchemy import DeclarativeBasefrom sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from arbety_double_bot.database import db


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password: Mapped[str]


class StrategyModel(Base):
    __tablename__ = 'strategies'
    id: Mapped[int] = mapped_column(primary_key=True)
    strategy: Mapped[str]
    value: Mapped[float]


Base.metadata.create_all(db)
