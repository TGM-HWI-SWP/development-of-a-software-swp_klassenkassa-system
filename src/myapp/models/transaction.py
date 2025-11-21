from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class Transaction(BaseModel):
    id: int
    type: Literal["einzahlung", "ausgabe"]
    amount: float
    description: str
    timestamp: datetime
