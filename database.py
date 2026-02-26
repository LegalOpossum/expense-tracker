from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, TIMESTAMP
from sqlalchemy.sql import func  
engine = create_engine("postgresql://tracker:trackerpass@localhost:5433/trackerdb")
metadata = MetaData()

expenses = Table(
    "expenses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("amount", Numeric, nullable=False),
    Column("currency", String(3), nullable=False),
    Column("category", String),
    Column("created_at", TIMESTAMP, server_default=func.now()),  
)

metadata.create_all(engine)
print("Таблиця expenses створена ✅")