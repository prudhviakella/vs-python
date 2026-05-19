"""
============================================================
Day 04 — File I/O, JSON, String Operations
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. with statement  — open and close files safely
  2. Reading text files  — system prompts from .txt files
  3. Writing files   — saving LLM call logs
  4. json.loads()    — parse LLM JSON response string → dict
  5. json.dumps()    — convert dict → JSON string
  6. .get()          — safe field access on LLM responses
  7. csv.DictReader  — load real e-commerce data
  8. String methods  — .strip(), .lower(), .split(), .join()

CONNECTION TO MODULE 00:
  In Module 00 you wrote system prompts in a text editor.
  Today: Python loads that file at startup and assembles prompts.
  In Module 00 Technique 04 you saw JSON structured output.
  Today: json.loads() turns the LLM's JSON string into a Python dict.

RUN THIS FILE:
  python modules/day04_file_io_json.py
"""

import json
import csv
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data" / "datasets"
PROMPT_DIR = BASE_DIR / "prompts"

print("=" * 60)
print("DAY 04 — File I/O, JSON, String Operations")
print("=" * 60)


# ============================================================
# SECTION 1 — THE with STATEMENT
# ============================================================

"""
WHAT IS THE with STATEMENT?
Opens a resource (file, DB connection, HTTP client) and guarantees
it is CLOSED when the block exits — even if an error occurs inside.

WITHOUT with (risky):
  f = open("file.txt")
  data = f.read()        ← if this raises an error, f is NEVER closed
  f.close()

WITH with (safe):
  with open("file.txt") as f:
      data = f.read()    ← error or not, Python calls f.close() automatically

MODES:
  "r"  → read (default)
  "w"  → write (overwrites existing content)
  "a"  → append (adds to end, creates if missing)

ALWAYS specify encoding="utf-8" — avoids platform differences.

Day 09 introduces async with — the same idea for async resources.
"""

print()
print("─" * 60)
print("SECTION 1 — with statement: reading and writing files")
print("─" * 60)


# ── SIMPLE — write then read a file ──────────────────────────

"""
SIMPLE — write a file, then read it back:
"""
temp_path = BASE_DIR / "temp_demo.txt"

print()
print("Simple — write then read:")

with open(temp_path, "w", encoding="utf-8") as f:
    f.write("Hello from Day 04\n")
    f.write("This is line two\n")

with open(temp_path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"  Written and read back:")
for line in content.splitlines():
    print(f"    {line}")

temp_path.unlink()   # clean up


# ── SHOPSMART — load system prompt from file ─────────────────

"""
SHOPSMART — loading the system prompt from prompts/system_prompt.txt.

Why keep prompts in files instead of hardcoded strings?
  - Non-technical team members can edit prompts without touching code
  - Prompts can be version-controlled independently from code
  - Different prompts for dev/staging/production environments
  - In Day 12 FastAPI loads this ONCE at startup (lifespan)
"""

system_prompt_path = PROMPT_DIR / "system_prompt.txt"

print()
print("ShopSmart — loading system prompt from file:")

try:
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()   # .strip() removes trailing newline
    print(f"  Loaded {len(system_prompt)} characters")
    print(f"  First 80 chars: {system_prompt[:80]}...")
except FileNotFoundError:
    system_prompt = "You are a helpful customer support agent for ShopSmart."
    print(f"  File not found — using default prompt")


# ── SHOPSMART — append to a log file (JSONL format) ──────────

"""
SHOPSMART — logging LLM calls in JSONL format.
JSONL = JSON Lines = one JSON object per line.
"a" mode appends — creates the file if it doesn't exist.
In production: every LLM call is logged for monitoring and cost tracking.
"""

log_path = BASE_DIR / "llm_calls.log"

call_records = [
    {"query": "Where is order #3042?",   "agent": "order_agent",  "tokens": 142},
    {"query": "Do you have a discount?", "agent": "promotions_agent", "tokens": 98},
]

print()
print("ShopSmart — writing JSONL call log:")
with open(log_path, "a", encoding="utf-8") as f:
    for record in call_records:
        line = json.dumps(record)
        f.write(line + "\n")
        print(f"  Logged: {line}")

# Read it back
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"  Log file now has {len(lines)} total lines")
log_path.unlink()   # clean up


# ============================================================
# SECTION 2 — JSON
# ============================================================

