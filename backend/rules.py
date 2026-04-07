def get_risk_level(days_inactive: int, order_count: int) -> str:
    if order_count == 1 and days_inactive > 60:
        return "High"
    if days_inactive > 90:
        return "High"
    if days_inactive > 60:
        return "Medium"
    if days_inactive > 30:
        return "Low"
    return "Safe"

def get_segment(order_count: int, total_spent: float) -> str:
    if total_spent > 10000:
        return "High Spender"
    if order_count == 1:
        return "One-time"
    if order_count >= 5:
        return "Loyal"
    return "Regular"

def get_suggested_action(risk_level: str, segment: str) -> str:
    if risk_level == "Safe":
        return "No action needed"
    if risk_level == "High":
        if segment == "One-time":
            return "Send win-back discount 20%"
        if segment == "High Spender":
            return "Send personal offer"
        if segment == "Loyal":
            return "Call customer directly"
        return "Send personal outreach email"
    if risk_level == "Medium":
        return "Send reminder email"
    if risk_level == "Low":
        return "Send product recommendation"
    return "No action needed"
