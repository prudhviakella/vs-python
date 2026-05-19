"""
============================================================
Day 03 — Functions + Data Structures (deep dive)
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU KNOW FROM DAY 02:
  - if/elif/else, for loops, while loops, break, continue
  - You wrote the same routing if/elif block several times
    → today you wrap it in a function and write it ONCE

WHAT YOU WILL LEARN TODAY:
  1. def, parameters, return, default values
  2. *args   — variable-length positional arguments
  3. **kwargs — variable-length keyword arguments
  4. Functions as objects — assign, pass, receive
  5. sorted(), map(), filter() — passing functions as arguments
  6. lambda — one-line anonymous functions
  7. List  — all methods: append, extend, pop, sort, slice
  8. Dict  — all methods: .get(), .items(), .keys(), .values(), .update()
  9. Set   — add, discard, union, intersection
  10. Tuple — packing, unpacking, zip()

CONNECTION TO MODULE 00:
  Every LLM API call requires three things built here:
    build_system_prompt() → the ## Role + ## Task section
    build_api_request()   → the full API payload dict
    messages list         → the OpenAI conversation history format
  route_query() is the Module 00 Technique 01 routing rules as Python.

RUN THIS FILE:
  python modules/day03_functions_data_structures.py
"""

from typing import Any

print("=" * 60)
print("DAY 03 — Functions + Data Structures")
print("=" * 60)


# ============================================================
# SECTION 1 — FUNCTIONS
# ============================================================

"""
WHAT IS A FUNCTION?
A named, reusable block of code. Write it once — call it anywhere.

In Day 02 you copy-pasted the same if/elif/else routing block
every time you needed it. That is the signal: wrap it in a function.

Syntax:
  def function_name(parameter1, parameter2):
      \"\"\"One-line description.\"\"\"
      # code here
      return result

Keywords:
  def       → marks the start of a function definition
  ()        → parameters live here
  :         → required at the end of the def line
  return    → sends a value back to whoever called the function
  indentation → the function body must be 4 spaces in
"""

print()
print("─" * 60)
print("SECTION 1 — Functions")
print("─" * 60)


# ── No parameters, no return value ───────────────────────────

def greet():
    """Print a greeting."""
    print("  Hello! Welcome.")

# Call the function twice — same code, no copy-paste
print()
print("No params, no return:")
greet()
greet()


# ── Parameters and return value ───────────────────────────────

def add(a, b):
    """Return the sum of a and b."""
    return a + b

print()
print("Params + return:")
print(f"  add(3, 7) = {add(3, 7)}")


# ── ShopSmart — the Day 02 routing block as a function ───────

# The if/elif/else from Day 02 is now a function.
# Write once → call for any query, any number of times.
def route_query(query: str) -> str:
    """Route a customer query to the correct support agent."""
    q = query.lower()
    if   "cancel" in q or "refund"   in q: return "human_agent"
    elif "track"  in q or "where"    in q: return "order_agent"
    elif "return" in q or "exchange" in q: return "returns_agent"
    elif "price"  in q or "discount" in q: return "promotions_agent"
    elif "product" in q or "spec"    in q: return "catalog_agent"
    else:                                   return "general_agent"

print()
print("ShopSmart — route_query() (Day 02 routing block as a function):")
for q in ["Where is my order?", "I want a refund", "Do you have discounts?"]:
    print(f"  '{q}' → {route_query(q)}")


# ── Default parameter values ──────────────────────────────────

"""
A parameter can have a default value.
If the caller does not pass it, the default is used.
If the caller does pass it, the caller's value wins.

Rule: parameters WITH defaults must come AFTER those without.
  def fn(required, optional=default)   ← correct
  def fn(optional=default, required)   ← SyntaxError
"""

def power(base, exponent=2):
    """Return base raised to exponent. Default: squared."""
    return base ** exponent

print()
print("Default parameter values:")
print(f"  power(3)    = {power(3)}")       # uses default exponent=2
print(f"  power(3, 3) = {power(3, 3)}")    # caller overrides to 3

