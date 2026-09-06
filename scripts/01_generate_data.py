"""
FunnelIQ - synthetic data generator
Creates a realistic e-commerce dataset: customers, sessions (funnel events),
and orders, spanning 6 months, with a built-in A/B test (checkout_variant)
and monthly-cohort retention decay baked into the random process.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N_CUSTOMERS = 4000
START_DATE = datetime(2025, 3, 1)
N_MONTHS = 6
FUNNEL_STEPS = ["view", "add_to_cart", "checkout", "purchase"]

CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad"]
CHANNELS = ["organic_search", "paid_social", "email", "direct", "referral"]
CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty", "Sports", "Books"]

# ---- customers ----------------------------------------------------------
signup_month_offset = rng.integers(0, N_MONTHS, size=N_CUSTOMERS)
signup_dates = [START_DATE + timedelta(days=int(m * 30 + rng.integers(0, 28))) for m in signup_month_offset]

customers = pd.DataFrame({
    "customer_id": np.arange(1, N_CUSTOMERS + 1),
    "signup_date": signup_dates,
    "city": rng.choice(CITIES, N_CUSTOMERS),
    "acquisition_channel": rng.choice(CHANNELS, N_CUSTOMERS, p=[0.35, 0.25, 0.15, 0.15, 0.10]),
    # A/B test assignment: control = old checkout, variant = new 1-click checkout
    "checkout_variant": rng.choice(["control", "variant"], N_CUSTOMERS, p=[0.5, 0.5]),
})
customers["signup_month"] = pd.to_datetime(customers["signup_date"]).dt.to_period("M").astype(str)

# ---- sessions / funnel events -------------------------------------------
# Each customer can return in multiple months after signup; probability of
# returning decays with age (classic retention curve), and conversion odds
# at each funnel step depend on the checkout_variant (variant converts better).
rows = []
session_id = 1
for _, cust in customers.iterrows():
    signup_dt = pd.Timestamp(cust["signup_date"])
    months_active = (START_DATE + timedelta(days=30 * N_MONTHS) - signup_dt).days // 30
    retention_curve = [0.55, 0.33, 0.22, 0.16, 0.12, 0.09][: max(months_active, 1)]

    for m_idx, p_active in enumerate(retention_curve):
        if m_idx == 0 or rng.random() < p_active:
            n_sessions_this_month = rng.poisson(1.6) + (1 if m_idx == 0 else 0)
            for _ in range(max(n_sessions_this_month, 0)):
                sess_date = signup_dt + timedelta(days=30 * m_idx + int(rng.integers(0, 28)))
                base_p_cart = 0.42
                base_p_checkout = 0.55
                base_p_purchase = 0.62 if cust["checkout_variant"] == "control" else 0.74

                reached = ["view"]
                if rng.random() < base_p_cart:
                    reached.append("add_to_cart")
                    if rng.random() < base_p_checkout:
                        reached.append("checkout")
                        if rng.random() < base_p_purchase:
                            reached.append("purchase")

                for step_order, step in enumerate(reached):
                    rows.append({
                        "session_id": session_id,
                        "customer_id": cust["customer_id"],
                        "event_date": sess_date + timedelta(minutes=step_order * 3),
                        "funnel_step": step,
                        "category": rng.choice(CATEGORIES),
                        "checkout_variant": cust["checkout_variant"],
                    })
                session_id += 1

events = pd.DataFrame(rows)

# ---- orders (only for sessions that reached purchase) --------------------
purchase_events = events[events["funnel_step"] == "purchase"].copy()
purchase_events["order_value"] = np.round(rng.gamma(shape=3.0, scale=550, size=len(purchase_events)), 2)
orders = purchase_events[["session_id", "customer_id", "event_date", "category",
                           "checkout_variant", "order_value"]].rename(columns={"event_date": "order_date"})
orders.insert(0, "order_id", np.arange(1, len(orders) + 1))

# ---- write raw CSVs -------------------------------------------------------
customers.to_csv("data/raw/customers.csv", index=False)
events.to_csv("data/raw/events.csv", index=False)
orders.to_csv("data/raw/orders.csv", index=False)

print(f"customers: {len(customers)} rows")
print(f"events:    {len(events)} rows")
print(f"orders:    {len(orders)} rows")