"""
WHAT IS JSON?
JSON (JavaScript Object Notation) is a text format for structured data.
Python dicts and JSON look almost identical — intentionally.

Python dict :  {"key": "value", "num": 42, "flag": True, "empty": None}
JSON string :  '{"key": "value", "num": 42, "flag": true, "empty": null}'

Differences:
  Python True/False vs JSON true/false (lowercase)
  Python None       vs JSON null

TWO KEY FUNCTIONS:
  json.loads(string) → parse JSON string → Python dict
  json.dumps(dict)   → Python dict → JSON string

  loads = "load from string"
  dumps = "dump to string"

WHY THIS IS CRITICAL:
  In Module 00 Technique 04 you saw the LLM return JSON like:
    {"category": "TRACK_ORDER", "confidence": "high"}

  That arrives from the API as a STRING — not a dict.
  You MUST call json.loads() before you can access the fields.
"""

print()
print("─" * 60)
print("SECTION 2 — JSON: loads and dumps")
print("─" * 60)


# ── SIMPLE — json.loads() ─────────────────────────────────────

"""
SIMPLE:
"""
raw_json_string = '{"name": "Alice", "age": 25, "active": true}'
parsed          = json.loads(raw_json_string)

print()
print("Simple — json.loads():")
print(f"  Input type  : {type(raw_json_string)}")
print(f"  Parsed type : {type(parsed)}")
print(f"  parsed['name'] = {parsed['name']}")
print(f"  parsed['age']  = {parsed['age']}")


# ── SIMPLE — json.dumps() ─────────────────────────────────────

"""
SIMPLE:
"""
my_dict    = {"model": "gpt-4o", "temperature": 0.2, "stream": False}
json_str   = json.dumps(my_dict)
pretty_str = json.dumps(my_dict, indent=2)

print()
print("Simple — json.dumps():")
print(f"  Compact: {json_str}")
print(f"  Pretty:\n{pretty_str}")


# ── SHOPSMART — parsing LLM JSON response ────────────────────

"""
SHOPSMART — the full LLM response parsing pattern.

In Module 00 Technique 04 the LLM was told to return:
  {"category": "TRACK_ORDER", "confidence": "high", "reason": "..."}

The API returns this as a STRING. Here is how to parse it.
"""

def parse_llm_response(raw: str) -> dict:
    """
    Parse an LLM JSON response string into a Python dict.
    Handles markdown fences that LLMs sometimes add.
    """
    cleaned = raw.strip()

    # LLMs sometimes wrap JSON in markdown fences:
    # ```json
    # {"key": "value"}
    # ```
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]        # remove opening ```json line
        cleaned = cleaned.rsplit("```", 1)[0]       # remove closing ``` line
        cleaned = cleaned.strip()

    return json.loads(cleaned)


print()
print("ShopSmart — parsing LLM JSON responses:")

test_cases = [
    '{"category": "TRACK_ORDER", "confidence": "high"}',
    '```json\n{"category": "BILLING", "confidence": "medium"}\n```',
]

for raw in test_cases:
    result = parse_llm_response(raw)
    print(f"  Input  : {raw[:50]}...")
    print(f"  Parsed : {result}")
    print()


# ── SHOPSMART — safe .get() on parsed response ───────────────

"""
SHOPSMART — always use .get() when reading LLM responses.
LLMs do not always include every field you asked for.

dict["missing_key"]              → KeyError — CRASH
dict.get("missing_key")          → None     — SAFE
dict.get("missing_key", "N/A")   → "N/A"   — SAFE with fallback
"""

incomplete_response = {"category": "BILLING"}   # "reason" field is missing

category   = incomplete_response.get("category",   "UNKNOWN")
confidence = incomplete_response.get("confidence", "low")      # missing → "low"
reason     = incomplete_response.get("reason",     "not given") # missing → "not given"

print()
print("ShopSmart — safe .get() on incomplete LLM response:")
print(f"  category  : {category}")
print(f"  confidence: {confidence}   ← key was missing, default used")
print(f"  reason    : {reason}  ← key was missing, default used")


# ── SHOPSMART — load few-shot examples from JSON ─────────────

"""
SHOPSMART — loading Module 00 Technique 02 examples from a file.
json.load(file_object) reads directly from a file
vs json.loads(string)  which reads from a string.
"""

few_shot_path = PROMPT_DIR / "few_shot_examples.json"
print()
print("ShopSmart — loading few-shot examples from JSON file:")

