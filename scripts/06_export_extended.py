"""FunnelIQ - export extended aggregates for the multi-page dashboard replica."""
import json
import pandas as pd

customers = pd.read_csv("data/raw/customers.csv", parse_dates=["signup_date"])
events = pd.read_csv("data/raw/events.csv", parse_dates=["event_date"])
orders = pd.read_csv("data/raw/orders.csv", parse_dates=["order_date"])

# revenue by category
rev_by_cat = (
    orders.groupby("category")["order_value"].agg(["sum", "count", "mean"])
    .sort_values("sum", ascending=False).round(2)
)

# monthly revenue trend
orders["month"] = orders["order_date"].dt.to_period("M").astype(str)
monthly_rev = orders.groupby("month")["order_value"].agg(["sum", "count"]).round(2)

# signups by channel
by_channel = customers["acquisition_channel"].value_counts()

# signups by city
by_city = customers["city"].value_counts()

# monthly signups
customers["month"] = customers["signup_date"].dt.to_period("M").astype(str)
monthly_signups = customers.groupby("month").size()

# purchase conversion + AOV by channel
purchasers = events[events["funnel_step"] == "purchase"][["customer_id"]].drop_duplicates()
cust_channel = customers.set_index("customer_id")["acquisition_channel"]
purchasers["channel"] = purchasers["customer_id"].map(cust_channel)
orders_channel = orders.merge(customers[["customer_id", "acquisition_channel"]], on="customer_id")
channel_stats = (
    customers.groupby("acquisition_channel")
    .agg(signups=("customer_id", "count"))
    .join(purchasers.groupby("channel").size().rename("purchasers"))
    .join(orders_channel.groupby("acquisition_channel")["order_value"].sum().rename("revenue"))
    .fillna(0)
)
channel_stats["conversion_%"] = (channel_stats["purchasers"] / channel_stats["signups"] * 100).round(1)

# AOV by variant
aov_by_variant = orders.groupby("checkout_variant")["order_value"].mean().round(2)

out = {
    "revenue_by_category": [
        {"category": k, "revenue": float(v["sum"]), "orders": int(v["count"]), "aov": float(v["mean"])}
        for k, v in rev_by_cat.iterrows()
    ],
    "monthly_revenue": [
        {"month": k, "revenue": float(v["sum"]), "orders": int(v["count"])}
        for k, v in monthly_rev.iterrows()
    ],
    "signups_by_channel": [{"channel": k, "count": int(v)} for k, v in by_channel.items()],
    "signups_by_city": [{"city": k, "count": int(v)} for k, v in by_city.items()],
    "monthly_signups": [{"month": k, "count": int(v)} for k, v in monthly_signups.items()],
    "channel_stats": [
        {"channel": k, "signups": int(v["signups"]), "purchasers": int(v["purchasers"]),
         "conversion_pct": float(v["conversion_%"]), "revenue": round(float(v["revenue"]), 2)}
        for k, v in channel_stats.iterrows()
    ],
    "aov_by_variant": {k: float(v) for k, v in aov_by_variant.items()},
}
with open("data/processed/dashboard_data_extended.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
