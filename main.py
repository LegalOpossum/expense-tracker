from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from models import Expense
from sqlalchemy import insert, select, update, delete, and_
from database import engine, expenses
from datetime import datetime

app = FastAPI()

# Статика тепер окремо
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# --- CREATE ---
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
    return {"message": "Expense added ✅"}


# --- READ ---
@app.get("/expenses")
def list_expenses(
    category: str | None = Query(None),  # фільтр за категорією
    date_from: str | None = Query(None),  # фільтр від дати (yyyy-mm-dd)
    date_to: str | None = Query(None)     # фільтр до дати
):
    with engine.connect() as conn:
        stmt = select(expenses)
        
        filters = []
        if category:
            filters.append(expenses.c.category == category)
        if date_from:
            filters.append(expenses.c.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            filters.append(expenses.c.created_at <= datetime.fromisoformat(date_to))
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        result = conn.execute(stmt).fetchall()
    
    return [dict(row._mapping) for row in result]


# --- UPDATE ---
@app.patch("/expenses/{expense_id}")
def update_expense(expense_id: int, updated: Expense):
    with engine.connect() as conn:
        stmt = update(expenses).where(expenses.c.id == expense_id).values(
            amount=updated.amount,
            currency=updated.currency,
            category=updated.category
        )
        result = conn.execute(stmt)
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} updated ✅"}


# --- DELETE ---
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    with engine.connect() as conn:
        stmt = delete(expenses).where(expenses.c.id == expense_id)
        result = conn.execute(stmt)
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} deleted ✅"}