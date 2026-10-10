"""
Phase 2: Detect Module
Three detection methods running in parallel:

  1. Anomaly detection  - flags days where a metric is >2 standard
                         deviations from its 30-day rolling average.
                         Requires 2+ consecutive flagged days (false-alarm filter).

  2. Trend detection   - compares last 7 days' average to the previous
                         7 days' average. Flags if change >= 10%.

  3. Forecast          - linear regression on last 30 days, projects 7 days
                         ahead. Flags if the forecast crosses a hard threshold.

Each event returned as a dict:
  {date, metric, type, direction, actual_value, expected_value,
   deviation_pct, confidence}
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

METRICS = ["daily_sales", "daily_expenses", "customer_count", "inventory_value"]

# Hard thresholds - if a metric crosses these, flag immediately
THRESHOLDS = {
    "daily_sales":     {"min": 500,  "max": None},
    "daily_expenses":  {"min": None, "max": 700},
    "customer_count":  {"min": 40,   "max": None},
    "inventory_value": {"min": 1000, "max": None},
}

# Human-readable names for display
METRIC_LABELS = {
    "daily_sales": "Daily sales",
    "daily_expenses": "Daily expenses",
    "customer_count": "Customer count",
    "inventory_value": "Inventory value",
}


def _std_anomalies(df):
    """Method 1: 2-std deviation from 30-day rolling mean, 2+ consecutive days."""
    events = []
    for metric in METRICS:
        vals = df[metric].values
        rolling_mean = pd.Series(vals).rolling(30, min_periods=10).mean()
        rolling_std = pd.Series(vals).rolling(30, min_periods=10).std()

        flagged = []
        for i in range(len(vals)):
            if pd.notna(rolling_std.iloc[i]) and rolling_std.iloc[i] > 0:
                z = abs(vals[i] - rolling_mean.iloc[i]) / rolling_std.iloc[i]
                if z >= 2.0:
                    direction = "down" if vals[i] < rolling_mean.iloc[i] else "up"
                    flagged.append((i, direction, vals[i], rolling_mean.iloc[i], z))

        # Group consecutive flagged days (same direction, gap <= 1 day)
        groups = []
        current = []
        for item in flagged:
            if not current:
                current = [item]
            elif item[0] - current[-1][0] <= 1 and item[1] == current[-1][1]:
                current.append(item)
            else:
                groups.append(current)
                current = [item]
        if current:
            groups.append(current)

        # Only keep groups with 2+ consecutive days (false-alarm filter)
        for group in groups:
            if len(group) >= 2:
                first = group[0]
                last = group[-1]
                median_val = float(np.median([g[2] for g in group]))
                expected = float(round(group[0][3], 2))
                dev_pct = round(abs((median_val - expected) / expected) * 100, 1) if expected else 0
                events.append({
                    "date": str(df.iloc[last[0]]["date"]),
                    "metric": metric,
                    "type": "anomaly",
                    "direction": first[1],
                    "actual_value": round(median_val, 2),
                    "expected_value": expected,
                    "deviation_pct": dev_pct,
                    "confidence": round(min(float(np.mean([g[4] for g in group])) / 4, 1), 2),
                    "start_date": str(df.iloc[first[0]]["date"]),
                    "end_date": str(df.iloc[last[0]]["date"]),
                    "duration_days": len(group),
                })
    return events


def _trend_detection(df):
    """Method 2: compare last 7 days avg to median of all prior data, flag if >= 10%.

    Using the median (instead of previous-7-day avg) as the baseline is more
    robust: it catches sustained declines that started more than 7 days ago,
    which a previous-7 comparison would miss (both periods would look the same).
    """
    events = []
    for metric in METRICS:
        vals = df[metric].values
        if len(vals) < 14:
            continue
        recent_avg = float(np.mean(vals[-7:]))
        # Median of all data EXCEPT the last 7 days = robust "normal" baseline
        baseline = float(np.median(vals[:-7]))
        if baseline == 0:
            continue
        change_pct = ((recent_avg - baseline) / baseline) * 100
        if abs(change_pct) >= 10:
            direction = "down" if change_pct < 0 else "up"
            events.append({
                "date": str(df.iloc[-1]["date"]),
                "metric": metric,
                "type": "trend",
                "direction": direction,
                "actual_value": round(recent_avg, 2),
                "expected_value": round(baseline, 2),
                "deviation_pct": round(abs(change_pct), 1),
                "confidence": round(min(abs(change_pct) / 20, 1.0), 2),
                "start_date": str(df.iloc[-7]["date"]),
                "end_date": str(df.iloc[-1]["date"]),
                "duration_days": 7,
            })
    return events


def _forecast(df):
    """Method 3: linear regression on last 30 days, project 7 days, check thresholds."""
    events = []
    for metric in METRICS:
        vals = df[metric].values
        recent = vals[-30:]
        X = np.arange(len(recent)).reshape(-1, 1)
        y = recent
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.arange(len(recent), len(recent) + 7).reshape(-1, 1)
        predicted = model.predict(future_X)

        thresh = THRESHOLDS.get(metric, {})
        for i, pred in enumerate(predicted):
            crossed = None
            if thresh.get("min") and pred < thresh["min"]:
                crossed = "below"
            elif thresh.get("max") and pred > thresh["max"]:
                crossed = "above"
            if crossed:
                current_val = float(vals[-1])
                dev = abs((pred - current_val) / current_val * 100) if current_val else 0
                forecast_date = pd.Timestamp(df.iloc[-1]["date"]) + pd.Timedelta(days=i + 1)
                events.append({
                    "date": str(forecast_date.date()),
                    "metric": metric,
                    "type": "forecast",
                    "direction": crossed,
                    "actual_value": round(float(pred), 2),
                    "expected_value": round(current_val, 2),
                    "deviation_pct": round(dev, 1),
                    "confidence": 0.75,
                    "threshold_value": thresh.get("min") or thresh.get("max"),
                    "forecast_day": i + 1,
                })
                break  # only report first crossing
    return events


def detect(df):
    """Main entry point. Returns a list of detected events."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    anomalies = _std_anomalies(df)
    trends = _trend_detection(df)
    forecasts = _forecast(df)

    # Deduplicate: if a trend and anomaly cover the same metric+direction, keep the trend
    seen = set()
    combined = []
    for ev in trends + forecasts + anomalies:
        key = (ev["metric"], ev["direction"], ev["type"])
        if key not in seen:
            seen.add(key)
            combined.append(ev)
    return combined


if __name__ == "__main__":
    df = pd.read_csv("cafe_data.csv")
    events = detect(df)
    print(f"Detected {len(events)} events:\n")
    for e in events:
        print(f"  [{e['type']:8s}] {METRIC_LABELS.get(e['metric'], e['metric']):16s} "
              f"{e['direction']:5s} {e['deviation_pct']}%  (conf {e['confidence']})")
