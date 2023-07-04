from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    password: str
    gale: Optional[int] = 0


class Strategy(BaseModel):
    id: Optional[int] = None
    strategy: str
    bet_color: str
    value: float
    user: Optional[User]


class Bet(BaseModel):
    id: Optional[int] = None
    value: float
    color: str
    strategy: Optional[Strategy]
