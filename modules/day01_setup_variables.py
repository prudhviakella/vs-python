"""
============================================================
Day 01 — Setup, Variables, Data Types, f-strings, os.environ
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU KNOW FROM MODULE 00:
  - An LLM takes a prompt (text in) and returns output (text out)
  - Every prompt has: Role, Context, Task, Output Format, Examples
  - The system message is fixed per deployment
  - The user message carries runtime data — changes every request
  - Tokens cost money — every word you add to a prompt has a price

WHAT YOU WILL LEARN TODAY:
  1. How to set up a Python project (venv + pip)
  2. Variables and the four primitive data types
  3. Type hints — what they are and why they matter
  4. f-strings — how to build LLM prompts from variables
  5. list, dict, set, tuple — first look
  6. os.environ + python-dotenv — loading API keys safely

THE CONNECTION:
  In Module 00 you wrote system prompts BY HAND in a text editor.
  Today you learn the Python building blocks that let you BUILD
  those prompts at runtime — injecting live database values.
  f-strings are the bridge between Module 00 and Module 01.

RUN THIS FILE:
  python modules/day01_setup_variables.py
"""

# ── Imports — all at the top of the file ─────────────────────
from typing import Optional      # Optional[str] = str or None


print("=" * 60)
print("DAY 01 — Setup, Variables, Types, f-strings")
print("=" * 60)


# ============================================================
# SECTION 1 — PROJECT SETUP
# ============================================================

"""
Every Python project uses a virtual environment (venv) —
an isolated Python installation so package versions from
one project don't break another.

Run these commands in your TERMINAL (not inside Python):

  python -m venv venv                  ← create the virtual environment
  source venv/bin/activate             ← Mac / Linux
  venv\\Scripts\\activate               ← Windows

You will see (venv) at the start of your terminal prompt.
That confirms you are inside the environment.

Then install all required packages:
  pip install -r requirements.txt

Then run any file:
  python modules/day01_setup_variables.py
"""
# ============================================================
# SECTION 2 — VARIABLES AND DATA TYPES
# ============================================================

"""
WHAT IS A VARIABLE?
A named container that stores a single value.

  name_of_variable = value

Python figures out the type from the value you assign.
You do NOT declare the type first (unlike Java or C++).

Python has four PRIMITIVE data types — single-value types:

  int    whole numbers with no decimal point
  float  numbers with a decimal point
  str    text — any characters wrapped in quotes
  bool   only two possible values: True or False

And one special value:

  None   represents "no value" or "not set yet"

Everything else — list, dict, set, tuple — is a CONTAINER
(a variable that holds multiple values). Those come in Section 5.
"""

print()
print("─" * 60)
print("SECTION 2 — Variables and Data Types")
print("─" * 60)


# ── int (integer) ─────────────────────────────────────────────

"""
int — a whole number with no decimal point.
Can be positive, negative, or zero.

  10, -5, 0, 1001, 8000

In everyday Python:
  counting things, index positions, loop counters

In LLM engineering:
  token counts, customer IDs, retry limits, port numbers
"""

# Simple — the naked concept
a = 10
b = 3
print()
print("int:")
print(f"  a = {a},  b = {b}")
print(f"  a + b = {a + b},  a * b = {a * b},  a // b = {a // b}  (floor division)")

# ShopSmart — where you actually use int in production code
max_tokens  = 1024   # maximum tokens the LLM is allowed to return
max_retries = 3      # how many times to retry a failed API call
customer_id = 1001   # from customers.csv
app_port    = 8000   # FastAPI will run on this port number

print()
print("  In LLM engineering:")
print(f"  max_tokens  = {max_tokens}   ← each token costs money (Module 00)")
print(f"  max_retries = {max_retries}     ← LLM APIs fail — we retry")
print(f"  customer_id = {customer_id}  ← from customers.csv")
print(f"  app_port    = {app_port}   ← FastAPI server (Day 12)")
print(f"  type(max_tokens) → {type(max_tokens)}")


# ── float (floating-point number) ─────────────────────────────

"""
float — a number with a decimal point.
Can be positive, negative, or zero.

  3.14, -0.5, 0.0, 205.21, 0.85

In everyday Python:
  measurements, percentages, averages

In LLM engineering:
  temperature  (controls LLM creativity — 0.0 to 1.0)
  price        (from products.csv)
  similarity   (cosine similarity for RAG retrieval — 0.0 to 1.0)

temperature explained:
  0.0 = fully deterministic — same input always gives same output
  1.0 = very creative and random
  0.2 = slightly creative — good for customer support (consistent)
"""

