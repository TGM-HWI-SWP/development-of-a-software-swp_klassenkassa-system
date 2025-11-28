from pydantic import BaseModel, validator
from datetime import datetime
from typing import Literal


class Transaction(BaseModel):
    id: int
    type: Literal["einzahlung", "ausgabe"]
    amount: float
    description: str
    timestamp: datetime

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v

    @validator("description")
    def description_length(cls, v):
        if v is None:
            return ""
        if len(v) > 200:
            raise ValueError("description must be at most 200 characters")
        return v
