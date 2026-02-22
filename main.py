from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from models import Expense
from sqlalchemy import insert, select
from database import engine, expenses

app = FastAPI()

# статика тепер окремо
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.post("/expenses")
def create_expense(expense: Expense):
    with engine.connect() as conn:
        stmt = insert(expenses).values(
            amount=expense.amount,
            currency=expense.currency,
            category=expense.category
        )
        conn.execute(stmt)
        conn.commit()
    return {"message": "Expense added"}


@app.get("/expenses")
def list_expenses():
    with engine.connect() as conn:
        stmt = select(expenses)
        result = conn.execute(stmt).fetchall()
    return [dict(row._mapping) for row in result]