# Simple
pi     = 3.14159
ratio  = 2 / 3
print()
print("float:")
print(f"  pi    = {pi}")
print(f"  2 / 3 = {ratio:.4f}  (division always returns float in Python)")

# ShopSmart
temperature          = 0.2    # LLM creativity — low = consistent and factual
top_p                = 0.9    # nucleus sampling — leave at 0.9 for most tasks
similarity_threshold = 0.85   # minimum RAG similarity score to include a result
product_price        = 205.21 # Classic Monitor price from products.csv

print()
print("  In LLM engineering:")
print(f"  temperature          = {temperature}   ← low = factual, high = creative")
print(f"  similarity_threshold = {similarity_threshold}  ← RAG relevance cutoff")
print(f"  product_price        = {product_price} ← from products.csv")
print(f"  type(temperature) → {type(temperature)}")


# ── str (string) ──────────────────────────────────────────────

"""
str — a sequence of characters. Always wrapped in quotes.
Single quotes and double quotes both work — be consistent.

  "hello"  'world'  "Danielle Johnson"  "gpt-4o"

A string can contain letters, numbers, spaces, symbols,
and even emoji — anything you can type.

An empty string "" is a valid string (length zero).

In everyday Python:
  names, messages, file paths, any text

In LLM engineering:
  model names, prompt text, order IDs, customer names,
  agent names, API endpoints — almost everything
"""

# Simple
word    = "hello"
sentence = "The quick brown fox"
empty   = ""
print()
print("str:")
print(f"  word     = '{word}'    length = {len(word)}")
print(f"  sentence = '{sentence}'    length = {len(sentence)}")
print(f"  empty    = '{empty}'         length = {len(empty)}")

# ShopSmart
model_name    = "gpt-4o"              # which LLM to call
customer_name = "Danielle Johnson"    # from customers.csv
order_id      = "ORD-3042"            # from orders.csv
order_status  = "In Transit"          # from orders.csv
product_name  = "Classic Monitor"     # from products.csv

print()
print("  In LLM engineering:")
print(f"  model_name    = '{model_name}'")
print(f"  customer_name = '{customer_name}'")
print(f"  order_id      = '{order_id}'")
print(f"  order_status  = '{order_status}'")
print(f"  type(model_name) → {type(model_name)}")


# ── bool (boolean) ────────────────────────────────────────────

"""
bool — has exactly two possible values: True or False.
Both are capitalised — this is required in Python.

  True   False

bool is often the result of a comparison:
  10 > 5    → True
  3 == 7    → False
  "a" in "apple" → True

In everyday Python:
  conditions in if/elif, loop flags

In LLM engineering:
  feature flags (is streaming on?), validation toggles,
  verified_purchase from reviews.csv
"""

# Simple
is_hot       = True
is_cold      = False
greater      = 10 > 5      # comparison → bool
print()
print("bool:")
print(f"  is_hot   = {is_hot}")
print(f"  is_cold  = {is_cold}")
print(f"  10 > 5   = {greater}   (comparison returns bool)")

# ShopSmart
stream_response = True    # send tokens to the user as they arrive
validate_output = True    # run Pydantic validation on LLM response (Day 08)
is_verified     = False   # verified_purchase column from reviews.csv

print()
print("  In LLM engineering:")
print(f"  stream_response = {stream_response}   ← streaming tokens in Day 12")
print(f"  validate_output = {validate_output}   ← Pydantic validation in Day 08")
print(f"  is_verified     = {is_verified}  ← verified_purchase from reviews.csv")
print(f"  type(stream_response) → {type(stream_response)}")


# ── None ──────────────────────────────────────────────────────

"""
None — represents "no value" or "not set yet".
It is its own type (NoneType) with only one possible value.

Use None when:
  - A variable has not been assigned a value yet
  - A function finds nothing to return
  - An optional field was not provided

In LLM engineering:
  pending_response = None  ← the LLM hasn't responded yet
  session_id = None        ← no session created yet
  api_key = None           ← not loaded from .env yet
"""

pending_response = None   # LLM has not responded yet
session_id       = None   # session not created yet

