from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from models import Expense
from sqlalchemy import insert, select, update, delete, and_
from database import engine, expenses
from datetime import datetime
from pydantic import BaseModel, Field
import requests
from fastapi import HTTPException
from pydantic import BaseModel

app = FastAPI()

class MonoStatementRequest(BaseModel):
    token: str
    account: str = "0"
    from_ts: int = Field(alias="from")
    to_ts: int = Field(alias="to")

class MonoTokenRequest(BaseModel):
    token: str

@app.post("/monobank/statement")
def monobank_statement(data: MonoStatementRequest):
    url = f"https://api.monobank.ua/personal/statement/{data.account}/{data.from_ts}/{data.to_ts}"

    headers = {
        "X-Token": data.token
    }

    response = requests.get(url, headers=headers)

    # ❌ якщо помилка від monobank
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    operations = response.json()

    result = []

    for op in operations:
        
        amount = abs(op.get("amount", 0)) / 100

        # код валюти → ISO
        currency_map = {
            980: "UAH",
            840: "USD",
            978: "EUR"
        }
        currency = currency_map.get(op.get("currencyCode"), "UAH")

        result.append({
            "time": op.get("time"),
            "amount": amount,
            "currency": currency,
            "description": op.get("description", "Monobank"),
            "mono_account_id": data.account,
        })

    return result


app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# --- CREATE ---
@app.post("/expenses")
def create_expense(expense: Expense):
    with engine.connect() as conn:
        stmt = insert(expenses).values(
    amount=expense.amount,
    currency=expense.currency,
    category=expense.category,

    mono_account_id=expense.mono_account_id,
    mono_account_type=expense.mono_account_type,
    mono_masked_pan=expense.mono_masked_pan,
)
        conn.execute(stmt)
        conn.commit()
    return {"message": "Expense added ✅"}


# --- READ ---
@app.get("/expenses")
def list_expenses(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,   # NEW
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
        
        if account_id:
         if account_id == "__manual__":
           filters.append(expenses.c.mono_account_id.is_(None))
         else:
           filters.append(expenses.c.mono_account_id == account_id)  


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

@app.post("/monobank/accounts")
def monobank_accounts(data: MonoTokenRequest):
    url = "https://api.monobank.ua/personal/client-info"
    headers = {"X-Token": data.token}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    payload = r.json()
    accounts = payload.get("accounts", [])

    
    return [
        {
            "id": a.get("id"),
            "type": a.get("type"),
            "currencyCode": a.get("currencyCode"),
            "currency": {980:"UAH",840:"USD",978:"EUR",826:"GBP",985:"PLN"}.get(a.get("currencyCode"), ""),
            "maskedPan": a.get("maskedPan", []),
        }
        for a in accounts
        if a.get("id")
    ]