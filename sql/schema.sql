-- FunnelIQ schema (SQLite)

DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id        INTEGER PRIMARY KEY,
    signup_date        TEXT NOT NULL,
    signup_month       TEXT NOT NULL,
    city                TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    checkout_variant    TEXT NOT NULL CHECK (checkout_variant IN ('control', 'variant'))
);

DROP TABLE IF EXISTS events;
CREATE TABLE events (
    session_id       INTEGER NOT NULL,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    event_date       TEXT NOT NULL,
    funnel_step      TEXT NOT NULL CHECK (funnel_step IN ('view','add_to_cart','checkout','purchase')),
    category         TEXT NOT NULL,
    checkout_variant TEXT NOT NULL
);

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id         INTEGER PRIMARY KEY,
    session_id       INTEGER NOT NULL,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date       TEXT NOT NULL,
    category         TEXT NOT NULL,
    checkout_variant TEXT NOT NULL,
    order_value      REAL NOT NULL
);

CREATE INDEX idx_events_customer ON events(customer_id);
CREATE INDEX idx_events_step ON events(funnel_step);
CREATE INDEX idx_orders_customer ON orders(customer_id);
