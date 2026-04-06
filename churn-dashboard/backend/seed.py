import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from backend.database import create_tables, get_connection, DB_PATH

FIRST_NAMES = [
    "Avery", "Jordan", "Taylor", "Morgan", "Sydney", "Casey", "Riley", "Parker", "Jamie", "Alex"
]
LAST_NAMES = [
    "Morgan", "Bailey", "Reed", "Brooks", "Cooper", "Bell", "Price", "Howard", "Hayes", "Perry"
]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(name: str) -> str:
    local = name.lower().replace(" ", ".")
    domain = random.choice(["brandmail.com", "d2cstore.co", "shopmail.com"])
    return f"{local}{random.randint(1,99)}@{domain}"


def random_phone() -> str:
    return f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"


def build_order_dates(last_purchase_date: datetime, count: int):
    dates = []
    current = last_purchase_date
    for _ in range(count):
        dates.append(current)
        days_back = random.randint(7, 30)
        current -= timedelta(days=days_back)
    return sorted(dates)


def seed_database(customer_count: int = 50):
    if DB_PATH.exists():
        DB_PATH.unlink()

    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    for _ in range(customer_count):
        name = random_name()
        email = random_email(name)
        phone = random_phone()
        days_since_last = random.randint(5, 120)
        last_purchase_date = now - timedelta(days=days_since_last)
        order_count = random.randint(1, 10)
        created_at = (last_purchase_date - timedelta(days=random.randint(30, 365))).isoformat()

        cursor.execute(
            "INSERT INTO customers (name, email, phone, created_at) VALUES (?, ?, ?, ?)",
            (name, email, phone, created_at),
        )
        customer_id = cursor.lastrowid

        order_dates = build_order_dates(last_purchase_date, order_count)
        for order_date in order_dates:
            amount = round(random.uniform(18, 320), 2)
            cursor.execute(
                "INSERT INTO orders (customer_id, amount, order_date) VALUES (?, ?, ?)",
                (customer_id, amount, order_date.isoformat()),
            )

    conn.commit()
    conn.close()
    print(f"Seeded {customer_count} customers into {DB_PATH}")


if __name__ == "__main__":
    seed_database()
