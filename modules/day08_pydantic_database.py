"""
============================================================
Day 08 — Pydantic v2 + Database Basics
============================================================
Module 01: Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. Why Pydantic? — validation beyond type hints
  2. BaseModel + Field — define and constrain a data model
  3. model_validate_json() — parse AND validate LLM JSON in one call
  4. TypedDict vs BaseModel — when to use which
  5. psycopg2 — connect to Postgres, create tables, insert and query

WHY THIS MATTERS:
  - LLM responses are strings. Pydantic parses AND validates them.
    If the LLM omits a required field or returns a wrong value,
    Pydantic raises ValidationError immediately — your service
    never silently propagates bad data.
  - In Day 12 FastAPI will use these same models for HTTP request
    and response validation.
  - The database holds your e-commerce data; LLM tools query it.

NOTE: the database section requires PostgreSQL running locally.
      Set DB_* variables in .env. The Pydantic section always works.

RUN THIS FILE:
  python modules/day08_pydantic_database.py
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "datasets"

print("=" * 60)
print("DAY 08 — Pydantic v2 + Database Basics")
print("=" * 60)


# ============================================================
# SECTION 1 — WHY PYDANTIC?
# ============================================================

"""
THE PROBLEM WITH TYPE HINTS ALONE:

  max_tokens: int = "one thousand"   ← Python allows this. No error.
  email: str = 12345                 ← Python allows this. No error.

Type hints are documentation for humans and IDEs.
Python DOES NOT enforce them at runtime.

THE PROBLEM WITH json.loads() ALONE:

  parsed = json.loads('{"rating": "five", "category": "UNKNOWN"}')
  parsed["rating"]   → "five" (string, not int)
  parsed["category"] → "UNKNOWN" (not in allowed values)

json.loads() parses the JSON — it does NOT validate the values.

PYDANTIC SOLVES BOTH PROBLEMS:
  - Validates types at runtime (raises ValidationError on failure)
  - Converts compatible types automatically ("5" → 5)
  - Enforces constraints (min_length, ge, le, Literal allowed values)
  - model_validate_json() does json.loads() + validation in one call

BRIDGE FROM MODULE 00 (Technique 04 — Structured Output):
  In your system prompt you write:
    Return JSON: {"category": "TRACK_ORDER|BILLING|OTHER", "confidence": "high|medium|low"}

  That schema BECOMES the Pydantic model below.
  Pydantic validates that the LLM followed your instructions.
"""

print()
print("─" * 60)
print("SECTION 1 — Pydantic basics")
print("─" * 60)


# ── BaseModel + Field ─────────────────────────────────────────

"""
DEFINING A MODEL:

  class MyModel(BaseModel):
      field_name: type = Field(constraint, description="...")

COMMON Field() CONSTRAINTS:
  min_length=N   → string must be at least N characters
  max_length=N   → string must be at most N characters
  ge=N           → number must be >= N   (greater than or equal)
  le=N           → number must be <= N   (less than or equal)
  gt=N           → number must be > N    (strictly greater than)

Literal["A", "B", "C"] restricts the value to one of the listed options.
If the LLM returns "D", Pydantic raises ValidationError.
"""

class TriageOutput(BaseModel):
    """
    Pydantic model for the LLM's triage classification.

    This is the Python mirror of the JSON schema in your system prompt.
    Every field here must match a field the LLM is told to return.
    """

    # Literal restricts to specific allowed values
    # If the LLM returns "URGENT" instead of one of these → ValidationError
    category: Literal["TRACK_ORDER", "BILLING", "RETURNS", "PRODUCT", "OTHER"]

    confidence: Literal["high", "medium", "low"]

    # Field(min_length=5) → the reason must be at least 5 characters
    reason: str = Field(min_length=5, description="One sentence explaining the classification")

    # model_config: extra settings for the model
    model_config = {"str_strip_whitespace": True}   # auto-strip whitespace from str fields


class CustomerRecord(BaseModel):
    """Validated customer record — used for both CSV loading and DB results."""

    customer_id: int   = Field(gt=0, description="Must be a positive integer")
    first_name : str   = Field(min_length=1, max_length=50)
    last_name  : str   = Field(min_length=1, max_length=50)
    email      : str
    city       : Optional[str] = None   # Optional means the field can be None
    state      : Optional[str] = None
    country    : str = "USA"

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        """Normalise email to lowercase when the model is created."""
        return value.lower().strip()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class ProductRecord(BaseModel):
    """Validated product record from the products table."""

    product_id    : int   = Field(gt=0)
    product_name  : str
    category      : Optional[str] = None
    brand         : Optional[str] = None
    price         : float = Field(ge=0)
    stock_quantity: int   = Field(ge=0, default=0)
    description   : Optional[str] = None

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def price_str(self) -> str:
        return f"${self.price:.2f}"


# ── model_validate_json() — parse + validate in one call ─────

"""
model_validate_json(raw_string)
  = json.loads(raw_string) + Pydantic validation
  = parse the JSON AND validate all fields in one step

