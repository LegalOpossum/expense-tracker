from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import insert, select
from database import engine, expenses

app = FastAPI()

# Модель для валідації запитів
class Expense(BaseModel):
    amount: float
    currency: str
    category: str

@app.post("/expenses")
def add_expense(expense: Expense):
    stmt = insert(expenses).values(
        amount=expense.amount,
        currency=expense.currency,
        category=expense.category
    )
    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()
    return {"status": "ok", "expense": expense.dict()}

@app.get("/expenses")
def get_expenses():
    stmt = select(expenses)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().all()
    return {"expenses": result}