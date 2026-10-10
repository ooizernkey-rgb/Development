"""
Phase 4: Prioritize Module
Scores each detected event 0-100 and returns the top N.

Score formula:
  score = financial_impact * urgency * (1 - reversibility_difficulty)

  financial_impact  - projected RM loss/gain over 30 days (0-40 range)
  urgency           - how soon it matters (1.0 = now, 0.5 = this week, 0.2 = monitor)
  reversibility     - how hard to fix (0.2 = easy, 0.5 = medium, 0.8 = hard)
"""
import numpy as np
import pandas as pd

# RM value per unit of each metric (for converting to financial impact)
RM_PER_UNIT = {
    "daily_sales": 1.0,       # already in RM
    "daily_expenses": 1.0,    # already in RM
    "customer_count": 14.12,  # avg spend per customer (1200 sales / 85 customers)
    "inventory_value": 1.0,   # already in RM
}

# Urgency by event type
URGENCY = {
    "forecast": 0.9,   # will happen soon
    "trend": 0.7,      # happening now
    "anomaly": 0.5,    # happened, may be ongoing
}

# Reversibility by category
REVERSIBILITY = {
    "sales": 0.3,       # can adjust prices, run promos
    "utilities": 0.2,   # usually fixable (fridge, AC)
    "customers": 0.6,   # harder to win back
    "inventory": 0.2,   # just reorder
    "cash_flow": 0.5,   # medium difficulty
}


def _financial_impact(event, df):
    """Estimate projected RM impact over 30 days."""
    metric = event["metric"]
    dev_pct = event["deviation_pct"] / 100
    rm_per = RM_PER_UNIT.get(metric, 1.0)
    median_val = float(np.median(df[metric].values))

    # Inventory is a one-time loss (stock value), not a daily rate
    if metric == "inventory_value":
        monthly_impact = abs(dev_pct * median_val * rm_per)
    else:
        monthly_impact = abs(dev_pct * median_val * rm_per * 30)
    return round(min(monthly_impact, 15000), 2)


def _urgency(event):
    """How soon does this matter?"""
    base = URGENCY.get(event["type"], 0.5)
    # trends with higher deviation are more urgent
    if event["type"] == "trend" and event["deviation_pct"] > 20:
        base = min(base + 0.2, 1.0)
    return base


def _reversibility(category):
    """How hard is it to fix?"""
    return REVERSIBILITY.get(category, 0.5)


def calculate_score(event, category, df):
    """Calculate a 0-100 priority score."""
    impact = _financial_impact(event, df)
    urgency = _urgency(event)
    rev = _reversibility(category)

    # Normalize financial impact to 0-1 (RM 0 -> 0, RM 10000+ -> 1)
    impact_norm = min(impact / 10000, 1.0)

    # Score = impact * urgency * (1 - reversibility)
    raw = impact_norm * urgency * (1 - rev)
    score = round(raw * 100, 1)
    return score


def prioritize(events, df, top_n=5):
    """Sort events by score and return top N with scores and categories.

    Deduplicates: if both a trend and an anomaly cover the same metric +
    direction, only the higher-scoring one is kept (the user doesn't need
    to see the same issue twice).
    """
    from categorize import categorize
    scored = []
    for event in events:
        cat = categorize(event)
        score = calculate_score(event, cat, df)
        scored.append({
            "event": event,
            "category": cat,
            "score": score,
            "financial_impact": _financial_impact(event, df),
        })
    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate by (metric, direction) - keep highest scoring only
    seen = set()
    unique = []
    for item in scored:
        e = item["event"]
        key = (e["metric"], e["direction"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:top_n]


if __name__ == "__main__":
    from detect import detect
    from categorize import categorize
    df = pd.read_csv("cafe_data.csv")
    events = detect(df)
    ranked = prioritize(events, df)
    print(f"Top {len(ranked)} alerts (ranked by score):\n")
    for i, item in enumerate(ranked, 1):
        e = item["event"]
        print(f"  {i}. [{e['type']:8s}] {e['metric']:16s} score={item['score']:5.1f}  "
              f"impact=RM{item['financial_impact']:,.0f}")
