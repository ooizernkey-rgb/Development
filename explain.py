"""
Phase 5: Explain Module
Turns each prioritized alert into 3 plain-language sentences:

  1. What happened  (with numbers)
  2. Why it matters  (in RM)
  3. What to try     (one concrete action)

Uses templates per category - no LLM needed, works offline.
"""
from categorize import get_action_hint, CATEGORY_LABELS
from detect import METRIC_LABELS

# Priority label based on score
def _priority_label(score):
    if score >= 60:
        return "URGENT"
    elif score >= 30:
        return "WATCH"
    else:
        return "MONITOR"

# Color for the priority badge (used by the UI)
def _priority_color(score):
    if score >= 60:
        return "#E24B4A"  # red
    elif score >= 30:
        return "#EF9F27"  # amber
    else:
        return "#639922"  # green

# Templates per category and direction
# Placeholders: {metric}, {direction}, {deviation_pct}, {actual}, {expected},
#               {impact}, {action}, {duration}, {threshold}
TEMPLATES = {
    "sales": {
        "down": "Your {metric} has dropped {deviation_pct}% (from RM{expected} to RM{actual} per day). "
                "At this rate, you'll lose about RM{impact} this month. "
                "Try this: {action}",
        "up": "Your {metric} is up {deviation_pct}% above normal (RM{actual} vs RM{expected}). "
              "This is adding about RM{impact}/month to your revenue. "
              "Keep doing what's working.",
    },
    "utilities": {
        "up": "Your {metric} spiked {deviation_pct}% (from RM{expected} to RM{actual} per day). "
              "That's about RM{impact} extra per month. "
              "Try this: {action}",
        "down": "Your {metric} dropped {deviation_pct}%. "
                "This saves about RM{impact}/month. "
                "No action needed.",
    },
    "customers": {
        "down": "Your {metric} has fallen {deviation_pct}% (from {expected} to {actual} per day). "
                "Fewer customers means about RM{impact}/month in lost revenue. "
                "Try this: {action}",
        "up": "Your {metric} is up {deviation_pct}%. "
              "More people are coming in. "
              "Keep it up.",
    },
    "inventory": {
        "down": "Your {metric} is dropping and may fall below RM{threshold} in about {forecast_day} days. "
                "Current value: RM{actual}. "
                "Try this: {action}",
        "up": "Your {metric} is above normal at RM{actual}. "
              "No action needed.",
    },
    "cash_flow": {
        "down": "Your cash balance is trending down {deviation_pct}%. "
                "Projected impact: RM{impact}/month. "
                "Try this: {action}",
        "up": "Your cash balance is improving. "
              "No action needed.",
    },
}


def explain(event, category, score, financial_impact, df):
    """Generate a 3-sentence plain-language explanation for an alert."""
    direction = event.get("direction", "down")

    # Normalize forecast directions to template directions
    template_dir = direction
    if direction == "below":
        template_dir = "down"
    elif direction == "above":
        template_dir = "up"

    # Look up template: try (category, template_dir), then fallback to cash_flow
    cat_templates = TEMPLATES.get(category, {})
    template = cat_templates.get(template_dir)
    if template is None:
        cf_templates = TEMPLATES.get("cash_flow", {})
        template = cf_templates.get(template_dir, cf_templates.get("down"))

    # Fill in placeholders
    text = template.format(
        metric=METRIC_LABELS.get(event["metric"], event["metric"]).lower(),
        direction=direction,
        deviation_pct=event.get("deviation_pct", 0),
        actual=f"{event.get('actual_value', 0):,.0f}",
        expected=f"{event.get('expected_value', 0):,.0f}",
        impact=f"{financial_impact:,.0f}",
        action=get_action_hint(category),
        duration=event.get("duration_days", 1),
        threshold=f"{event.get('threshold_value', 1000):,.0f}",
        forecast_day=event.get("forecast_day", 7),
    )

    return {
        "priority": _priority_label(score),
        "priority_color": _priority_color(score),
        "category_label": CATEGORY_LABELS.get(category, category),
        "metric_label": METRIC_LABELS.get(event["metric"], event["metric"]),
        "text": text,
        "action": get_action_hint(category),
    }


if __name__ == "__main__":
    import pandas as pd
    from detect import detect
    from prioritize import prioritize
    df = pd.read_csv("cafe_data.csv")
    events = detect(df)
    ranked = prioritize(events, df)
    print(f"Explaining top {len(ranked)} alerts:\n")
    for i, item in enumerate(ranked, 1):
        e = item["event"]
        result = explain(e, item["category"], item["score"], item["financial_impact"], df)
        print(f"  {i}. [{result['priority']}] {result['metric_label']}")
        print(f"     {result['text']}")
        print()