# ShopSmart — max_sentences has a sensible default for most callers.
# Callers that need one-sentence replies can override it explicitly.
def build_system_prompt(role: str, domain: str, max_sentences: int = 3) -> str:
    """Build a system prompt following the Module 00 Technique 01 template."""
    return (
        f"You are a {role} for {domain}. "
        f"Respond in {max_sentences} sentences maximum. "
        f"Only use information provided to you — never invent details."
    )

print()
print("ShopSmart — build_system_prompt() with default:")
p1 = build_system_prompt("support agent", "ShopSmart")
p2 = build_system_prompt("support agent", "ShopSmart", max_sentences=1)
print(f"  Default (3): {p1[:65]}...")
print(f"  Override(1): {p2[:65]}...")


# ── *args — variable-length positional arguments ──────────────

"""
*args collects any number of positional arguments into a TUPLE.
Inside the function the name is just args — the * is the syntax.

Use *args when the caller might pass one value or ten
and you want to handle all cases without changing the signature.
"""

def total(*numbers):
    """Add any number of values together."""
    result = 0
    for n in numbers:
        result += n
    return result

print()
print("*args — variable positional arguments:")
print(f"  total(1, 2)          = {total(1, 2)}")
print(f"  total(1, 2, 3, 4, 5) = {total(1, 2, 3, 4, 5)}")

# ShopSmart — combine_context() accepts however many RAG chunks
# the retrieval step returns. The caller never needs to count them.
def combine_context(*chunks: str, separator: str = "\n\n") -> str:
    """
    Join multiple RAG context chunks into one string.
    Empty chunks are silently ignored.
    The separator= is a keyword-only argument after *chunks.
    """
    non_empty = [c.strip() for c in chunks if c.strip()]
    return separator.join(non_empty)

print()
print("ShopSmart — combine_context(*chunks):")
ctx = combine_context(
    "[Doc 1] Classic Monitor: 27-inch 4K display, $205.21.",
    "[Doc 2] Return policy: 30 days from delivery.",
    "",   # empty chunk — ignored automatically
)
print(f"  Combined ({len(ctx)} chars): {ctx[:80]}...")


# ── **kwargs — variable-length keyword arguments ──────────────

"""
**kwargs collects any number of keyword arguments into a DICT.
Inside the function the name is just kwargs — the ** is the syntax.

Use **kwargs when callers may pass optional named parameters
that you cannot predict in advance — like LLM API options.
"""

def describe(**details):
    """Print whatever keyword arguments are passed in."""
    for key, value in details.items():
        print(f"  {key}: {value}")

print()
print("**kwargs — variable keyword arguments:")
describe(name="Alice", age=25, city="Hyderabad")

# ShopSmart — build_api_request() always needs model and messages.
# Everything else (temperature, max_tokens, stream, top_p…) is optional
# and changes per call. **kwargs handles all of them without listing each.
def build_api_request(model: str, messages: list, **kwargs: Any) -> dict:
    """
    Build an OpenAI-compatible API request payload.
    Required: model, messages.
    Optional via **kwargs: temperature, max_tokens, stream, top_p, etc.
    """
    payload = {"model": model, "messages": messages}
    payload.update(kwargs)   # merge all optional params into the payload
    return payload

print()
print("ShopSmart — build_api_request(**kwargs):")
payload = build_api_request(
    model       = "gpt-4o",
    messages    = [{"role": "user", "content": "Hello"}],
    temperature = 0.2,
    max_tokens  = 512,
    stream      = True,
)
for k, v in payload.items():
    if k != "messages":
        print(f"  {k}: {v}")


# ── Functions as objects ──────────────────────────────────────

"""
FUNCTIONS ARE FIRST-CLASS OBJECTS IN PYTHON.

You can:
  1. Assign a function to a variable
  2. Pass a function INTO another function as an argument
  3. Receive a function as a return value (Day 05 — higher-order functions)

This is not a trick — it is how sorted(), map(), filter() work.
They all accept a function as the key= or first argument.
Day 06 decorators are built entirely on this same concept.
"""

def square(n): return n * n
def cube(n):   return n * n * n

