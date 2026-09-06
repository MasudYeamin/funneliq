"""FunnelIQ - load raw CSVs into a SQLite database using the sql/schema.sql DDL."""
import sqlite3
import pandas as pd

DB_PATH = "funneliq.db"

conn = sqlite3.connect(DB_PATH)
with open("sql/schema.sql", "r") as f:
    conn.executescript(f.read())

customers = pd.read_csv("data/raw/customers.csv")
events = pd.read_csv("data/raw/events.csv")
orders = pd.read_csv("data/raw/orders.csv")

customers.to_sql("customers", conn, if_exists="append", index=False)
events.to_sql("events", conn, if_exists="append", index=False)
orders.to_sql("orders", conn, if_exists="append", index=False)

conn.commit()

counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ["customers", "events", "orders"]}
print("Rows loaded:", counts)

conn.close()