model_validate(python_dict)
  = validate a Python dict that is already parsed

model_validate_json is the main entry point for LLM responses.
"""

print()
print("model_validate_json() — parsing LLM responses:")

test_cases = [
    # Valid response
    '{"category": "TRACK_ORDER", "confidence": "high", "reason": "Customer asked about order location"}',
    # Valid — with markdown fences (we strip them first)
    '```json\n{"category": "BILLING", "confidence": "medium", "reason": "Invoice question received"}\n```',
    # Invalid category
    '{"category": "URGENT", "confidence": "high", "reason": "Invalid category value used"}',
    # Missing required field
    '{"category": "PRODUCT", "confidence": "low"}',
]

for raw in test_cases:
    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = TriageOutput.model_validate_json(cleaned)
        log.info(f"VALID   category={result.category}, confidence={result.confidence}")
    except ValidationError as e:
        # e.errors() gives field-level detail — much more useful than a generic crash
        error_summary = "; ".join(
            f"{err['loc'][0]}: {err['msg']}"
            for err in e.errors()
        )
        log.error(f"INVALID  {error_summary}")


# ── model_validate() — from a Python dict ────────────────────

print()
print("model_validate() — from a Python dict (e.g. a database row):")

customer_data = {
    "customer_id": 1001,
    "first_name" : "Danielle",
    "last_name"  : "Johnson",
    "email"      : "JOHN21@EXAMPLE.NET",   # uppercase — will be normalised
    "city"       : "Port Matthew",
    "state"      : "CO",
}

customer = CustomerRecord.model_validate(customer_data)
log.info(f"Customer: {customer.full_name}, email={customer.email}")

# model_dump() — convert back to a plain Python dict
print(f"  model_dump(): {customer.model_dump()}")


# ============================================================
# SECTION 2 — TypedDict vs BaseModel
# ============================================================

"""
TypedDict vs BaseModel — which one to use?

TypedDict:
  - Type HINTS only — Python does NOT validate at runtime
  - Zero overhead (just a dict at runtime)
  - Required by LangChain for agent context (context_schema)

BaseModel:
  - Validates AND converts at runtime
  - Raises ValidationError on bad data
  - Required by FastAPI for HTTP request/response models

RULE:
  Use TypedDict  → when LangChain requires it (agent context)
  Use BaseModel  → when you receive untrusted data (LLM output, HTTP requests)

In Day 12 FastAPI automatically uses Pydantic models to validate
incoming HTTP requests and serialise outgoing responses.
"""

from typing import TypedDict

class AgentContext(TypedDict, total=False):
    """
    Per-request context passed to LangChain agents.

    MUST be TypedDict — LangChain requires it for context_schema.
    total=False means all keys are optional.

    Usage:
      context = {"user_id": "user_123", "session_id": "sess_456"}
      agent.astream_events(input, context=context)
    """
    user_id   : str
    session_id: str
    domain    : str

print()
print("─" * 60)
print("SECTION 2 — TypedDict vs BaseModel")
print("─" * 60)
print()
print("  TypedDict — hints only, no runtime validation:")

ctx: AgentContext = {"user_id": "user_123", "session_id": "sess_abc", "domain": "ecommerce"}
print(f"  context = {ctx}")
print(f"  type    = {type(ctx)}   ← it's just a dict at runtime")

print()
print("  BaseModel — validated at runtime:")
try:
    bad_customer = CustomerRecord.model_validate({"customer_id": -1, "first_name": "", "last_name": "X", "email": "x@y.com"})
except ValidationError as e:
    print(f"  ValidationError caught: {e.errors()[0]['msg']} on field '{e.errors()[0]['loc'][0]}'")


# ============================================================
# SECTION 3 — DATABASE WITH psycopg2
# ============================================================

"""
WHAT IS psycopg2?
psycopg2 is the most widely used Python library for PostgreSQL.