# Writing square without () assigns the function object itself.
# Writing square() calls it and assigns the return value.
operation = square           # assigns the function — not calling it
print()
print("Function as object — assign to variable:")
print(f"  operation = square  →  operation(5) = {operation(5)}")
operation = cube
print(f"  operation = cube    →  operation(5) = {operation(5)}")

# A function that takes another function as an argument
def apply(fn, value):
    """Call fn with value and return the result."""
    return fn(value)

print()
print("Passing a function as an argument:")
print(f"  apply(square, 4) = {apply(square, 4)}")
print(f"  apply(cube,   4) = {apply(cube,   4)}")


# ── sorted(), map(), filter() with lambda ─────────────────────

"""
lambda is a one-line anonymous function.

  lambda x: x["price"]   →   for each x, return x["price"]

It is shorthand for writing a def when the function is simple
and only used in one place. Used almost exclusively with
sorted(), map(), filter(), and similar functions.

sorted(items, key=fn) — fn tells Python what value to sort by.
map(fn, items)        — apply fn to every item, return results.
filter(fn, items)     — keep items where fn returns True.
"""

products = [
    {"name": "Classic Monitor",   "price": 205.21, "rating": 4.2},
    {"name": "Ultimate Perfume",  "price": 568.17, "rating": 3.8},
    {"name": "Yoga Mat Pro",      "price":  45.00, "rating": 4.7},
    {"name": "Budget Headphones", "price":  29.99, "rating": 3.1},
]

by_price  = sorted(products, key=lambda x: x["price"])
by_rating = sorted(products, key=lambda x: x["rating"], reverse=True)

print()
print("ShopSmart — sorted() with key= lambda:")
print("  Cheapest first:")
for p in by_price:
    print(f"    ${p['price']:7.2f}  {p['name']}")
print("  Highest rated first:")
for p in by_rating:
    print(f"    ★{p['rating']}  {p['name']}")

prices     = [205.21, 568.17, 45.00, 29.99]
discounted = list(map(lambda p: round(p * 0.9, 2), prices))    # 10% off all
affordable = list(filter(lambda p: p < 100, prices))            # under $100 only

print()
print("ShopSmart — map() and filter():")
print(f"  Original  : {prices}")
print(f"  10% off   : {discounted}")
print(f"  Under $100: {affordable}")


# ============================================================
# SECTION 2 — LIST (deep dive)
# ============================================================

"""
LIST — ordered, mutable, allows duplicates.
Every LLM API call sends a list of dicts as the conversation history.
Every CSV loader returns a list of dicts.
Every search returns a list of results.
"""

print()
print("─" * 60)
print("SECTION 2 — List (deep dive)")
print("─" * 60)

# Core methods on a list of numbers
nums = [3, 1, 4, 1, 5, 9]
print()
print("List methods:")
nums.append(2)
print(f"  append(2)        : {nums}")
nums.extend([6, 5])
print(f"  extend([6, 5])   : {nums}")
popped = nums.pop()
print(f"  pop()            : {nums}  ← removed: {popped}")
nums.sort()
print(f"  sort()           : {nums}")
nums.reverse()
print(f"  reverse()        : {nums}")
print(f"  index(9)         : {nums.index(9)}")
print(f"  count(1)         : {nums.count(1)}")
print(f"  slice [1:4]      : {nums[1:4]}")

# ShopSmart — the message history grows one append() at a time.
# This is the exact pattern used in every LLM chat application.
system_prompt = build_system_prompt("support agent", "ShopSmart")
messages: list[dict] = [{"role": "system", "content": system_prompt}]

messages.append({"role": "user",      "content": "Where is my order #3042?"})
messages.append({"role": "assistant", "content": "Could you confirm your email?"})
messages.append({"role": "user",      "content": "It is john21@example.net"})

print()
print("ShopSmart — LLM message history (list grows with append):")
for msg in messages:
    print(f"  {msg['role']:12s} | {msg['content'][:55]}")
print(f"  Total turns: {len(messages)}")


# ============================================================
# SECTION 3 — DICT (deep dive)
# ============================================================