print()
print("None:")
print(f"  pending_response = {pending_response}  ← nothing yet")
print(f"  session_id       = {session_id}  ← not created yet")
print(f"  type(None)       → {type(None)}")
print(f"  pending_response is None → {pending_response is None}  ← correct way to check")


# ============================================================
# SECTION 3 — TYPE HINTS
# ============================================================

"""
TYPE HINTS — telling Python (and your IDE) what type a variable holds.

Syntax:
  variable_name: type = value

Examples:
  max_tokens  : int   = 1024
  temperature : float = 0.2
  model_name  : str   = "gpt-4o"
  stream      : bool  = True
  api_key     : Optional[str] = None   ← str or None

IMPORTANT: Python does NOT enforce type hints at runtime.
  max_tokens: int = "one thousand"   ← Python allows this. No error.

So why write them?
  1. Your IDE (VS Code, PyCharm) shows a warning if you pass
     the wrong type — catches bugs before you run the code
  2. Pydantic DOES enforce them at runtime (Day 08)
  3. They make the code self-documenting — any reader knows
     immediately what type each variable should hold

You will see type hints on every variable and function
throughout this codebase from Day 03 onwards.
"""

print()
print("─" * 60)
print("SECTION 3 — Type Hints")
print("─" * 60)

# Without type hints (valid Python):
count = 10
name  = "Alice"

# With type hints (same variables — just more explicit):
count : int = 10
name  : str = "Alice"

# Optional means the value can be the stated type OR None
# We import Optional from the typing module (imported at the top of this file)
api_key : Optional[str] = None   # will be a str once loaded, None until then

# Full ShopSmart set with type hints:
max_tokens  : int   = 1024
temperature : float = 0.2
model_name  : str   = "gpt-4o"
stream      : bool  = True

print()
print("  Variables with type hints:")
print(f"  max_tokens  : int   = {max_tokens}")
print(f"  temperature : float = {temperature}")
print(f"  model_name  : str   = '{model_name}'")
print(f"  stream      : bool  = {stream}")
print(f"  api_key     : Optional[str] = {api_key}  ← None until loaded from .env")


# ============================================================
# SECTION 4 — f-STRINGS
# ============================================================

"""
WHAT IS AN f-STRING?
A way to embed Python variable values directly inside a string.

Syntax: put the letter f before the opening quote,
        then use {variable_name} inside curly braces.

Without f-string (clunky string concatenation):
  message = "Hello " + customer_name + ", your order " + order_id + " is " + order_status

With f-string (clean and readable):
  message = f"Hello {customer_name}, your order {order_id} is {order_status}"

WHY THIS IS THE MOST IMPORTANT CONCEPT IN DAY 01:
  In Module 00 you wrote prompts BY HAND with the customer name
  and order ID already typed in.

  In production, customer_name and order_id come from a database
  query at runtime — they are different for every request.
  f-strings are how you inject those live values into the prompt.

  Every LLM prompt is a TEMPLATE.
  f-strings fill in the blanks at runtime.
"""

print()
print("─" * 60)
print("SECTION 4 — f-strings")
print("─" * 60)


# ── Basic f-string ────────────────────────────────────────────

first_name = "Alice"
score      = 95

result = f"Hello {first_name}, your score is {score}."
print()
print("Basic f-string:")
print(f"  {result}")


# ── Expressions inside {} ─────────────────────────────────────

"""
You can put any Python expression inside the braces — not just
a variable name. Python evaluates it and converts it to a string.
"""

a = 10
b = 3
print()
print("Expressions inside {}:")
print(f"  a = {a},  b = {b}")
print(f"  a + b = {a + b}")
print(f"  a > b = {a > b}")
print(f"  'pass' if score >= 90 else 'fail'  →  {'pass' if score >= 90 else 'fail'}")


# ── Number formatting inside {} ───────────────────────────────

"""
Add a colon after the variable name to format numbers:

  {value:,}    → add comma thousand-separator    1048576 → 1,048,576
  {value:.2f}  → fixed 2 decimal places          205.2   → 205.20
  {value:.1f}  → fixed 1 decimal place           0.2     → 0.2
  {value:>10}  → right-align in 10-character field
  {value:<10}  → left-align in 10-character field
"""

big_number    = 1048576
exact_price   = 205.2
temperature_v = 0.19999

print()
print("Number formatting:")
print(f"  {{big_number:,}}    → {big_number:,}")
print(f"  {{exact_price:.2f}} → {exact_price:.2f}")
print(f"  {{temperature:.1f}} → {temperature_v:.1f}")


