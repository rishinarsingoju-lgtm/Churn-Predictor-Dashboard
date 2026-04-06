import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import database
from backend.rules import compute_risk_level

app = FastAPI(title="Customer Churn Prediction Dashboard")
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend"),
    name="static",
)


def _dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _parse_iso_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _get_customer_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, phone, created_at FROM customers"
    )
    customers = [row for row in cursor.fetchall()]

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    summary = {
        "total_customers": 0,
        "high_risk_customers": 0,
        "contacted_this_week": 0,
    }
    seen_contacted = set()
    cursor.execute(
        "SELECT DISTINCT customer_id FROM actions WHERE taken_at >= ?",
        (week_ago.isoformat(),),
    )
    for row in cursor.fetchall():
        seen_contacted.add(row[0])

    summary["total_customers"] = len(customers)
    summary["contacted_this_week"] = len(seen_contacted)
    return summary


def _get_customer_base_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT c.id, c.name, c.email, c.phone, c.created_at, MAX(o.order_date) as last_purchase_date, COUNT(o.id) as total_orders "
        "FROM customers c "
        "LEFT JOIN orders o ON c.id = o.customer_id "
        "GROUP BY c.id"
    )
    rows = []
    now = datetime.utcnow()
    for row in cursor.fetchall():
        last_purchase_date = row["last_purchase_date"] or row["created_at"]
        last_purchase_dt = _parse_iso_date(last_purchase_date)
        days_inactive = (now - last_purchase_dt).days
        risk_level = compute_risk_level(days_inactive, row["total_orders"])

        rows.append(
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "created_at": row["created_at"],
                "last_purchase_date": last_purchase_date,
                "days_since_last_purchase": days_inactive,
                "total_orders": row["total_orders"],
                "risk_level": risk_level,
            }
        )

    cursor.execute(
        "SELECT customer_id FROM actions WHERE taken_at >= ?",
        ((datetime.utcnow() - timedelta(days=7)).isoformat(),),
    )
    contacted_ids = {row[0] for row in cursor.fetchall()}
    for row in rows:
        row["contacted_this_week"] = row["id"] in contacted_ids
    return sorted(rows, key=lambda item: item["days_since_last_purchase"], reverse=True)


@app.on_event("startup")
def startup_event():
    database.create_tables()


@app.get("/", response_class=FileResponse)
def homepage():
    return FileResponse(Path(__file__).resolve().parent.parent / "frontend" / "index.html")


@app.get("/customers")
def list_customers():
    conn = database.get_connection()
    customers = _get_customer_base_rows(conn)
    summary = _get_customer_summary(conn)
    conn.close()
    return {"customers": customers, "summary": summary}


@app.get("/customers/{customer_id}")
def customer_detail(customer_id: int):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, created_at FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    if customer is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    cursor.execute(
        "SELECT id, amount, order_date FROM orders WHERE customer_id = ? ORDER BY order_date DESC",
        (customer_id,),
    )
    orders = [
        {
            "id": row["id"],
            "amount": row["amount"],
            "order_date": row["order_date"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return {"customer": _dict_from_row(customer), "orders": orders}


@app.post("/actions")
def log_action(payload: Dict[str, Any]):
    customer_id = payload.get("customer_id")
    action_type = payload.get("action_type")
    if not customer_id or not action_type:
        raise HTTPException(status_code=400, detail="customer_id and action_type are required")

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    taken_at = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO actions (customer_id, action_type, taken_at) VALUES (?, ?, ?)",
        (customer_id, action_type, taken_at),
    )
    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={"message": "Action logged", "customer_id": customer_id, "action_type": action_type})


@app.get("/export/csv")
def export_csv():
    conn = database.get_connection()
    customers = _get_customer_base_rows(conn)
    conn.close()

    output_path = Path(__file__).resolve().parent / "static" / "export.csv"
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "Email", "Last Purchase Date", "Days Inactive", "Risk Level"])
        for customer in customers:
            if customer["risk_level"] in {"High", "Medium"}:
                writer.writerow(
                    [
                        customer["name"],
                        customer["email"],
                        customer["last_purchase_date"],
                        customer["days_since_last_purchase"],
                        customer["risk_level"],
                    ]
                )

    return FileResponse(output_path, media_type="text/csv", filename="at_risk_customers.csv")
