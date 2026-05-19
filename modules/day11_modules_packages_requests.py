"""
============================================================
Day 11 — Modules, Packages, and the requests Library
============================================================
Module 01: Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  PART A — Modules vs Packages
    1. What is a module?    (a single .py file)
    2. What is a package?   (a folder with __init__.py)
    3. Why __init__.py exists
    4. Absolute vs relative imports
    5. How this project is structured

  PART B — the requests library (synchronous HTTP client)
    6. GET requests with query parameters
    7. POST requests with JSON body
    8. Handling responses and errors
    9. requests vs httpx — which to use when

WHY THIS MATTERS:
  - Every LLM API call is an HTTP POST request
  - Understanding imports lets you read and write LangChain code
  - requests is the simplest way to call any API from a script
  - httpx (async, Day 09) is what you use inside FastAPI endpoints

RUN THIS FILE:
  python modules/day11_modules_packages_requests.py
"""

import json
import logging
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

print("=" * 60)
print("DAY 11 — Modules, Packages, requests")
print("=" * 60)


# ============================================================
# PART A — MODULE vs PACKAGE
# ============================================================

"""
WHAT IS A MODULE?
A module is a single .py file.

  day01_setup_variables.py   → a module
  json                       → a built-in module (part of Python stdlib)
  requests                   → a third-party module (pip install requests)

You import a module with:
  import json                     → use as json.loads()
  from json import loads          → use as loads()
  from json import loads, dumps   → import multiple names
  import json as j                → alias: use as j.loads()
"""

print()
print("─" * 60)
print("PART A — Module vs Package")
print("─" * 60)

print()
print("This file is a module: day11_modules_packages_requests.py")
print(f"  __name__  = {__name__}")     # __main__ when run directly
print(f"  __file__  = {__file__}")     # absolute path of this file


"""
WHAT IS A PACKAGE?
A package is a FOLDER that contains:
  1. An __init__.py file     (makes the folder a package)
  2. One or more .py files   (modules inside the package)

The folder name becomes the package name.

EXAMPLE — the fastapi_app/ folder in this project:

  fastapi_app/              ← PACKAGE (has __init__.py)
  ├── __init__.py           ← makes this folder a package
  ├── main.py               ← module: FastAPI entry point
  ├── models.py             ← module: Pydantic models
  ├── database.py           ← module: DB connection
  └── routers/              ← SUB-PACKAGE (has its own __init__.py)
      ├── __init__.py
      ├── customers.py
      └── products.py

A sub-package is a package inside a package.
"""

print()
print("Project structure:")
print("""
  module01/
  ├── modules/              ← NOT a package (no __init__.py)
  │   ├── day01_setup_variables.py
  │   ├── day11_modules_packages_requests.py
  │   └── ...
  │
  ├── fastapi_app/          ← PACKAGE (__init__.py present)
  │   ├── __init__.py
  │   ├── main.py
  │   ├── models.py
  │   ├── database.py
  │   └── routers/          ← SUB-PACKAGE
  │       ├── __init__.py
  │       ├── customers.py
  │       └── products.py
  │
  └── data/
      ├── datasets/
      └── knowledge_base/
""")


"""
WHY DOES __init__.py EXIST?
__init__.py tells Python "this folder is a package, not just a directory."
It runs automatically the first time the package is imported.

THREE COMMON USES:

1. EMPTY — just marks the folder as a package (most common)
   fastapi_app/routers/__init__.py  (empty file)

2. RE-EXPORT — expose selected names so imports are shorter
   # In fastapi_app/__init__.py:
   from .models import CustomerRecord, ProductRecord

   # Now callers can write:
   from fastapi_app import CustomerRecord
   # Instead of:
   from fastapi_app.models import CustomerRecord

3. INITIALISE — set up shared resources (use sparingly)
   # In fastapi_app/__init__.py:
   import logging
   log = logging.getLogger(__name__)
"""

print()
print("__init__.py in this project:")
init_path = Path(__file__).parent.parent / "fastapi_app" / "__init__.py"
if init_path.exists():
    content = init_path.read_text()
    print(f"  fastapi_app/__init__.py ({len(content)} chars)")
    print(f"  First 3 lines: {content.strip().splitlines()[0]}")
