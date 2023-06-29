from typing import Optional

from pydantic import BaseModel


class Signal(BaseModel):
    value: int
    color: str
