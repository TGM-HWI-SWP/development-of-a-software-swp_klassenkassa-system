from datetime import datetime, date as dt_date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")  # falls Mongo-Dokumente mehr Felder haben

    id: int
    type: str
    amount: float
    description: str = ""
    timestamp: datetime

    category: str = ""
    student: str = ""
    date: dt_date | None = None


class Balance(BaseModel):
    model_config = ConfigDict(extra="ignore")

    current_total: float = 0.0
    total: float | None = None

    def model_post_init(self, __context):
        if self.total is None:
            self.total = self.current_total
        elif self.current_total == 0.0:
            self.current_total = self.total
