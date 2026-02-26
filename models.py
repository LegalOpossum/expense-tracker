from pydantic import BaseModel
from typing import Literal

class Expense(BaseModel):
    amount: float
    currency: Literal['USD', 'EUR', 'UAH', 'PLN', 'GBP']
    category: str