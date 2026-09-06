"""
FunnelIQ - export a compact CUSTOMER-LEVEL fact table for the interactive dashboard.

Instead of pre-aggregated summaries, this emits one row per customer so the
dashboard can recompute every chart live under any filter combination
(the way a real BI tool slices a model).

Encoding: arrays-of-arrays with dimension values as integer indexes, to keep
the payload small enough to inline in a single HTML page.
"""
import json
import pandas as pd
import numpy as np

customers = pd.read_csv("data/raw/customers.csv", parse_dates=["signup_date"])
events = pd.read_csv("data/raw/events.csv", parse_dates=["event_date"])
orders = pd.read_csv("data/raw/orders.csv", parse_dates=["order_date"])

STEP_ORDER = ["view", "add_to_cart", "checkout", "purchase"]
step_rank = {s: i for i, s in enumerate(STEP_ORDER)}

# ---- dimension vocabularies (index -> label) -------------------------------
channels = sorted(customers["acquisition_channel"].unique())
cities = sorted(customers["city"].unique())
variants = ["control", "variant"]
months = sorted(customers["signup_date"].dt.to_period("M").astype(str).unique())
categories = sorted(orders["category"].unique())

ch_ix = {v: i for i, v in enumerate(channels)}
city_ix = {v: i for i, v in enumerate(cities)}
var_ix = {v: i for i, v in enumerate(variants)}
mon_ix = {v: i for i, v in enumerate(months)}

# ---- per-customer deepest funnel step -------------------------------------
events["rank"] = events["funnel_step"].map(step_rank)
max_step = events.groupby("customer_id")["rank"].max()

# ---- per-customer retention bitmask (bit m = active m months after signup) -
signup_period = customers.set_index("customer_id")["signup_date"].dt.to_period("M")
ev = events[["customer_id", "event_date"]].copy()
ev["activity_period"] = ev["event_date"].dt.to_period("M")
ev["signup_period"] = ev["customer_id"].map(signup_period)
ev["mdiff"] = (
    (ev["activity_period"].dt.year - ev["signup_period"].dt.year) * 12
    + (ev["activity_period"].dt.month - ev["signup_period"].dt.month)
)
ev = ev[(ev["mdiff"] >= 0) & (ev["mdiff"] <= 5)]
mask = ev.groupby("customer_id")["mdiff"].apply(lambda s: int(np.bitwise_or.reduce([1 << int(m) for m in s.unique()])))

# ---- per-customer order rollup --------------------------------------------
order_rollup = orders.groupby("customer_id")["order_value"].agg(["count", "sum"])

# ---- monthly revenue rows (order-level is needed for the trend) -----------
orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)
order_months = sorted(orders["order_month"].unique())
omon_ix = {v: i for i, v in enumerate(order_months)}

rows = []
for cid, c in customers.set_index("customer_id").iterrows():
    rows.append([
        ch_ix[c["acquisition_channel"]],
        city_ix[c["city"]],
        var_ix[c["checkout_variant"]],
        mon_ix[c["signup_date"].to_period("M").strftime("%Y-%m")],
        int(max_step.get(cid, 0)),
        int(order_rollup["count"].get(cid, 0)),
        round(float(order_rollup["sum"].get(cid, 0.0)), 2),
        int(mask.get(cid, 1)),
    ])

# order-level rows kept separately (small: ~2,011) for revenue-by-month/category
order_rows = []
cust_dims = customers.set_index("customer_id")
for _, o in orders.iterrows():
    c = cust_dims.loc[o["customer_id"]]
    order_rows.append([
        omon_ix[o["order_month"]],
        categories.index(o["category"]),
        ch_ix[c["acquisition_channel"]],
        city_ix[c["city"]],
        var_ix[c["checkout_variant"]],
        round(float(o["order_value"]), 2),
    ])

out = {
    "dims": {
        "channels": channels, "cities": cities, "variants": variants,
        "signup_months": months, "categories": categories, "order_months": order_months,
        "steps": ["View", "Add to Cart", "Checkout", "Purchase"],
    },
    "customers": rows,        # [channel, city, variant, signupMonth, maxStep, orders, revenue, retentionMask]
    "orders": order_rows,     # [orderMonth, category, channel, city, variant, value]
}
with open("data/processed/fact_table.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"customers rows: {len(rows)}")
print(f"order rows:     {len(order_rows)}")
print(f"dims: {[(k, len(v)) for k, v in out['dims'].items()]}")
