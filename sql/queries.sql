-- FunnelIQ: SQL analysis queries (SQLite)

-- 1. Overall funnel: distinct customers reaching each step
SELECT
    funnel_step,
    COUNT(DISTINCT customer_id) AS customers_reached
FROM events
GROUP BY funnel_step
ORDER BY CASE funnel_step
    WHEN 'view' THEN 1 WHEN 'add_to_cart' THEN 2
    WHEN 'checkout' THEN 3 WHEN 'purchase' THEN 4 END;

-- 2. Funnel split by checkout A/B variant (control vs variant)
SELECT
    checkout_variant,
    funnel_step,
    COUNT(DISTINCT customer_id) AS customers_reached
FROM events
GROUP BY checkout_variant, funnel_step
ORDER BY checkout_variant, CASE funnel_step
    WHEN 'view' THEN 1 WHEN 'add_to_cart' THEN 2
    WHEN 'checkout' THEN 3 WHEN 'purchase' THEN 4 END;

-- 3. Revenue and average order value by category
SELECT
    category,
    COUNT(*) AS orders,
    ROUND(SUM(order_value), 2) AS total_revenue,
    ROUND(AVG(order_value), 2) AS avg_order_value
FROM orders
GROUP BY category
ORDER BY total_revenue DESC;

-- 4. Monthly new-customer acquisition by channel
SELECT
    signup_month,
    acquisition_channel,
    COUNT(*) AS new_customers
FROM customers
GROUP BY signup_month, acquisition_channel
ORDER BY signup_month, new_customers DESC;

-- 5. Monthly cohort retention: for each signup cohort, count distinct
--    customers active in each subsequent calendar month (months_since_signup)
WITH cohort AS (
    SELECT customer_id, signup_month
    FROM customers
),
activity AS (
    SELECT customer_id, strftime('%Y-%m', event_date) AS activity_month
    FROM events
    GROUP BY customer_id, activity_month
)
SELECT
    c.signup_month AS cohort_month,
    (
        (CAST(substr(a.activity_month, 1, 4) AS INTEGER) - CAST(substr(c.signup_month, 1, 4) AS INTEGER)) * 12
        + (CAST(substr(a.activity_month, 6, 2) AS INTEGER) - CAST(substr(c.signup_month, 6, 2) AS INTEGER))
    ) AS months_since_signup,
    COUNT(DISTINCT a.customer_id) AS active_customers
FROM cohort c
JOIN activity a ON a.customer_id = c.customer_id
GROUP BY cohort_month, months_since_signup
ORDER BY cohort_month, months_since_signup;
