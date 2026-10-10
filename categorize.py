"""
Phase 3: Categorize Module
Simple rules engine that labels each detected event with an issue category.

Categories:
  cash_flow   - money in/out problems
  sales       - revenue going up or down
  inventory   - stock too low or too high
  utilities   - bills spiking
  customers   - foot traffic or retention changes

Also provides action hints per category (used by the Explain module).
"""

# Map (metric, direction) -> category
CATEGORY_MAP = {
    ("daily_sales", "down"): "sales",
    ("daily_sales", "up"): "sales",
    ("daily_sales", "below"): "sales",
    ("daily_sales", "above"): "sales",
    ("daily_expenses", "up"): "utilities",
    ("daily_expenses", "down"): "utilities",
    ("daily_expenses", "above"): "utilities",
    ("daily_expenses", "below"): "utilities",
    ("customer_count", "down"): "customers",
    ("customer_count", "up"): "customers",
    ("customer_count", "below"): "customers",
    ("customer_count", "above"): "customers",
    ("inventory_value", "down"): "inventory",
    ("inventory_value", "up"): "inventory",
    ("inventory_value", "below"): "inventory",
    ("inventory_value", "above"): "inventory",
}

# Human-readable category labels
CATEGORY_LABELS = {
    "sales": "Sales",
    "utilities": "Utilities",
    "customers": "Customers",
    "inventory": "Inventory",
    "cash_flow": "Cash flow",
}

# Suggested actions per category (used by Explain module)
ACTION_HINTS = {
    "sales": "Check if a new competitor opened nearby, or run a promo on your best-selling item.",
    "utilities": "Check fridge seals and AC filters - these are the usual suspects for cafes.",
    "customers": "Review your recent reviews or social media. Ask staff if they noticed anything.",
    "inventory": "Contact your supplier immediately and reorder. Check if deliveries were missed.",
    "cash_flow": "Review pending payments. Consider short-term financing or negotiate supplier terms.",
}


def categorize(event):
    """Return a category string for a detected event."""
    key = (event["metric"], event["direction"])
    return CATEGORY_MAP.get(key, "cash_flow")


def get_action_hint(category):
    """Return a suggested action string for a category."""
    return ACTION_HINTS.get(category, "Investigate the cause and consult your accountant.")


if __name__ == "__main__":
    from detect import detect
    import pandas as pd
    df = pd.read_csv("cafe_data.csv")
    events = detect(df)
    for e in events:
        cat = categorize(e)
        print(f"  {e['metric']:20s} {e['direction']:5s} -> {cat}")
