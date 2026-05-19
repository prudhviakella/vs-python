"""
seed_db.py — Load ecom CSV dataset into local PostgreSQL

Usage:
    pip install psycopg2-binary pandas python-dotenv
    python seed_db.py

Env vars (or .env file):
    POSTGRES_HOST      default: localhost
    POSTGRES_PORT      default: 5432
    POSTGRES_DB        default: ecom
    POSTGRES_USER      default: postgres
    POSTGRES_PASSWORD  (required)
    CSV_DIR            default: ./data  (folder containing the 14 CSVs)
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Connection ─────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "ecom"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


# ── DDL ────────────────────────────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS categories (
    category_id         INTEGER PRIMARY KEY,
    category_name       TEXT    NOT NULL,
    parent_category_id  INTEGER REFERENCES categories(category_id),
    category_level      INTEGER,
    description         TEXT,
    created_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id  INTEGER PRIMARY KEY,
    first_name   TEXT,
    last_name    TEXT,
    email        TEXT,
    phone        TEXT,
    address      TEXT,
    city         TEXT,
    state        TEXT,
    zip_code     TEXT,
    country      TEXT,
    created_at   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_addresses (
    address_id    INTEGER PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(customer_id),
    address_type  TEXT,
    is_default    TEXT,
    address_line1 TEXT,
    address_line2 TEXT,
    city          TEXT,
    state         TEXT,
    zip_code      TEXT,
    country       TEXT,
    phone         TEXT,
    created_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id      INTEGER PRIMARY KEY,
    supplier_name    TEXT,
    contact_person   TEXT,
    email            TEXT,
    phone            TEXT,
    address          TEXT,
    city             TEXT,
    state            TEXT,
    country          TEXT,
    payment_terms    TEXT,
    rating           NUMERIC(3,1),
    created_at       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id     INTEGER PRIMARY KEY,
    warehouse_name   TEXT,
    address          TEXT,
    city             TEXT,
    state            TEXT,
    zip_code         TEXT,
    country          TEXT,
    phone            TEXT,
    email            TEXT,
    capacity_sqft    INTEGER,
    manager_name     TEXT,
    operating_since  DATE
);

CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    brand           TEXT,
    price           NUMERIC(10,2),
    stock_quantity  INTEGER,
    description     TEXT,
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promotions (
    promotion_id        INTEGER PRIMARY KEY,
    promotion_name      TEXT,
    promotion_type      TEXT,
    discount_percent    NUMERIC(5,2),
    discount_amount     NUMERIC(10,2),
    start_date          TIMESTAMP,
    end_date            TIMESTAMP,
    promo_code          TEXT,
    min_purchase_amount NUMERIC(10,2),
    max_discount        NUMERIC(10,2),
    status              TEXT,
    usage_limit         INTEGER,
    times_used          INTEGER
);

CREATE TABLE IF NOT EXISTS orders (
    order_id          INTEGER PRIMARY KEY,
    customer_id       INTEGER REFERENCES customers(customer_id),
    order_date        TIMESTAMP,
    total_amount      NUMERIC(10,2),
    payment_method    TEXT,
    order_status      TEXT,
    shipping_address  TEXT,
    shipping_city     TEXT,
    shipping_state    TEXT,
    shipping_zip      TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER REFERENCES orders(order_id),
    product_id     INTEGER REFERENCES products(product_id),
    quantity       INTEGER,
    unit_price     NUMERIC(10,2),
    total_price    NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id          INTEGER PRIMARY KEY,
    product_id         INTEGER REFERENCES products(product_id),
    customer_id        INTEGER REFERENCES customers(customer_id),
    rating             INTEGER,
    review_title       TEXT,
    review_text        TEXT,
    review_date        TIMESTAMP,
    verified_purchase  TEXT,
    helpful_votes      INTEGER
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id         INTEGER PRIMARY KEY,
    order_id            INTEGER REFERENCES orders(order_id),
    warehouse_id        INTEGER REFERENCES warehouses(warehouse_id),
    carrier             TEXT,
    tracking_number     TEXT,
    ship_date           TIMESTAMP,
    estimated_delivery  TIMESTAMP,
    actual_delivery     TIMESTAMP,
    shipping_cost       NUMERIC(8,2),
    weight_lbs          NUMERIC(6,2),
    status              TEXT
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    transaction_id      INTEGER PRIMARY KEY,
    order_id            INTEGER REFERENCES orders(order_id),
    payment_method      TEXT,
    payment_provider    TEXT,
    transaction_date    TIMESTAMP,
    amount              NUMERIC(10,2),
    currency            TEXT,
    status              TEXT,
    card_last_four      TEXT,
    authorization_code  TEXT,
    processing_fee      NUMERIC(8,2)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id        INTEGER PRIMARY KEY,
    product_id          INTEGER REFERENCES products(product_id),
    warehouse_id        INTEGER REFERENCES warehouses(warehouse_id),
    quantity_available  INTEGER,
    quantity_reserved   INTEGER,
    reorder_point       INTEGER,
    last_restock_date   TIMESTAMP,
    last_stock_check    TIMESTAMP,
    bin_location        TEXT
);

CREATE TABLE IF NOT EXISTS product_suppliers (
    product_supplier_id     INTEGER PRIMARY KEY,
    product_id              INTEGER REFERENCES products(product_id),
    supplier_id             INTEGER REFERENCES suppliers(supplier_id),
    cost_price              NUMERIC(10,2),
    lead_time_days          INTEGER,
    minimum_order_quantity  INTEGER,
    is_primary_supplier     TEXT,
    last_order_date         TIMESTAMP
);
"""

