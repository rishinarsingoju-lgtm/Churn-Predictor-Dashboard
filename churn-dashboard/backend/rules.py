from datetime import datetime


def compute_risk_level(days_since_last_purchase: int, total_orders: int) -> str:
    if total_orders == 1 and days_since_last_purchase > 60:
        return "High"
    if days_since_last_purchase > 90:
        return "High"
    if days_since_last_purchase > 60:
        return "Medium"
    return "Low"


def format_date(value: str) -> str:
    try:
        date = datetime.fromisoformat(value)
        return date.strftime("%b %d, %Y")
    except ValueError:
        return value