try:
    with open(few_shot_path, "r", encoding="utf-8") as f:
        data     = json.load(f)    # json.load reads from file object
    examples = data.get("examples", [])
    print(f"  Loaded {len(examples)} examples")
    for ex in examples[:2]:
        print(f"  Input : {ex['input']}")
        print(f"  Output: {ex['output']}")
        print()
except FileNotFoundError:
    print("  few_shot_examples.json not found — check prompts/ folder")


# ============================================================
# SECTION 3 — CSV (loading real ShopSmart data)
# ============================================================

"""
READING CSV WITH csv.DictReader:
csv.DictReader reads each row as a dict, using header row as keys.

IMPORTANT: ALL values from CSV are strings.
If you need int or float — convert manually: int(row["customer_id"])
"""

print()
print("─" * 60)
print("SECTION 3 — csv.DictReader (real data)")
print("─" * 60)


# ── SIMPLE — csv.DictReader ───────────────────────────────────

"""
SIMPLE concept — DictReader turns each CSV row into a dict:
Row:    1001,Danielle,Johnson,john21@example.net
Dict: {"customer_id": "1001", "first_name": "Danielle", ...}
"""

customers_path = DATA_DIR / "customers.csv"
customers      = []

print()
print("ShopSmart — loading customers.csv:")

try:
    with open(customers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)   # reads header row automatically
        for i, row in enumerate(reader):
            if i >= 5:
                break   # only load first 5 for demo
            customers.append({
                "customer_id": int(row["customer_id"]),        # str → int
                "name"       : f"{row['first_name']} {row['last_name']}",
                "email"      : row["email"].lower().strip(),   # normalise
                "city"       : row["city"],
                "state"      : row["state"],
            })

    print(f"  Loaded {len(customers)} customers")
    for c in customers:
        print(f"  {c['customer_id']} | {c['name']:25s} | {c['city']}, {c['state']}")

except FileNotFoundError:
    print("  customers.csv not found — check data/datasets/ folder")


# ============================================================
# SECTION 4 — STRING METHODS
# ============================================================

"""
COMMON STRING METHODS FOR LLM ENGINEERING:

  text.strip()          → remove leading/trailing whitespace
  text.lower()          → convert to lowercase
  text.upper()          → convert to uppercase
  text.replace(a, b)    → replace all occurrences of a with b
  text.split(sep)       → split into list at separator
  sep.join(items)       → join list into string with separator
  text.startswith(s)    → True if text begins with s
  text.endswith(s)      → True if text ends with s
  len(text)             → character count
"""

print()
print("─" * 60)
print("SECTION 4 — String methods")
print("─" * 60)


# ── SIMPLE — basic string methods ────────────────────────────

"""
SIMPLE:
"""
text = "  Hello, World!  "
print()
print("Simple string methods:")
print(f"  original       : '{text}'")
print(f"  .strip()       : '{text.strip()}'")
print(f"  .lower()       : '{text.strip().lower()}'")
print(f"  .upper()       : '{text.strip().upper()}'")
print(f"  .replace('!','.'): '{text.strip().replace('!', '.')}'")
print(f"  .split(', ')   : {text.strip().split(', ')}")
print(f"  '-'.join(list) : {'-'.join(['a', 'b', 'c'])}")


# ── SHOPSMART — cleaning CSV data before prompt injection ────

"""
SHOPSMART — raw product descriptions from CSV often have:
  - Extra whitespace between words
  - Leading/trailing newlines
  - Tabs and other control characters

Clean before injecting into a prompt to avoid wasting tokens.
"""

raw_description = "  Interesting   help   church   successful   effort.  Care   base   know   goal.  "

# .split() with no args splits on ANY whitespace, removes empties
# " ".join() puts it back with single spaces — collapses all gaps
words   = raw_description.split()
cleaned = " ".join(words)

print()
print("ShopSmart — cleaning product description:")
print(f"  Raw    : '{raw_description[:50]}...'")
print(f"  Cleaned: '{cleaned[:50]}...'")

# Truncate for prompt (avoid context overflow)
max_length = 80
if len(cleaned) > max_length:
    truncated = cleaned[:max_length - 3] + "..."
else:
    truncated = cleaned

print(f"  Truncated to {max_length} chars: '{truncated}'")


# ── SHOPSMART — normalise email from CSV ─────────────────────

