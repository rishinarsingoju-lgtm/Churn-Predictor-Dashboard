import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "churn.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    # customers: id, name, email, phone, created_at, total_spent
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        created_at TEXT,
        total_spent REAL DEFAULT 0.0
    );
    """)
    # Add total_spent column if missing via ALTER TABLE
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN total_spent REAL DEFAULT 0.0;")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount REAL,
        order_date TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        action_type TEXT,
        taken_at TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
