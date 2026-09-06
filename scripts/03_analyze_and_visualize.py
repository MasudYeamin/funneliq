"""
FunnelIQ - analysis + visualization
Computes funnel conversion, monthly cohort retention, and an A/B test read-out
(two-proportion z-test) on the checkout_variant experiment, using pandas/numpy/
scipy/statsmodels. Saves processed CSVs and seaborn charts.
"""
import sqlite3
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportions_ztest

sns.set_theme(style="whitegrid")
conn = sqlite3.connect("funneliq.db")

customers = pd.read_sql("SELECT * FROM customers", conn)
events = pd.read_sql("SELECT * FROM events", conn)
orders = pd.read_sql("SELECT * FROM orders", conn)

STEP_ORDER = ["view", "add_to_cart", "checkout", "purchase"]

# ---------------------------------------------------------------- funnel ---
funnel = (
    events.groupby("funnel_step")["customer_id"].nunique()
    .reindex(STEP_ORDER)
    .rename("customers_reached")
    .to_frame()
)
funnel["conversion_from_prev_%"] = np.round(
    funnel["customers_reached"] / funnel["customers_reached"].shift(1) * 100, 1
)
funnel["conversion_from_start_%"] = np.round(
    funnel["customers_reached"] / funnel["customers_reached"].iloc[0] * 100, 1
)
funnel.to_csv("data/processed/funnel_summary.csv")
print("Funnel summary:\n", funnel, "\n")

funnel_by_variant = (
    events.groupby(["checkout_variant", "funnel_step"])["customer_id"].nunique()
    .reindex(pd.MultiIndex.from_product([["control", "variant"], STEP_ORDER]))
    .rename("customers_reached").reset_index()
    .rename(columns={"level_0": "checkout_variant", "level_1": "funnel_step"})
)
funnel_by_variant.to_csv("data/processed/funnel_by_variant.csv", index=False)

# --------------------------------------------------------------- cohorts ---
events["event_date"] = pd.to_datetime(events["event_date"])
events["activity_month"] = events["event_date"].dt.to_period("M")
customers_p = customers.copy()
customers_p["signup_period"] = pd.to_datetime(customers_p["signup_date"]).dt.to_period("M")

activity = events[["customer_id", "activity_month"]].drop_duplicates()
merged = activity.merge(customers_p[["customer_id", "signup_period"]], on="customer_id")
merged["months_since_signup"] = (
    (merged["activity_month"].dt.year - merged["signup_period"].dt.year) * 12
    + (merged["activity_month"].dt.month - merged["signup_period"].dt.month)
)

cohort_sizes = customers_p.groupby("signup_period")["customer_id"].nunique()
cohort_counts = (
    merged.groupby(["signup_period", "months_since_signup"])["customer_id"]
    .nunique().unstack(fill_value=0)
)
retention_pct = cohort_counts.div(cohort_sizes, axis=0).mul(100).round(1)
retention_pct.index = retention_pct.index.astype(str)
retention_pct.to_csv("data/processed/retention_cohort.csv")
print("Retention cohort (%):\n", retention_pct, "\n")

# -------------------------------------------------------------- A/B test ---
purchasers = events[events["funnel_step"] == "purchase"][["customer_id", "checkout_variant"]].drop_duplicates()
variant_totals = customers.groupby("checkout_variant")["customer_id"].nunique()
variant_purchasers = purchasers.groupby("checkout_variant")["customer_id"].nunique()

counts = np.array([variant_purchasers["variant"], variant_purchasers["control"]])
nobs = np.array([variant_totals["variant"], variant_totals["control"]])
z_stat, p_value = proportions_ztest(counts, nobs)

rate_control = variant_purchasers["control"] / variant_totals["control"]
rate_variant = variant_purchasers["variant"] / variant_totals["variant"]
lift_pct = (rate_variant - rate_control) / rate_control * 100

ab_result = pd.DataFrame([{
    "control_customers": int(variant_totals["control"]),
    "control_purchasers": int(variant_purchasers["control"]),
    "control_conversion_%": round(rate_control * 100, 2),
    "variant_customers": int(variant_totals["variant"]),
    "variant_purchasers": int(variant_purchasers["variant"]),
    "variant_conversion_%": round(rate_variant * 100, 2),
    "lift_%": round(lift_pct, 2),
    "z_stat": round(z_stat, 3),
    "p_value": round(p_value, 5),
    "significant_at_0.05": bool(p_value < 0.05),
}])
ab_result.to_csv("data/processed/ab_test_results.csv", index=False)
print("A/B test result:\n", ab_result.T, "\n")

# ------------------------------------------------------------- charts ------
fig, ax = plt.subplots(figsize=(7, 4.5))
sns.barplot(x=funnel.index, y=funnel["customers_reached"], ax=ax, hue=funnel.index, palette="Blues_d", legend=False)
ax.set_title("FunnelIQ - Overall Conversion Funnel")
ax.set_xlabel("Funnel step")
ax.set_ylabel("Distinct customers")
for i, v in enumerate(funnel["customers_reached"]):
    ax.text(i, v + max(funnel["customers_reached"]) * 0.01, str(v), ha="center")
plt.tight_layout()
plt.savefig("visuals/funnel_overall.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(8, 5))
pivot_variant = funnel_by_variant.pivot(index="funnel_step", columns="checkout_variant", values="customers_reached").reindex(STEP_ORDER)
pivot_variant.plot(kind="bar", ax=ax, color=["#4C72B0", "#DD8452"])
ax.set_title("FunnelIQ - Funnel by Checkout Variant (A/B Test)")
ax.set_ylabel("Distinct customers")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("visuals/funnel_by_variant.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(retention_pct, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "% retained"}, ax=ax)
ax.set_title("FunnelIQ - Monthly Cohort Retention (%)")
ax.set_xlabel("Months since signup")
ax.set_ylabel("Signup cohort")
plt.tight_layout()
plt.savefig("visuals/retention_heatmap.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(7, 4.5))
sns.histplot(orders["order_value"], bins=30, kde=True, ax=ax, color="#55A868")
ax.set_title("FunnelIQ - Order Value Distribution")
ax.set_xlabel("Order value (INR)")
plt.tight_layout()
plt.savefig("visuals/order_value_distribution.png", dpi=150)
plt.close()

print("Charts saved to visuals/")
conn.close()
