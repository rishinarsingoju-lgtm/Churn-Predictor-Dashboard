import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "churn.db"

CREATE_CUSTOMERS_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    created_at TEXT NOT NULL
);
"""

CREATE_ORDERS_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
"""

CREATE_ACTIONS_SQL = """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_CUSTOMERS_SQL)
    cursor.execute(CREATE_ORDERS_SQL)
    cursor.execute(CREATE_ACTIONS_SQL)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
