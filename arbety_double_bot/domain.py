from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    password: str


class Strategy(BaseModel):
    id: Optional[int] = None
    strategy: str
    bet_color: str
    value: float
    user: Optional[User]
