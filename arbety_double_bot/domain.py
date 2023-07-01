from typing import Optional

from pydantic import BaseModel


class Signal(BaseModel):
    value: int
    color: str


class User(BaseModel):
    id: Optional[int] = None
    email: str
    password: str


class Strategy(BaseModel):
    id: Optional[int] = None
    strategy: str
    value: float