PATTERN:
  conn   = psycopg2.connect(...)   connect to the database
  cursor = conn.cursor()           create a cursor to run SQL
  cursor.execute("SQL", values)    run a parameterised query
  conn.commit()                    save the changes
  conn.close()                     close the connection

ALWAYS use parameterised queries (%s placeholders):
  cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
  ← SAFE: psycopg2 escapes the value

NEVER do string formatting:
  cursor.execute(f"SELECT * FROM customers WHERE id = {customer_id}")
  ← DANGEROUS: SQL injection attack possible

The with statement works for connections and cursors too.
"""

print()
print("─" * 60)
print("SECTION 3 — Database with psycopg2")
print("─" * 60)

try:
    import psycopg2
    import psycopg2.extras   # for RealDictCursor

    db_config = {
        "host"    : os.environ.get("DB_HOST", "localhost"),
        "port"    : int(os.environ.get("DB_PORT", "5432")),
        "dbname"  : os.environ.get("DB_NAME", "ecommerce"),
        "user"    : os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }

    print()
    print(f"Connecting to {db_config['host']}:{db_config['port']}/{db_config['dbname']}...")
    conn = psycopg2.connect(**db_config)
    log.info("Connected to database")

    # Create tables
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                first_name  VARCHAR(50),
                last_name   VARCHAR(50),
                email       VARCHAR(100),
                city        VARCHAR(50),
                state       VARCHAR(2),
                country     VARCHAR(50) DEFAULT 'USA',
                created_at  TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id     INTEGER PRIMARY KEY,
                product_name   VARCHAR(200),
                category       VARCHAR(100),
                brand          VARCHAR(100),
                price          NUMERIC(10,2),
                stock_quantity INTEGER DEFAULT 0,
                description    TEXT,
                created_at     TIMESTAMP
            )
        """)
    conn.commit()
    log.info("Tables ready")

    # Load customers from CSV
    customers_path = DATA_DIR / "customers.csv"
    rows_inserted  = 0

    with open(customers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with conn.cursor() as cur:
            for i, row in enumerate(reader):
                if i >= 50:
                    break
                try:
                    cur.execute(
                        """INSERT INTO customers
                           (customer_id, first_name, last_name, email, city, state, country, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT DO NOTHING""",
                        (row["customer_id"], row["first_name"], row["last_name"],
                         row["email"], row["city"], row["state"],
                         row.get("country", "USA"), row.get("created_at"))
                    )
                    rows_inserted += 1
                except Exception:
                    conn.rollback()
    conn.commit()
    log.info(f"Inserted {rows_inserted} customers")

    # Query using RealDictCursor (returns rows as dicts, not tuples)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM customers WHERE customer_id = %s",
            (1001,)   # parameterised — ALWAYS use %s, never f-strings in SQL
        )
        row = cur.fetchone()

    if row:
        # Validate through Pydantic — catches any bad data in the DB
        customer = CustomerRecord.model_validate(dict(row))
        log.info(f"Customer 1001: {customer.full_name} | {customer.email}")

    conn.close()
    log.info("Connection closed")

except Exception as e:
    print()
    print(f"  Database not available: {e}")
    print("  (Expected if PostgreSQL is not running)")
    print("  Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in .env")
    print()
    print("  Pydantic section above always works without a database.")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS:

1. Pydantic validates data at runtime.
   Type hints alone do not.

2. class MyModel(BaseModel):
       field: Literal["A","B"] = Field(min_length=5)
   → restricts values, enforces constraints, raises ValidationError

3. model_validate_json(string) = json.loads + validation in one call.
   model_validate(dict)        = validate an already-parsed dict.

4. TypedDict → for LangChain agent context (hints only, no validation)
   BaseModel → for LLM responses and FastAPI endpoints (validates everything)

5. psycopg2 pattern:
   conn → cursor → cur.execute(sql, (values,)) → conn.commit()
   ALWAYS parameterise: %s placeholders, never f-strings in SQL.

NEXT: Day 09 — Async Fundamentals
  (why async matters for LLM services, event loop, await)
"""

print()
print("=" * 60)
print("Day 08 complete. Run: python modules/day09_async_fundamentals.py")
print("=" * 60)