"""
SHOPSMART — emails in CSV may be inconsistent case.
Always normalise before storing or comparing.
"""
raw_emails = ["JOHN21@EXAMPLE.NET", " Lindsay78@Example.Org ", "user@TEST.COM"]
print()
print("ShopSmart — normalising emails:")
for raw in raw_emails:
    normalised = raw.strip().lower()
    print(f"  '{raw}' → '{normalised}'")


# ── SHOPSMART — building context block for prompt ────────────

"""
SHOPSMART — building the <context> block for a RAG prompt.
In Module 00 Technique 05 (RAG Grounding) the context goes
inside <context> XML tags — here is how Python builds those tags.
"""

def build_product_context(product: dict) -> str:
    """
    Format a product dict as an XML context block for an LLM prompt.
    Matches the <context> tag format from Module 00 Technique 05.
    """
    description = " ".join(product.get("description", "").split())
    if len(description) > 100:
        description = description[:97] + "..."

    return (
        f"<context>\n"
        f"  Product : {product.get('product_name', 'Unknown')}\n"
        f"  Price   : ${float(product.get('price', 0)):.2f}\n"
        f"  In Stock: {product.get('stock_quantity', 0)} units\n"
        f"  Desc    : {description}\n"
        f"</context>"
    )

sample_product = {
    "product_name"  : "Classic Monitor",
    "price"         : "205.21",
    "stock_quantity": "238",
    "description"   : "  High-resolution  27-inch  4K  display.  Perfect  for  professionals.  ",
}

print()
print("ShopSmart — product context block for LLM:")
print(build_product_context(sample_product))


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 04:

1. with open(path, "r") as f: f.read()      ← safe file reading
   with open(path, "a") as f: f.write(...)  ← safe file appending
   "r" read, "w" write (overwrite), "a" append

2. json.loads(string)  → parse JSON string → Python dict
   json.dumps(dict)    → Python dict → JSON string
   json.load(f)        → read JSON from file object

3. dict.get("key", default)  → always safe, never crashes
   Use ALWAYS when reading LLM responses — fields may be missing

4. csv.DictReader reads each CSV row as a dict.
   All values are strings — convert types yourself.

5. String methods:
   .strip()  → remove whitespace
   .lower()  → lowercase for consistent comparisons
   .split()  → break into list
   .join()   → reassemble list into string
   Truncate with: text[:max] + "..."

CONNECTION TO MODULE 00:
  System prompt (## Role/Task/Output/Examples) loaded from .txt
  json.loads() is what happens to every Technique 04 response
  <context> block for RAG built from database data with f-strings

NEXT: Day 05 — Exception Handling + logging
  What happens when the file is missing, JSON is broken,
  or the API call fails — and higher-order functions.
"""

print()
print("=" * 60)
print("Day 04 complete.")
print("Next: python modules/day05_exception_handling_logging.py")
print("=" * 60)

# ── SHOPSMART — os.environ + dotenv ───────────────────────────

"""
SHOPSMART:
load_dotenv() reads the .env file and puts values into os.environ.
Must be called BEFORE any os.environ.get() for .env values.
"""
load_dotenv()   # reads .env file — silent if file does not exist

openai_key = os.environ.get("OPENAI_API_KEY")
db_host    = os.environ.get("DB_HOST", "localhost")
db_port    = os.environ.get("DB_PORT", "5432")
log_level  = os.environ.get("LOG_LEVEL", "INFO")

print()
print("os.environ — ShopSmart (from .env):")

if openai_key:
    masked = openai_key[:4] + "..." + openai_key[-4:]
    print(f"  OPENAI_API_KEY : {masked}  ← loaded from .env")
else:
    print("  OPENAI_API_KEY : not set  ← copy .env.example to .env")

print(f"  DB_HOST        : {db_host}")
print(f"  DB_PORT        : {db_port}")
print(f"  LOG_LEVEL      : {log_level}")

"""
SAFE vs UNSAFE access:

  SAFE:   os.environ.get("KEY")          → returns None if missing
  SAFE:   os.environ.get("KEY", "val")   → returns "val" if missing
  UNSAFE: os.environ["KEY"]              → raises KeyError if missing
                                           crashes with confusing error

Always use .get() — never os.environ["KEY"] on untrusted keys.
"""
print()
print("Safe vs Unsafe access:")
print("  .get('MISSING_KEY')          →", os.environ.get("MISSING_KEY"))
print("  .get('MISSING_KEY', 'default') →", os.environ.get("MISSING_KEY", "default"))


