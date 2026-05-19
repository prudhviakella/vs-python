"""
fastapi_app/database.py — Database Connection and Queries
===========================================================
Centralises all database access for the FastAPI app.

Uses psycopg2 (synchronous) for simplicity in this module.
In production, switch to psycopg3 async for better FastAPI integration.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from fastapi_app.models import CustomerRecord, ProductRecord, OrderRecord

load_dotenv()
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "datasets"


def get_connection() -> psycopg2.extensions.connection:
    """Create and return a database connection."""
    return psycopg2.connect(
        host    = os.environ.get("DB_HOST", "localhost"),
        port    = int(os.environ.get("DB_PORT", "5432")),
        dbname  = os.environ.get("DB_NAME", "ecommerce"),
        user    = os.environ.get("DB_USER", "postgres"),
        password= os.environ.get("DB_PASSWORD", ""),
    )


def create_all_tables(conn) -> None:
    """Create all e-commerce tables."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY, first_name VARCHAR(50),
                last_name VARCHAR(50), email VARCHAR(100), phone VARCHAR(30),
                address TEXT, city VARCHAR(50), state VARCHAR(2),
                zip_code VARCHAR(10), country VARCHAR(50) DEFAULT 'USA',
                created_at TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY, product_name VARCHAR(200),
                category VARCHAR(100), brand VARCHAR(100),
                price NUMERIC(10,2), stock_quantity INTEGER DEFAULT 0,
                description TEXT, created_at TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY, customer_id INTEGER,
                order_date TIMESTAMP, total_amount NUMERIC(10,2),
                payment_method VARCHAR(50), order_status VARCHAR(20),
                shipping_address TEXT, shipping_city VARCHAR(50),
                shipping_state VARCHAR(50), shipping_zip VARCHAR(10)
            )
        """)
    conn.commit()
    log.info("All tables ready")


def seed_data(conn, limit: int = 100) -> None:
    """Load CSV data into the database tables."""

    def load_csv(path, table, cols, limit):
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            with conn.cursor() as cur:
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    try:
                        cur.execute(sql, tuple(row.get(c) or None for c in cols))
                    except Exception:
                        conn.rollback()
        conn.commit()
        log.info(f"Seeded {table}")

    load_csv(DATA_DIR / "customers.csv", "customers",
             ["customer_id","first_name","last_name","email","phone","address","city","state","zip_code","country","created_at"], limit)
    load_csv(DATA_DIR / "products.csv", "products",
             ["product_id","product_name","category","brand","price","stock_quantity","description","created_at"], limit)
    load_csv(DATA_DIR / "orders.csv", "orders",
             ["order_id","customer_id","order_date","total_amount","payment_method","order_status","shipping_address","shipping_city","shipping_state","shipping_zip"], limit)


def get_customer(conn, customer_id: int) -> Optional[CustomerRecord]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        return CustomerRecord.model_validate(dict(row))
    except Exception as e:
        log.error(f"Invalid customer data: {e}")
        return None


def get_products(conn, category: Optional[str] = None, limit: int = 20) -> list[ProductRecord]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if category:
            cur.execute("SELECT * FROM products WHERE stock_quantity > 0 AND category = %s ORDER BY price LIMIT %s", (category, limit))
        else:
            cur.execute("SELECT * FROM products WHERE stock_quantity > 0 ORDER BY product_name LIMIT %s", (limit,))
        rows = cur.fetchall()
    result = []
    for row in rows:
        try:
            result.append(ProductRecord.model_validate(dict(row)))
        except Exception:
            pass
    return result


def get_order(conn, order_id: int) -> Optional[OrderRecord]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        return OrderRecord.model_validate(dict(row))
    except Exception as e:
        log.error(f"Invalid order data: {e}")
        return None


def get_orders_for_customer(conn, customer_id: int, limit: int = 5) -> list[OrderRecord]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY order_id DESC LIMIT %s", (customer_id, limit))
        rows = cur.fetchall()
    return [OrderRecord.model_validate(dict(r)) for r in rows if r]
