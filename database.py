from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, TIMESTAMP
from sqlalchemy.sql import func  
engine = create_engine("postgresql://tracker:trackerpass@localhost:5433/trackerdb")
metadata = MetaData()

DEFAULT_MCC_CATEGORIES = [
  (4111, "Transport"),
  (4121, "Taxi"),
  (4131, "Bus"),
  (4511, "Flights"),
  (4784, "Tolls"),
  (4812, "Telecom"),
  (4814, "Telecom"),
  (4816, "Digital services"),
  (4829, "Transfers"),
  (4899, "Digital services"),
  (4900, "Utilities"),
  (5200, "Home goods"),
  (5211, "Home goods"),
  (5231, "Hardware"),
  (5251, "Building supplies"),
  (5261, "Garden"),
  (5311, "Department store"),
  (5331, "Variety store"),
  (5399, "General shopping"),
  (5411, "Groceries"),
  (5422, "Meat"),
  (5441, "Candy"),
  (5451, "Dairy"),
  (5462, "Bakery"),
  (5499, "Food store"),
  (5511, "Car sales"),
  (5533, "Auto parts"),
  (5541, "Fuel"),
  (5542, "Fuel"),
  (5611, "Menswear"),
  (5621, "Womenswear"),
  (5631, "Accessories"),
  (5651, "Clothing"),
  (5661, "Shoes"),
  (5691, "Clothing"),
  (5699, "Fashion"),
  (5712, "Furniture"),
  (5719, "Home decor"),
  (5722, "Appliances"),
  (5732, "Electronics"),
  (5734, "Computer software"),
  (5735, "Music"),
  (5811, "Catering"),
  (5812, "Restaurants"),
  (5813, "Bars"),
  (5814, "Fast food"),
  (5912, "Pharmacy"),
  (5921, "Alcohol"),
  (5941, "Sport goods"),
  (5942, "Books"),
  (5943, "Office supplies"),
  (5944, "Jewelry"),
  (5945, "Toys"),
  (5947, "Gifts"),
  (5948, "Leather goods"),
  (5949, "Textiles"),
  (5968, "Subscriptions"),
  (5970, "Art"),
  (5977, "Cosmetics"),
  (5992, "Florist"),
  (5993, "Tobacco"),
  (5994, "Newsstand"),
  (5995, "Pets"),
  (5999, "Retail"),
  (6010, "Cash"),
  (6011, "ATM"),
  (6012, "Financial services"),
  (6300, "Insurance"),
  (6513, "Real estate"),
  (7011, "Hotels"),
  (7210, "Laundry"),
  (7299, "Services"),
  (7311, "Advertising"),
  (7399, "Business services"),
  (7512, "Car rental"),
  (7538, "Auto service"),
  (7832, "Cinema"),
  (7922, "Events"),
  (7995, "Entertainment"),
  (7997, "Clubs"),
  (8011, "Medical"),
  (8021, "Dental"),
  (8043, "Optics"),
  (8099, "Healthcare"),
  (8211, "Education"),
  (8241, "Training"),
  (8299, "Education"),
  (8398, "Charity"),
  (8661, "Donations"),
  (8999, "Professional services"),
  (9211, "Court fees"),
  (9222, "Fines"),
  (9311, "Taxes"),
  (9399, "Government"),
  (9402, "Postal services"),
]

expenses = Table(
  "expenses",
  metadata,
  Column("id", Integer, primary_key=True),
  Column("amount", Numeric, nullable=False),
  Column("currency", String(3), nullable=False),
  Column("category", String),
  Column("description", String, nullable=True),
  Column("comment", String, nullable=True),
  Column("mcc", Integer, nullable=True),
  Column("mcc_category", String, nullable=True),
  Column("counter_name", String, nullable=True),
  Column("counter_edrpou", String, nullable=True),
  Column("currency_code", Integer, nullable=True),
  Column("mono_account_id", String, nullable=True),
  Column("mono_account_type", String, nullable=True),
  Column("mono_masked_pan", String, nullable=True),
  Column("created_at", TIMESTAMP, server_default=func.now()),
)

mcc_categories = Table(
  "mcc_categories",
  metadata,
  Column("mcc", Integer, primary_key=True),
  Column("category", String, nullable=False),
)

metadata.create_all(engine)

with engine.begin() as conn:
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS description VARCHAR")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS comment VARCHAR")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS mcc INTEGER")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS mcc_category VARCHAR")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS counter_name VARCHAR")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS counter_edrpou VARCHAR")
  conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS currency_code INTEGER")

  for mcc, category in DEFAULT_MCC_CATEGORIES:
    conn.exec_driver_sql(
      """
      INSERT INTO mcc_categories (mcc, category)
      VALUES (%s, %s)
      ON CONFLICT (mcc) DO UPDATE SET category = EXCLUDED.category
      """,
      (mcc, category),
    )

print("Таблиця expenses створена ✅")
