import csv
from datetime import datetime
from io import StringIO
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import database
from backend import rules

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

class ActionsPayload(BaseModel):
    customer_ids: List[int]
    action_type: str

def get_customers_data():
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    customers = [dict(row) for row in c.fetchall()]

    c.execute("SELECT customer_id, amount, order_date FROM orders")
    orders = c.fetchall()
    
    order_groups = {}
    for o in orders:
        cid = o["customer_id"]
        if cid not in order_groups:
            order_groups[cid] = []
        order_groups[cid].append(o)

    c.execute("SELECT customer_id, taken_at FROM actions")
    actions = c.fetchall()
    action_groups = {}
    for a in actions:
        cid = a["customer_id"]
        if cid not in action_groups:
            action_groups[cid] = []
        action_groups[cid].append(a)

    conn.close()

    now = datetime.utcnow()
    results = []

    for cust in customers:
        cid = cust["id"]
        c_orders = order_groups.get(cid, [])
        c_actions = action_groups.get(cid, [])

        order_count = len(c_orders)
        total_spent = cust["total_spent"]
        if total_spent is None:
            total_spent = 0.0

        if order_count > 0:
            last_purchase_date = max(o["order_date"] for o in c_orders)
            try:
                date_obj = datetime.fromisoformat(last_purchase_date)
            except:
                date_obj = now
            days_inactive = (now - date_obj).days
            last_purchase_str = last_purchase_date[:10]  # Just YYYY-MM-DD
        else:
            try:
                date_obj = datetime.fromisoformat(cust["created_at"])
            except:
                date_obj = now
            days_inactive = (now - date_obj).days
            last_purchase_str = cust["created_at"][:10] if cust["created_at"] else "N/A"

        risk_level = rules.get_risk_level(days_inactive, order_count)
        segment = rules.get_segment(order_count, total_spent)
        suggested_action = rules.get_suggested_action(risk_level, segment)

        contacted = False
        recovered = False
        last_contacted_date = None
        
        if c_actions:
            last_action_date = max(a["taken_at"] for a in c_actions)
            last_contacted_date = last_action_date
            try:
                last_action_obj = datetime.fromisoformat(last_action_date)
                if (now - last_action_obj).days <= 7:
                    contacted = True
            except:
                pass
                
            # Check recovered: order after action date
            for o in c_orders:
                if o["order_date"] > last_action_date:
                    recovered = True
                    break

        results.append({
            "id": cid,
            "name": cust["name"],
            "email": cust["email"],
            "days_inactive": days_inactive,
            "last_purchase_date": last_purchase_str,
            "order_count": order_count,
            "total_spent": total_spent,
            "risk_level": risk_level,
            "segment": segment,
            "suggested_action": suggested_action,
            "contacted": contacted,
            "last_contacted_date": last_contacted_date,
            "recovered": recovered
        })

    return results

def apply_filters(data, risk="all", segment="all", min_days=None, max_days=None, sort_by="days_inactive", order="desc"):
    filtered = data
    if risk and risk.lower() != "all":
        r_list = [r.strip().lower() for r in risk.split(",")]
        filtered = [c for c in filtered if c["risk_level"].lower() in r_list]
    
    if segment and segment.lower() != "all":
        s_list = [s.strip().lower() for s in segment.split(",")]
        filtered = [c for c in filtered if c["segment"].lower() in s_list]

    if min_days is not None:
        filtered = [c for c in filtered if c["days_inactive"] is not None and c["days_inactive"] >= min_days]
    
    if max_days is not None:
        filtered = [c for c in filtered if c["days_inactive"] is not None and c["days_inactive"] <= max_days]

    if sort_by not in ["days_inactive", "total_spent"]:
        sort_by = "days_inactive"

    reverse = (order.lower() == "desc")
    
    def sort_key(c):
        val = c[sort_by]
        return val if val is not None else -1

    filtered.sort(key=sort_key, reverse=reverse)
    return filtered

@app.get("/")
def index():
    return FileResponse(
        "frontend/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/customers")
