from pydantic import BaseModel

class Balance(BaseModel):
    current_total: float