else:
    print("  fastapi_app/__init__.py not found")


"""
ABSOLUTE vs RELATIVE IMPORTS:

ABSOLUTE — starts from the project root (most readable):
  from fastapi_app.models import CustomerRecord
  from fastapi_app.routers import customers

RELATIVE — starts from the current module's location:
  from .models import CustomerRecord       (. = same package)
  from ..database import get_connection   (.. = parent package)

WHEN TO USE WHICH:
  Absolute imports → in application code (scripts, main.py)
  Relative imports → inside packages (to avoid circular imports)

FastAPI router files typically use relative imports:
  # In fastapi_app/routers/customers.py:
  from ..models import CustomerRecord   ← goes up to fastapi_app/, then imports
"""

print()
print("Import syntax examples:")
print("  import json                           → json.loads()")
print("  from json import loads                → loads()")
print("  from fastapi_app.models import ...    → absolute import")
print("  from .models import ...               → relative import (inside package)")


# ============================================================
# PART B — requests LIBRARY
# ============================================================

"""
WHAT IS requests?
requests is a Python library for making HTTP calls (GET, POST, etc.)

  pip install requests

EVERY LLM API CALL IS AN HTTP POST REQUEST.
When you call openai.chat.completions.create(...), it sends an HTTP POST.
requests lets you make those calls directly — no SDK needed.

requests vs httpx:
┌──────────────────┬──────────────────────────────────────────┐
│ requests         │ Synchronous — blocks while waiting       │
│                  │ Simple scripts, CLI tools, notebooks      │
│                  │ Cannot be used inside async functions     │
├──────────────────┼──────────────────────────────────────────┤
│ httpx (async)    │ Asynchronous — yields to the event loop  │
│                  │ FastAPI endpoints, async agents           │
│                  │ Must be used inside async def functions   │
└──────────────────┴──────────────────────────────────────────┘

Rule: inside `async def` → use httpx.
      everywhere else    → requests is fine.
"""

print()
print("─" * 60)
print("PART B — requests library")
print("─" * 60)


# ── GET request ───────────────────────────────────────────────

"""
GET REQUESTS — retrieve data. Parameters go in the URL.

  requests.get(url, params={...}, timeout=10)

params={"key": "value"} is automatically URL-encoded:
  → https://api.example.com/todos?userId=1&_limit=2

ALWAYS set timeout= to prevent hanging forever.

response.raise_for_status() raises HTTPError for 4xx and 5xx responses.
response.json() parses the JSON body into a Python dict.
"""

print()
print("GET request (JSONPlaceholder public API):")

try:
    response = requests.get(
        "https://jsonplaceholder.typicode.com/todos/1",
        timeout=10,
    )
    response.raise_for_status()   # raises HTTPError if status >= 400

    data = response.json()
    log.info(f"HTTP {response.status_code} | {response.url}")
    print(f"  userId    : {data['userId']}")
    print(f"  title     : {data['title']}")
    print(f"  completed : {data['completed']}")

except requests.exceptions.Timeout:
    log.error("Request timed out")
except requests.exceptions.ConnectionError:
    log.error("Cannot connect — check internet access")
except requests.exceptions.HTTPError as e:
    log.error(f"HTTP error: {e.response.status_code}")


# ── GET with query parameters ─────────────────────────────────

print()
print("GET with query parameters:")

try:
    response = requests.get(
        "https://jsonplaceholder.typicode.com/posts",
        params={"userId": 1, "_limit": 3},   # → ?userId=1&_limit=3
        timeout=10,
    )
    response.raise_for_status()
    posts = response.json()
    log.info(f"HTTP {response.status_code} | fetched {len(posts)} posts")
    for post in posts:
        print(f"  [{post['id']}] {post['title'][:50]}")

except Exception as e:
    log.error(f"Request failed: {e}")


# ── POST request — calling an LLM API ────────────────────────

"""
POST REQUESTS — send data to create or process something.

For LLM APIs: the request body is a JSON dict (the API payload).
requests.post(url, json=payload) serialises the dict to JSON automatically.

REAL OpenAI API:
  url     = "https://api.openai.com/v1/chat/completions"
  headers = {"Authorization": f"Bearer {api_key}"}
  payload = {"model": "gpt-4o", "messages": [...], "max_tokens": 512}
  response = requests.post(url, headers=headers, json=payload, timeout=30)

We use JSONPlaceholder here (no API key needed) to show the POST pattern.
"""

