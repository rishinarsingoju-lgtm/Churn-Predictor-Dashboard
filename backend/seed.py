import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Setup path so running from anywhere works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import create_tables, get_connection

FIRST_NAMES = ["Avery", "Jordan", "Taylor", "Morgan", "Sydney", "Casey", "Riley", "Parker", "Jamie", "Alex"]
LAST_NAMES = ["Morgan", "Bailey", "Reed", "Brooks", "Cooper", "Bell", "Price", "Howard", "Hayes", "Perry"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_email(name):
    local = name.lower().replace(" ", ".") + str(random.randint(1,999))
    domain = random.choice(["brandmail.com", "d2cstore.co", "shopmail.com"])
    return f"{local}@{domain}"

def random_phone():
    return f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"

def seed():
    create_tables()
    conn = get_connection()
    # Clear existing data for fresh seed
    conn.execute("DELETE FROM customers")
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM actions")
    
    now = datetime.utcnow()
    cursor = conn.cursor()

    patterns = [
        {"type": "one_time", "count": 10},
        {"type": "big_spender", "count": 5},
        {"type": "old_churned", "count": 10},
        {"type": "regular", "count": 15},
        {"type": "loyal", "count": 10},
    ]

    for p in patterns:
        for _ in range(p["count"]):
            name = random_name()
            email = random_email(name)
            created_at = (now - timedelta(days=random.randint(100, 400))).isoformat()
            cursor.execute(
                "INSERT INTO customers (name, email, phone, created_at, total_spent) VALUES (?, ?, ?, ?, ?)",
                (name, email, random_phone(), created_at, 0.0)
            )
            cid = cursor.lastrowid
            
            p_type = p["type"]
            if p_type == "one_time":
                order_count = 1
                days_inactive = random.randint(60, 120)
                amounts = [random.uniform(50, 150)]
            elif p_type == "big_spender":
                order_count = random.randint(9, 15)
                days_inactive = random.randint(5, 45)
                amounts = [random.uniform(1000, 2000) for _ in range(order_count)]
                if sum(amounts) <= 10000:
                    amounts[0] += 10000
            elif p_type == "old_churned":
                order_count = random.randint(2, 5)
                days_inactive = random.randint(101, 300)
                amounts = [random.uniform(20, 100) for _ in range(order_count)]
            elif p_type == "regular":
                order_count = random.randint(2, 4)
                days_inactive = random.randint(10, 80)
                amounts = [random.uniform(50, 150) for _ in range(order_count)]
            elif p_type == "loyal":
                order_count = random.randint(5, 10)
                days_inactive = random.randint(1, 29)
                amounts = [random.uniform(20, 100) for _ in range(order_count)]

            total_spent = sum(amounts)
            cursor.execute("UPDATE customers SET total_spent=? WHERE id=?", (total_spent, cid))
            
            # Place last order at days_inactive
            last_order_date = now - timedelta(days=days_inactive)
            cursor.execute("INSERT INTO orders (customer_id, amount, order_date) VALUES (?, ?, ?)",
                           (cid, amounts[0], last_order_date.isoformat()))
            
            curr_date = last_order_date
            for amt in amounts[1:]:
                curr_date = curr_date - timedelta(days=random.randint(15, 60))
                cursor.execute("INSERT INTO orders (customer_id, amount, order_date) VALUES (?, ?, ?)",
                               (cid, amt, curr_date.isoformat()))
    
    conn.commit()
    conn.close()
    print("Seed complete.")

if __name__ == "__main__":
    seed()
