from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class Expense(BaseModel):
  amount: float
  currency: Literal['USD', 'EUR', 'UAH', 'PLN', 'GBP']
  category: str
  created_at: Optional[datetime] = None
  description: Optional[str] = None
  comment: Optional[str] = None
  mcc: Optional[int] = None
  mcc_category: Optional[str] = None
  counter_name: Optional[str] = None
  counter_edrpou: Optional[str] = None
  currency_code: Optional[int] = None

  mono_account_id: Optional[str] = None
  mono_account_type: Optional[str] = None
  mono_masked_pan: Optional[str] = None