print()
print("POST request — sending JSON data:")

try:
    payload = {
        "title" : "Customer query: Where is my order?",
        "body"  : "Customer 1001 is asking about order #3042",
        "userId": 1,
    }

    response = requests.post(
        "https://jsonplaceholder.typicode.com/posts",
        json   = payload,    # requests serialises dict → JSON automatically
        timeout= 10,
    )
    response.raise_for_status()
    created = response.json()

    log.info(f"HTTP {response.status_code} | Created post id={created.get('id')}")
    print(f"  Sent  : {payload['title']}")
    print(f"  Got id: {created.get('id')}")

except Exception as e:
    log.error(f"POST failed: {e}")


# ── Calling an LLM API (mock if no key) ──────────────────────

"""
This is what EVERY LLM SDK does under the hood.
requests.post() to the API endpoint with your prompt in the body.
"""

def call_openai_api(prompt: str) -> dict | None:
    """
    Call the OpenAI Chat Completions API via raw HTTP.

    In production: set OPENAI_API_KEY in your .env file.
    Without a key: returns a mock response for demonstration.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        log.warning("OPENAI_API_KEY not set — returning mock response")
        return {
            "choices": [{
                "message": {
                    "role"   : "assistant",
                    "content": json.dumps({
                        "category"  : "TRACK_ORDER",
                        "confidence": "high",
                        "reason"    : "Customer asked about order location",
                    })
                }
            }],
            "usage": {"total_tokens": 80},
        }

    url     = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json",
    }
    payload = {
        "model"      : "gpt-4o",
        "messages"   : [{"role": "user", "content": prompt}],
        "max_tokens" : 256,
        "temperature": 0.2,
    }

    try:
        start    = time.perf_counter()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed  = round((time.perf_counter() - start) * 1000)
        response.raise_for_status()
        log.info(f"OpenAI API: HTTP {response.status_code} in {elapsed}ms")
        return response.json()
    except requests.exceptions.HTTPError as e:
        log.error(f"OpenAI API error {e.response.status_code}: {e.response.text[:200]}")
        return None


def extract_text(api_response: dict) -> str | None:
    """Extract the assistant's text from an OpenAI API response dict."""
    if not api_response:
        return None
    choices = api_response.get("choices", [])
    if not choices:
        return None
    return choices[0].get("message", {}).get("content")


print()
print("LLM API call (mock or real depending on OPENAI_API_KEY):")

classification_prompt = """
Classify the customer message and respond ONLY with valid JSON:
{"category": "TRACK_ORDER|BILLING|RETURNS|OTHER", "confidence": "high|medium|low", "reason": "one sentence"}

Customer message: "Where is my order #3042? It has been 8 days."
"""

api_response = call_openai_api(classification_prompt)
text = extract_text(api_response)

if text:
    # Strip markdown fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
        print(f"  Category  : {parsed.get('category')}")
        print(f"  Confidence: {parsed.get('confidence')}")
        print(f"  Reason    : {parsed.get('reason')}")
    except json.JSONDecodeError:
        print(f"  Raw text: {text}")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS:

PART A — Modules vs Packages:
  Module  = a single .py file
  Package = a folder with __init__.py + one or more .py files

  __init__.py makes a folder a package.
  It can be empty (just marks the folder) or re-export names.

  Absolute import: from fastapi_app.models import CustomerRecord
  Relative import: from .models import CustomerRecord  (inside a package)

PART B — requests:
  requests.get(url, params={...}, timeout=10)   → GET request
  requests.post(url, json={...}, timeout=30)    → POST with JSON body
  response.raise_for_status()                   → raises on 4xx/5xx
  response.json()                               → parse JSON body → dict

  requests   → synchronous, use in scripts and notebooks
  httpx      → async, use inside FastAPI and async agents

NEXT: Day 12 — FastAPI
  (wiring everything together: Pydantic models + async + HTTP endpoints)
"""

print()
print("=" * 60)
print("Day 11 complete. Run: uvicorn fastapi_app.main:app --reload")
print("=" * 60)