"""
DICT — key-value pairs. Access by key. Keys are unique.
Model config, one API message, a CSV row, a parsed LLM response —
all are dicts. The most common data structure in LLM engineering.
"""

print()
print("─" * 60)
print("SECTION 3 — Dict (deep dive)")
print("─" * 60)

person = {"name": "Alice", "age": 25}
print()
print("Dict methods:")
print(f"  .keys()              : {list(person.keys())}")
print(f"  .values()            : {list(person.values())}")
print(f"  .items()             : {list(person.items())}")
print(f"  .get('name')         : {person.get('name')}")
print(f"  .get('phone', 'N/A') : {person.get('phone', 'N/A')}")   # safe — no crash

person.update({"city": "Hyderabad", "age": 26})
print(f"  .update(...)         : {person}")
popped_val = person.pop("city")
print(f"  .pop('city')         : {person}  ← removed: {popped_val}")


# ShopSmart — .get() is critical when reading LLM JSON responses.
# In Module 00 Technique 04 the LLM was told to return specific fields.
# It doesn't always comply. .get() is how you handle missing fields safely.
#   dict["missing_key"]           → KeyError — crashes the service
#   dict.get("missing_key", "N/A") → "N/A"   — safe fallback
llm_response = {"category": "TRACK_ORDER", "confidence": "high"}
category   = llm_response.get("category",   "UNKNOWN")
confidence = llm_response.get("confidence", "low")
reason     = llm_response.get("reason",     "not provided")   # key is missing

print()
print("ShopSmart — .get() on LLM response (reason field is missing):")
print(f"  category  : {category}")
print(f"  confidence: {confidence}")
print(f"  reason    : {reason}   ← key missing, default used")

# .items() is the right way to loop over a dict key-value pairs.
model_config = {"model": "gpt-4o", "max_tokens": 1024, "temperature": 0.2, "stream": False}
print()
print("ShopSmart — .items() to loop model config:")
for key, value in model_config.items():
    print(f"  {key:15s}: {value}")

# Dict unpacking with ** merges two dicts.
# Keys from the second dict override keys from the first.
defaults  = {"temperature": 0.2, "max_tokens": 512, "stream": False}
overrides = {"temperature": 0.0, "max_tokens": 256}
merged    = {**defaults, **overrides}
print()
print("Dict unpacking — {**defaults, **overrides}:")
print(f"  defaults  : {defaults}")
print(f"  overrides : {overrides}")
print(f"  merged    : {merged}   ← overrides win on duplicate keys")


# ============================================================
# SECTION 4 — SET (deep dive)
# ============================================================

"""
SET — unique values only. No guaranteed order.
The primary use: fast O(1) membership checking.
`in` on a list is O(n) — slows with size.
`in` on a set is O(1) — instant regardless of size.
"""

print()
print("─" * 60)
print("SECTION 4 — Set (deep dive)")
print("─" * 60)

a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print()
print("Set operations:")
print(f"  a = {a},  b = {b}")
print(f"  a | b  (union)      : {a | b}")
print(f"  a & b  (intersect)  : {a & b}")
print(f"  a - b  (difference) : {a - b}")

a.add(10)
print(f"  a.add(10)           : {a}")
a.discard(99)   # discard is safe — no error if 99 is not in the set
print(f"  a.discard(99)       : {a}   ← 99 was not there, no error")

# ShopSmart — when the LLM agent (Think → Act → Observe loop from
# Module 00) requests a tool, validate the name before calling it.
# Use a set so validation stays O(1) even with 100 tools registered.
ALLOWED_TOOLS: set[str] = {
    "lookup_order",
    "lookup_customer",
    "lookup_product",
    "check_inventory",
    "search_reviews",
}

print()
print("ShopSmart — agent tool validation with set (O(1)):")
for tool in ["lookup_order", "delete_database", "search_reviews", "format_disk"]:
    status = "ALLOWED" if tool in ALLOWED_TOOLS else "REJECTED"
    print(f"  '{tool}': {status}")


# ============================================================
# SECTION 5 — TUPLE (deep dive)
# ============================================================

