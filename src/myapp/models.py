from __future__ import annotations

from datetime import datetime, date as dt_date, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # int statt str, damit Mongo/Backend/TxOut zusammenpassen
    id: int = 0
    type: str = "einzahlung"
    amount: float
    description: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    category: str = ""
    student: str = ""
    date: Optional[dt_date] = None


class Balance(BaseModel):
    model_config = ConfigDict(extra="ignore")

    current_total: float = 0.0
    total: Optional[float] = None

    #  mypy verlangt Returntype
    def model_post_init(self, __context: object) -> None:
        if self.total is None:
            self.total = self.current_total
        elif self.current_total == 0.0:
            self.current_total = self.total