# Indexes for common NLQ query patterns
INDEXES = """
CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_date        ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order  ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_prod   ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product    ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_customer   ON reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product  ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_wh       ON inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_shipments_order    ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_order      ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_prod_sup_product   ON product_suppliers(product_id);
CREATE INDEX IF NOT EXISTS idx_customer_addr_cust ON customer_addresses(customer_id);
"""


# ── Loader ─────────────────────────────────────────────────────────────────────
def _null(val):
    """Convert NaN / empty string to None, and float integers like '1.0' → '1'."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    # pandas emits "1.0" for nullable integer columns — strip the decimal
    if isinstance(val, str):
        try:
            f = float(val)
            if f == int(f):
                return str(int(f))
        except (ValueError, OverflowError):
            pass
    return val


def load_csv(cur, csv_path: Path, table: str):
    df = pd.read_csv(csv_path, dtype=str)          # read everything as str first
    df = df.where(pd.notnull(df), None)            # replace NaN → None
    cols = list(df.columns)
    col_sql = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    insert_sql = (
        f'INSERT INTO {table} ({col_sql}) VALUES ({placeholders}) '
        f'ON CONFLICT DO NOTHING'
    )
    rows = [tuple(_null(v) for v in row) for row in df.itertuples(index=False, name=None)]
    execute_values(
        cur,
        f'INSERT INTO {table} ({col_sql}) VALUES %s ON CONFLICT DO NOTHING',
        rows,
    )
    log.info("  %-30s  %d rows", table, len(rows))


# Load order matters — respect FK dependencies
LOAD_ORDER = [
    ("categories.csv",            "categories"),
    ("customers.csv",             "customers"),
    ("customer_addresses.csv",    "customer_addresses"),
    ("suppliers.csv",             "suppliers"),
    ("warehouses.csv",            "warehouses"),
    ("products.csv",              "products"),
    ("promotions.csv",            "promotions"),
    ("orders.csv",                "orders"),
    ("order_items.csv",           "order_items"),
    ("reviews.csv",               "reviews"),
    ("shipments.csv",             "shipments"),
    ("payment_transactions.csv",  "payment_transactions"),
    ("inventory.csv",             "inventory"),
    ("product_suppliers.csv",     "product_suppliers"),
]


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    csv_dir = Path(os.getenv("CSV_DIR", "./data"))
    if not csv_dir.exists():
        log.error("CSV_DIR '%s' not found. Set CSV_DIR env var to point at the data folder.", csv_dir)
        sys.exit(1)

    log.info("Connecting to Postgres...")
    conn = get_conn()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            log.info("Creating schema...")
            cur.execute(DDL)
            conn.commit()

            log.info("Loading data...")
            for filename, table in LOAD_ORDER:
                path = csv_dir / filename
                if not path.exists():
                    log.warning("  SKIP %s — file not found", filename)
                    continue
                load_csv(cur, path, table)

            conn.commit()

            log.info("Creating indexes...")
            cur.execute(INDEXES)
            conn.commit()

        log.info("Done! All tables loaded successfully.")

    except Exception as e:
        conn.rollback()
        log.error("Seed failed: %s", e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()