"""
TUPLE — ordered, immutable. Cannot be changed after creation.
Use a tuple when the values must stay fixed — version records,
coordinate pairs, or a function returning two values at once.

Unpacking assigns each position to its own variable in one line:
  version, description = (4, "Added few-shot examples")
"""

print()
print("─" * 60)
print("SECTION 5 — Tuple + zip()")
print("─" * 60)

coordinates = (40.7128, -74.0060)    # New York City
lat, lon    = coordinates             # unpack into two variables
print()
print("Tuple packing + unpacking:")
print(f"  coordinates = {coordinates}")
print(f"  lat = {lat},  lon = {lon}   ← unpacked in one line")

# A function can return multiple values as a tuple.
# The caller unpacks them in one assignment line.
def min_max(numbers):
    """Return (minimum, maximum) as a tuple."""
    return min(numbers), max(numbers)

low, high = min_max([3, 1, 7, 2, 9])
print()
print("Function returning multiple values via tuple:")
print(f"  min_max([3, 1, 7, 2, 9]) → low={low}, high={high}")


# ── zip() — pair items from two lists ────────────────────────

# zip() pairs items from two (or more) lists by position.
# It stops when the shorter list runs out.
names  = ["Alice", "Bob", "Carol"]
scores = [90, 75, 88]
print()
print("zip() — pair two lists by position:")
for name, score in zip(names, scores):
    print(f"  {name}: {score}")

# ShopSmart — build conversation history from two parallel lists.
# zip() pairs each user message with its assistant reply.
user_messages = ["Where is my order?", "What is the return policy?"]
asst_messages = ["Please share your order ID.", "Returns accepted within 30 days."]

conversation: list[dict] = []
for user_msg, asst_msg in zip(user_messages, asst_messages):
    conversation.append({"role": "user",      "content": user_msg})
    conversation.append({"role": "assistant", "content": asst_msg})

print()
print("ShopSmart — zip() to pair user and assistant messages:")
for msg in conversation:
    print(f"  {msg['role']:12s} | {msg['content']}")

# Prompt version history — list of tuples.
# Tuples prevent accidental modification of the record.
prompt_versions: list[tuple[int, str]] = [
    (1, "Initial ShopSmart support prompt"),
    (2, "Added refund handling rules"),
    (3, "Improved output format — Technique 04"),
    (4, "Added few-shot examples — Technique 02"),
]

print()
print("ShopSmart — prompt version history (list of tuples):")
for version, description in prompt_versions:    # unpack each tuple
    print(f"  v{version}: {description}")

latest_v, latest_d = prompt_versions[-1]
print(f"\n  Latest: v{latest_v} — {latest_d}")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 03:

1. def, parameters, return
   Default values: parameters WITH defaults must come AFTER those without.

2. *args  → caller passes any number of positional values → tuple inside fn
   **kwargs → caller passes any number of keyword values → dict inside fn

3. Functions are objects:
   - Assign to a variable: operation = square
   - Pass as an argument:  sorted(items, key=lambda x: x["price"])
   - Day 05: a function can also RETURN another function

4. lambda x: expression → one-line anonymous function for simple use cases.
   Used with sorted(), map(), filter().

5. List  methods: .append(), .extend(), .pop(), .sort(), .reverse(), slice
   Dict  methods: .get(), .items(), .keys(), .values(), .update(), .pop()
   Set   operations: .add(), .discard(), | union, & intersect, - difference
   Tuple: immutable, unpack with a, b = (x, y), pair lists with zip()

CONNECTION TO MODULE 00:
  build_system_prompt() → Module 00 Technique 01 (Prompt Anatomy) in Python
  build_api_request()   → assembles the full API payload the LLM receives
  route_query()         → the routing rules from ## Task, now reusable
  combine_context()     → builds the <context> block from Technique 05 (RAG)

NEXT: Day 04 — File I/O + JSON + String Operations
  Loading system prompts from .txt files at startup.
  Parsing the LLM JSON response string into a Python dict.
"""

print()
print("=" * 60)
print("Day 03 complete.")
print("Next: python modules/day04_file_io_json.py")
print("=" * 60)