# ── Multi-line f-string — the LLM prompt pattern ─────────────

"""
Use triple quotes for prompts that span multiple lines.
The backslash \\ at the end of the opening line prevents a
leading blank line appearing in the string.
"""

customer_name = "Danielle Johnson"
order_id      = "ORD-3042"
order_status  = "In Transit"
product_name  = "Classic Monitor"
product_price = 205.21

# This is the user message — built from database values at runtime.
# In Module 00 you wrote this out manually with names already in it.
# Here Python assembles it from variables that change per request.
user_message = f"""\
Customer name  : {customer_name}
Order ID       : {order_id}
Order status   : {order_status}
Product ordered: {product_name} (${product_price:.2f})

The customer is asking: "Where is my order and when will it arrive?"
Please answer based only on the order status shown above.
Respond in 2 sentences maximum.
"""

print()
print("Multi-line f-string — LLM user message:")
print("-" * 40)
print(user_message)


# ── System prompt as a plain multi-line string ────────────────

"""
The system prompt is the fixed instruction to the LLM.
It does NOT change per request — only the user message changes.

This is the ## Role + ## Task + ## Output Format template
from Module 00 Technique 01, now written as a Python string.
Day 04 shows how to load this from a .txt file at startup
instead of hardcoding it here.
"""

system_prompt = """\
## Role
You are a customer support assistant for ShopSmart e-commerce.

## Task
Answer the customer question using ONLY the information provided.
You MUST NOT make up order details, prices, or dates.
You MUST keep your response under 3 sentences.

## Output Format
Plain English. Always mention the order ID in your response.
"""

print("System prompt (Module 00 Technique 01, now in Python):")
print("-" * 40)
print(system_prompt)


# ============================================================
# SECTION 5 — DATA STRUCTURES (first look)
# ============================================================

"""
So far every variable holds ONE value:
  customer_name = "Danielle Johnson"
  product_price = 205.21

What if you have 250 customers? Or 5 messages in a conversation?
You need a CONTAINER — a variable that holds MULTIPLE values.

Python has four built-in containers:

  list  — ordered sequence, allows duplicates, can change
  dict  — key-value pairs, look up any value by its key
  set   — unique values only, duplicates are removed automatically
  tuple — ordered sequence, cannot be changed after creation

Day 03 covers every method and operation on all four in depth.
Today: understand what each one looks like and when to use it.
"""

print()
print("─" * 60)
print("SECTION 5 — Data Structures (first look)")
print("─" * 60)


# ── list ──────────────────────────────────────────────────────

"""
list — ordered sequence of items in square brackets [].

The items keep their order. You can have duplicates.
You can add, remove, or change items after creation.
Access items by position (index) — first item is index 0.

In LLM engineering:
  The conversation history that gets sent to the OpenAI API IS a list.
  Each item in the list is one message (a dict with role and content).
  This is not an abstraction — it IS the OpenAI API wire format.
"""

# Simple — a list of numbers
scores = [85, 92, 78, 95, 60]
print()
print("list:")
print(f"  scores          = {scores}")
print(f"  scores[0]       = {scores[0]}   ← index 0 is the first item")
print(f"  scores[-1]      = {scores[-1]}   ← index -1 is the last item")
print(f"  scores[1:3]     = {scores[1:3]}   ← slice: items at index 1 and 2")
print(f"  len(scores)     = {len(scores)}")

# ── dict ──────────────────────────────────────────────────────

"""
dict — key-value pairs in curly braces with colons {key: value}.

Every value has a key (a name) — you look up values by key.
Keys must be unique — you cannot have two entries with the same key.
Values can be any type — str, int, float, bool, list, even another dict.

In LLM engineering:
  Model configuration, one API message, a CSV row from the database,
  a parsed LLM JSON response — all of these are dicts.
"""

# Simple — a person dict
person = {"name": "Alice", "age": 25, "city": "Hyderabad"}
print()
print("dict:")
print(f"  person            = {person}")
print(f"  person['name']    = {person['name']}   ← access by key")
print(f"  person['age']     = {person['age']}")

# ShopSmart — model configuration dict
model_config = {
    "model"      : "gpt-4o",  # which model to call
    "max_tokens" : 1024,      # maximum tokens in the response
    "temperature": 0.2,       # creativity setting
    "stream"     : False,     # whether to stream tokens (Day 12)
}
print()
print("  In LLM engineering (model config dict):")
for key, value in model_config.items():
    print(f"  {key:15s}: {value}")

