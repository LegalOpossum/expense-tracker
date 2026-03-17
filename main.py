from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from models import Expense
from sqlalchemy import insert, select, update, delete, and_
from database import engine, expenses, mcc_categories
from datetime import datetime
from pydantic import BaseModel, Field
import requests
from fastapi import HTTPException
from pydantic import BaseModel

app = FastAPI()

MONO_CURRENCY_CODES = {
    "UAH": 980,
    "USD": 840,
    "EUR": 978,
    "GBP": 826,
    "PLN": 985,
}


def normalize_text_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized.casefold() or None


def matches_text_filter(candidate: str | None, needle: str | None) -> bool:
    if not needle:
        return True
    if not candidate:
        return False
    normalized_candidate = " ".join(candidate.strip().split()).casefold()
    return needle in normalized_candidate


def parse_currency_code_filter(value: str | None) -> int | None:
    if value is None:
        return None

    normalized = value.strip().upper()
    if not normalized:
        return None

    if normalized.isdigit():
        return int(normalized)

    return MONO_CURRENCY_CODES.get(normalized)


def load_mcc_category_map(mcc_codes: list[int]) -> dict[int, str]:
    clean_codes = [code for code in mcc_codes if code is not None]
    if not clean_codes:
        return {}

    with engine.connect() as conn:
        rows = conn.execute(
            select(mcc_categories.c.mcc, mcc_categories.c.category)
            .where(mcc_categories.c.mcc.in_(clean_codes))
        ).fetchall()

    return {row.mcc: row.category for row in rows}

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
    mcc_map = load_mcc_category_map([
        op.get("mcc") for op in operations
        if op.get("mcc") is not None
    ])

    for op in operations:
        
        amount = abs(op.get("amount", 0)) / 100
        mcc = op.get("mcc")
        mcc_category = mcc_map.get(mcc)

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
            "comment": op.get("comment"),
            "mcc": mcc,
            "mcc_category": mcc_category,
            "counter_name": op.get("counterName"),
            "counter_edrpou": op.get("counterEdrpou"),
            "currency_code": op.get("currencyCode"),
            "mono_account_id": data.account,
        })

    return result


app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# --- CREATE ---
@app.post("/expenses")
def create_expense(expense: Expense):
    with engine.connect() as conn:
        category = expense.category or expense.mcc_category or "Other"
        values = {
            "amount": expense.amount,
            "currency": expense.currency,
            "category": category,
            "description": expense.description,
            "comment": expense.comment,
            "mcc": expense.mcc,
            "mcc_category": expense.mcc_category,
            "counter_name": expense.counter_name,
            "counter_edrpou": expense.counter_edrpou,
            "currency_code": expense.currency_code,
            "mono_account_id": expense.mono_account_id,
            "mono_account_type": expense.mono_account_type,
            "mono_masked_pan": expense.mono_masked_pan,
        }
        if expense.created_at is not None:
            values["created_at"] = expense.created_at

        stmt = insert(expenses).values(**values)
        conn.execute(stmt)
        conn.commit()
    return {"message": "Expense added ✅"}


# --- READ ---
@app.get("/expenses")
def list_expenses(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    amount: float | None = None,
    description: str | None = None,
    currency_code: str | None = None,
):
    with engine.connect() as conn:
        stmt = select(expenses)
        normalized_description = normalize_text_filter(description)
        parsed_currency_code = parse_currency_code_filter(currency_code)
        
        filters = []
        if category:
            filters.append(expenses.c.category == category)
        if date_from:
            filters.append(expenses.c.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            filters.append(expenses.c.created_at <= datetime.fromisoformat(date_to))
        if amount is not None:
            filters.append(expenses.c.amount == amount)
        if parsed_currency_code is not None:
            filters.append(expenses.c.currency_code == parsed_currency_code)
        
        if account_id:
         if account_id == "__manual__":
           filters.append(expenses.c.mono_account_id.is_(None))
         else:
           filters.append(expenses.c.mono_account_id == account_id)  


        if filters:
            stmt = stmt.where(and_(*filters))

          
        
        result = conn.execute(stmt).fetchall()

    items = [dict(row._mapping) for row in result]

    if normalized_description:
        items = [
            item for item in items
            if matches_text_filter(item.get("description"), normalized_description)
            or matches_text_filter(item.get("comment"), normalized_description)
        ]

    return items


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
