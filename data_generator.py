"""
Phase 1: Data Generator
Generates 90 days of synthetic cafe data with 4 planted problems
so the Detect module has something to catch during the demo.

Planted problems:
  1. Sales decline     - days 76-90: 20% drop on all daily sales
  2. Expense spike     - days 76-90: +RM 250/day extra (electricity)
  3. Customer decline  - days 60-90: gradual -1.5 customers/day
  4. Inventory drop    - days 80-90: -RM 350/day (restocking stopped)

Run:  python data_generator.py
Output: cafe_data.csv
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_cafe_data(output_path=None):
    np.random.seed(42)
    start = datetime(2026, 7, 15)
    dates = [start + timedelta(days=i) for i in range(90)]
    dow = [d.weekday() for d in dates]
    is_weekend = [1 if d >= 5 else 0 for d in dow]

    # --- Base patterns (normal cafe operation) ---
    sales = []
    for i, w in enumerate(is_weekend):
        base = 1500 if w else 1200
        sales.append(round(base + np.random.normal(0, 60), 2))

    expenses = [round(400 + np.random.normal(0, 25), 2) for _ in range(90)]

    customers = []
    for w in is_weekend:
        base = 110 if w else 85
        customers.append(int(round(base + np.random.normal(0, 6))))

    inventory = []
    for i in range(90):
        base = 4800 - (i % 7) * 200  # depletes, restocked weekly
        inventory.append(round(base + np.random.normal(0, 80), 2))

    # --- PLANTED PROBLEM 1: Sales decline (30% drop, days 76-90) ---
    for i in range(75, 90):
        sales[i] = round(sales[i] * 0.70, 2)

    # --- PLANTED PROBLEM 2: Expense spike (+RM 250/day, days 76-90) ---
    for i in range(75, 90):
        expenses[i] = round(expenses[i] + 250, 2)

    # --- PLANTED PROBLEM 3: Customer decline (-1.5/day, days 60-90) ---
    for i in range(60, 90):
        decline = (i - 60) * 1.5
        customers[i] = max(20, int(round(customers[i] - decline)))

    # --- PLANTED PROBLEM 4: Inventory drop (-RM 350/day, days 80-90) ---
    for i in range(80, 90):
        inventory[i] = round(inventory[i] - 350 * (i - 79), 2)

    df = pd.DataFrame({
        "date": dates,
        "daily_sales": sales,
        "daily_expenses": expenses,
        "customer_count": customers,
        "inventory_value": inventory,
    })
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Save to file only if a path is given (None = in-memory only)
    if output_path:
        df.to_csv(output_path, index=False)
        print(f"Generated 90 days of cafe data -> {output_path}")
    print(f"Date range: {df['date'].iloc[0]} to {df['date'].iloc[-1]}")
    print("\nPlanted problems (the AI should find these):")
    print("  1. Sales decline 30%      (days 76-90)")
    print("  2. Expense spike +RM250   (days 76-90)")
    print("  3. Customer decline -1.5/d (days 60-90)")
    print("  4. Inventory drop -RM350/d (days 80-90)")
    return df


if __name__ == "__main__":
    generate_cafe_data("cafe_data.csv")
