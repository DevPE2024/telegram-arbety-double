from datetime import date
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    password: str
    gale: int
    stop_loss: str
    stop_win: str


class Strategy(BaseModel):
    id: Optional[int] = None
    strategy: str
    bet_color: str
    value: float
    user_id: Optional[int]


class Bet(BaseModel):
    id: Optional[int] = None
    value: float
    strategy_id: Optional[int]


class Token(BaseModel):
    id: Optional[int] = None
    value: str
    expiration_date: date