def get_customers(risk: str = "all", segment: str = "all", min_days: Optional[int] = None, max_days: Optional[int] = None, sort_by: str = "days_inactive", order: str = "desc"):
    data = get_customers_data()
    data = apply_filters(data, risk, segment, min_days, max_days, sort_by, order)
    return data

@app.get("/customers/{cid}")
def get_single_customer(cid: int):
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id=?", (cid,))
    cust = c.fetchone()
    if not cust:
        conn.close()
        raise HTTPException(404, "Customer not found")
    c.execute("SELECT * FROM orders WHERE customer_id=?", (cid,))
    orders = [dict(o) for o in c.fetchall()]
    conn.close()
    return {"customer": dict(cust), "orders": orders}

@app.post("/actions")
def post_actions(payload: ActionsPayload):
    conn = database.get_connection()
    c = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    for cid in payload.customer_ids:
        c.execute("INSERT INTO actions (customer_id, action_type, taken_at) VALUES (?, ?, ?)",
                  (cid, payload.action_type, now_str))
    conn.commit()
    conn.close()
    return {"success": True, "count": len(payload.customer_ids)}

@app.get("/export/csv")
def export_csv(risk: str = "all", segment: str = "all", min_days: Optional[int] = None, max_days: Optional[int] = None, sort_by: str = "days_inactive", order: str = "desc"):
    data = get_customers_data()
    filtered = apply_filters(data, risk, segment, min_days, max_days, sort_by, order)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "days_inactive", "risk_level", "segment", "suggested_action", "total_spent"])
    for row in filtered:
        writer.writerow([row["name"], row["email"], row["days_inactive"], row["risk_level"], row["segment"], row["suggested_action"], row["total_spent"]])
    
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    filter_name = risk.replace(",", "_") if risk != "all" else "all"
    response.headers["Content-Disposition"] = f"attachment; filename={filter_name}-customers.csv"
    return response

@app.post("/upload/csv")
async def upload_csv(request: Request):
    try:
        from fastapi import UploadFile
        # fallback to raw body if multipart isn't available
    except ImportError:
        pass
    
    # Let's use form data parsing. If python-multipart is missing, this might fail,
    # but the prompt demands 'multipart/form-data'. 
    # To play very safe and avoid pip issues without python-multipart:
    content_type = request.headers.get('content-type', '')
    if 'multipart/form-data' in content_type:
        form = await request.form()
        if "file" not in form:
            return {"success": False, "error": "No file uploaded"}
        up_file = form["file"]
        content = await up_file.read()
    else:
        # Fallback reading raw body
        content = await request.body()
        
    text = content.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    
    conn = database.get_connection()
    c = conn.cursor()
    
    imported = 0
    skipped = 0
    now_str = datetime.utcnow().isoformat()
    
    for row in reader:
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        if not name or not email:
            skipped += 1
            continue
            
        c.execute("SELECT id FROM customers WHERE email=?", (email,))
        if c.fetchone():
            skipped += 1
            continue
            
        phone = row.get("phone", "")
        # defaults
        order_count = 1
        total_spent = 0.0
        try:
            total_spent = float(row.get("total_spent", 0.0))
        except:
            total_spent = 0.0
        
        last_purchase_date = row.get("last_purchase_date", "").strip()
        if not last_purchase_date:
            last_purchase_date = now_str
            
        c.execute("INSERT INTO customers (name, email, phone, created_at, total_spent) VALUES (?, ?, ?, ?, ?)",
                  (name, email, phone, now_str, total_spent))
        cid = c.lastrowid
        
        c.execute("INSERT INTO orders (customer_id, amount, order_date) VALUES (?, ?, ?)",
                  (cid, total_spent, last_purchase_date))
        imported += 1
        
    conn.commit()
    conn.close()
    
    return {"success": True, "imported": imported, "skipped": skipped}

@app.get("/actions/log")
def action_log():
    conn = database.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT customers.name as customer_name, customers.email, actions.action_type, actions.taken_at
        FROM actions
        JOIN customers ON actions.customer_id = customers.id
        ORDER BY actions.taken_at DESC
        LIMIT 50
    ''')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
