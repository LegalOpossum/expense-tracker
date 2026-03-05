from pydantic import BaseModel
from typing import Literal, Optional

class Expense(BaseModel):
  amount: float
  currency: Literal['USD', 'EUR', 'UAH', 'PLN', 'GBP']
  category: str

  mono_account_id: Optional[str] = None
  mono_account_type: Optional[str] = None
  mono_masked_pan: Optional[str] = None