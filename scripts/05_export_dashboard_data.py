"""FunnelIQ - export compact JSON aggregates (order-value histogram) for the HTML dashboard replica."""
import json
import pandas as pd

orders = pd.read_csv("data/raw/orders.csv")

bins = list(range(0, 5001, 500))
counts = pd.cut(orders["order_value"], bins=bins).value_counts(sort=False)
hist = [{"range": f"{int(iv.left)}-{int(iv.right)}", "count": int(c)} for iv, c in counts.items()]

out = {
    "order_value_hist": hist,
    "avg_order_value": round(float(orders["order_value"].mean()), 2),
    "median_order_value": round(float(orders["order_value"].median()), 2),
    "total_revenue": round(float(orders["order_value"].sum()), 2),
    "total_orders": int(len(orders)),
}
with open("data/processed/dashboard_data.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