# ShopSmart — the LLM message history
messages = [
    {"role": "system",    "content": system_prompt},
    {"role": "user",      "content": user_message},
]
print()
print("  In LLM engineering (OpenAI message history):")
print(f"  len(messages) = {len(messages)}")
for msg in messages:
    print(f"  role={msg['role']:10s} | {msg['content'][:55]}...")


# ── set ───────────────────────────────────────────────────────

"""
set — unique values only, in curly braces {}.

Duplicates are removed automatically when the set is created.
Sets are UNORDERED — items have no guaranteed position.
The primary use is fast membership checking: is X in this set?

Checking membership in a set is O(1) — instant, regardless of size.
Checking membership in a list is O(n) — slows down as list grows.

In LLM engineering:
  The set of tool names an agent is allowed to call.
  When the LLM requests a tool, you check: is it in the allowed set?
"""

# Simple — a set of colours (notice duplicates are removed)
colours = {"red", "blue", "green", "red", "blue"}
print()
print("set:")
print(f"  colours = {{\"red\", \"blue\", \"green\", \"red\", \"blue\"}}")
print(f"  result  = {colours}   ← duplicates removed")
print(f"  'red' in colours → {'red' in colours}")

# ShopSmart — allowed LLM agent tools
available_tools = {
    "lookup_order",
    "lookup_customer",
    "lookup_product",
    "check_inventory",
}
print()
print("  In LLM engineering (allowed agent tools):")
print(f"  'lookup_order'    in available_tools → {'lookup_order' in available_tools}")
print(f"  'delete_database' in available_tools → {'delete_database' in available_tools}")


# ── tuple ─────────────────────────────────────────────────────

"""
tuple — ordered sequence in parentheses ().

Like a list, BUT immutable — you cannot change it after creation.
Use a tuple when the values should remain fixed.

Unpacking: assign each value to its own variable in one line.
  version_num, version_desc = (4, "Added few-shot examples")

In LLM engineering:
  Prompt version records (number + description).
  Functions that return two values return them as a tuple.
"""

# Simple — a coordinate pair
coordinates = (40.7128, -74.0060)   # New York City
lat, lon    = coordinates           # unpacking into two variables
print()
print("tuple:")
print(f"  coordinates = {coordinates}")
print(f"  lat = {lat},  lon = {lon}   ← unpacked in one line")

# ShopSmart — prompt version record
prompt_version          = (4, "Added few-shot examples from Module 00 Technique 02")
version_num, version_desc = prompt_version   # unpacking
print()
print("  In LLM engineering (prompt version record):")
print(f"  prompt_version = {prompt_version}")
print(f"  version_num    = {version_num}")
print(f"  version_desc   = '{version_desc}'")

# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 01:

PRIMITIVE TYPES — hold one value each:
  int    whole number               max_tokens = 1024
  float  decimal number             temperature = 0.2
  str    text in quotes             model_name = "gpt-4o"
  bool   True or False              stream = True
  None   no value / not set yet     api_key = None

CONTAINER TYPES — hold multiple values (deep dive Day 03):
  list  = [...]  ordered, mutable, allows duplicates
  dict  = {...}  key-value pairs, look up by key
  set   = {...}  unique values only, fast membership check
  tuple = (...)  ordered, immutable

TYPE HINTS:
  temperature : float = 0.2   ← Python won't enforce this
                                 but your IDE and Pydantic will

f-STRINGS:
  f"Hello {customer_name}, order {order_id} is {order_status}."
  ← the primary tool for building LLM prompts in Python

API KEYS:
  Never hardcode. Use .env + load_dotenv() + os.environ.get()

CONNECTION TO MODULE 00:
  The system prompt (## Role/Task/Output/Examples) is now a
  Python string — Day 04 loads it from a file.
  The user message is an f-string built from database values.
  Day 08 loads those values from a real Postgres database.
  Day 12 wires everything into a live FastAPI service.

NEXT: Day 02 — Conditions and Loops
  if/elif/else to route customer queries to the right agent.
  while loops to retry failed LLM API calls automatically.
"""

print()
print("=" * 60)
print("Day 01 complete.")
print("Next: python modules/day02_conditions_loops.py")
print("=" * 60)