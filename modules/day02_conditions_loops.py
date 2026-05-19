"""
============================================================
Day 02 — Conditions and Loops
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU KNOW FROM DAY 01:
  - Variables: int, float, str, bool, None
  - Containers: list, dict, set, tuple (first look)
  - f-strings for building prompts

WHAT YOU WILL LEARN TODAY:
  1. if / elif / else      — making decisions in code
  2. Comparison operators  — ==, !=, >, <, >=, <=, in, and, or, not
  3. for loops             — processing collections item by item
  4. enumerate()           — loop with index + value
  5. while loops           — repeating until a condition is met
  6. range()               — generating sequences of numbers
  7. break and continue    — controlling loop flow
  8. List comprehension    — build a list from a loop in one line
  9. Dict comprehension    — build a dict from a loop in one line

CONNECTION TO MODULE 00:
  In Module 00 you wrote routing rules BY HAND in the ## Task section:
    "Route TRACK_ORDER queries to the logistics team."
  Today you write those same routing rules IN PYTHON with if/elif/else.
  Day 03 wraps this logic into a reusable function.
  Day 12 FastAPI calls that function on every incoming HTTP request.

RUN THIS FILE:
  python modules/day02_conditions_loops.py
"""

import time
import random

print("=" * 60)
print("DAY 02 — Conditions and Loops")
print("=" * 60)


# ============================================================
# SECTION 1 — if / elif / else
# ============================================================

"""
A condition is a question your code asks at runtime.
The answer is always True or False.

Syntax:
  if condition:
      runs when condition is True
  elif other_condition:
      runs when the first was False but this is True
  else:
      runs when nothing above matched — the catch-all

Three rules to remember:
  1. Colon : is required at the end of every if / elif / else line
  2. Python checks conditions top to bottom and STOPS at the first match
  3. Always write an else — real data will always surprise you
"""

print()
print("─" * 60)
print("SECTION 1 — if / elif / else")
print("─" * 60)

# Simple — grade from a score
score = 72

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

print()
print(f"Simple — score={score} → grade={grade}")


# ── COMPARISON AND BOOLEAN OPERATORS ─────────────────────────

"""
COMPARISON OPERATORS — produce True or False:

  ==   equal to                 status == "Delivered"
  !=   not equal to             status != "Cancelled"
  >    greater than             rating > 3
  <    less than                price < 100.0
  >=   greater than or equal    rating >= 4
  <=   less than or equal       stock <= 0
  in   substring / membership   "cancel" in query.lower()

BOOLEAN OPERATORS — combine conditions:

  and   both must be True     is_in_stock and is_recommended
  or    at least one True     "cancel" in q or "refund" in q
  not   flip True to False    not is_cancelled
"""

price         = 205.21
stock         = 238
rating        = 4
is_in_stock   = stock > 0
is_affordable = price < 300.0
is_recommended = rating >= 4

print()
print("Comparison + boolean operators:")
print(f"  stock > 0              → {is_in_stock}")
print(f"  price < 300            → {is_affordable}")
print(f"  rating >= 4            → {is_recommended}")

if is_in_stock and is_recommended:
    recommendation = "Great choice — in stock and highly rated!"
elif is_in_stock and not is_recommended:
    recommendation = "In stock but reviews are mixed."
else:
    recommendation = "Out of stock."

print(f"  Recommendation: {recommendation}")


# ── SHOPSMART — query routing (Module 00 ## Task rules in Python)

"""
In Module 00 Technique 01 you wrote:
  "Route TRACK_ORDER queries to the logistics team.
   Route COMPLAINT queries to a senior agent within 2 minutes."

Here those same rules become Python if/elif/else.
Two things to notice:
  - .lower() makes matching case-insensitive ("WHERE" and "where" both match)
  - `in` checks if a word exists inside the query string
  - Most urgent condition goes FIRST — cancel/refund before general tracking
"""

customer_query = "Where is my order #3042?"
q = customer_query.lower()

if "cancel" in q or "refund" in q:
    agent   = "human_agent"
    urgency = "high"
elif "track" in q or "where" in q or "delivery" in q:
    agent   = "order_agent"
    urgency = "normal"
elif "return" in q or "exchange" in q:
    agent   = "returns_agent"
    urgency = "normal"
elif "price" in q or "discount" in q or "coupon" in q:
    agent   = "promotions_agent"
    urgency = "normal"
elif "product" in q or "review" in q or "spec" in q:
    agent   = "catalog_agent"
    urgency = "low"
else:
    agent   = "general_agent"
    urgency = "normal"

print()
print("ShopSmart — query routing:")
print(f"  Query   : '{customer_query}'")
print(f"  Agent   : {agent}")
print(f"  Urgency : {urgency}")


# ── SHOPSMART — mapping database status to customer message ───

"""
Real order statuses from orders.csv:
  Delivered · In Transit · Processing · Pending · Cancelled · Refunded

The else at the end handles any unexpected value from the database.
Real data is messy — you will always encounter a value you didn't expect.
"""

print()
print("ShopSmart — status → customer message:")

for status in ["Delivered", "In Transit", "Cancelled", "Refunded", "Unknown"]:
    if status == "Delivered":
        msg = "Your order has been delivered."
    elif status == "In Transit":
        msg = "Your order is on its way."
    elif status == "Processing":
        msg = "Your order is being prepared."
    elif status == "Pending":
        msg = "Your order is confirmed and waiting."
    elif status == "Cancelled":
        msg = "Your order has been cancelled."
    elif status == "Refunded":
        msg = "Your refund has been processed."
    else:
        msg = f"Status '{status}' — please contact support."

    print(f"  '{status:12s}' → '{msg}'")


# ============================================================
# SECTION 2 — for LOOPS
# ============================================================

"""
A for loop runs a block of code once for each item in a sequence.

Syntax:
  for item in collection:
      do something with item

The loop variable (item) takes the value of each item in turn.
When there are no more items the loop ends automatically.

for vs while:
  for   — use when you know the collection in advance
  while — use when you don't know how many iterations you need
"""

print()
print("─" * 60)
print("SECTION 2 — for loops")
print("─" * 60)


# Simple — loop over a list of strings
fruits = ["apple", "banana", "cherry"]

print()
print("Simple — loop over a list:")
for fruit in fruits:
    print(f"  {fruit}")


# enumerate() gives both the index AND the value in one call.
# Without it: for item in items       → value only
# With it:    for i, item in enumerate(items) → index + value
print()
print("Simple — enumerate() (index + value):")
for i, fruit in enumerate(fruits):
    print(f"  [{i}] {fruit}")


# ── SHOPSMART — process a batch of customer queries ───────────

"""
In production this loop calls the LLM for each query.
Here it uses keyword routing to demonstrate the pattern.
The same loop structure handles 5 queries or 50,000.

Accumulation pattern (used everywhere in Python):
  results = []              ← start with an empty list
  for item in collection:
      results.append(...)   ← add one result per iteration
"""

test_queries = [
    "Where is my order #3042?",
    "I want to cancel my purchase",
    "Do you have a discount code?",
    "What are the specs of the Classic Monitor?",
    "My package hasn't arrived yet",
]

results = []
print()
print("ShopSmart — routing a batch of queries:")

for i, query in enumerate(test_queries):
    q = query.lower()
    if   "cancel" in q or "refund"   in q: agent = "human_agent"
    elif "track"  in q or "where"    in q: agent = "order_agent"
    elif "return" in q or "exchange" in q: agent = "returns_agent"
    elif "price"  in q or "discount" in q: agent = "promotions_agent"
    elif "product" in q or "spec"    in q: agent = "catalog_agent"
    else:                                   agent = "general_agent"

    results.append({"index": i, "query": query, "agent": agent})
    print(f"  [{i}] {query[:40]:40s} → {agent}")


# ── SHOPSMART — loop over a list of dicts ────────────────────

"""
Data loaded from CSV files comes as a list of dicts.
Each dict is one row — the keys are the column names.
Every row has the same set of keys.
"""

reviews = [
    {"review_id": 5001, "rating": 3, "title": "Its fine"},
    {"review_id": 5002, "rating": 5, "title": "Excellent!"},
    {"review_id": 5003, "rating": 4, "title": "Really good"},
    {"review_id": 5004, "rating": 2, "title": "Disappointed"},
]

print()
print("ShopSmart — loop over review dicts:")
for review in reviews:
    stars = "★" * review["rating"] + "☆" * (5 - review["rating"])
    print(f"  ID:{review['review_id']} | {stars} | {review['title']}")


# ============================================================
# SECTION 3 — range()
# ============================================================

"""
range() generates a sequence of integers — nothing is stored in memory
until you actually loop over it. Three forms:

  range(stop)            → 0, 1, 2, ..., stop-1
  range(start, stop)     → start, start+1, ..., stop-1
  range(start, stop, step) → every step-th value from start to stop-1

Use range() when:
  - You need to loop exactly N times
  - You need the index position to do arithmetic
"""

print()
print("─" * 60)
print("SECTION 3 — range()")
print("─" * 60)

print()
print("range() forms:")
print(f"  range(5)        → {list(range(5))}")
print(f"  range(1, 6)     → {list(range(1, 6))}")
print(f"  range(0, 10, 2) → {list(range(0, 10, 2))}")

# ShopSmart — split 9 queries into batches of 3
total_queries = 9
batch_size    = 3

print()
print("ShopSmart — batch processing with range():")
for batch_num in range(total_queries // batch_size):
    start = batch_num * batch_size
    end   = start + batch_size
    print(f"  Batch {batch_num + 1}: queries {start} to {end - 1}")


# ============================================================
# SECTION 4 — while LOOPS
# ============================================================

"""
A while loop runs AS LONG AS its condition is True.
When the condition becomes False the loop ends.

  while condition:
      do something
      update what the condition checks   ← if you forget this → infinite loop

The critical difference from for:
  for   — the collection decides how many times you iterate
  while — you control when to stop with a condition
  Use while when the number of iterations is not known in advance.
"""

print()
print("─" * 60)
print("SECTION 4 — while loops")
print("─" * 60)

# Simple — count up to 4
count = 0
print()
print("Simple while loop (count to 4):")
while count < 5:
    print(f"  count = {count}")
    count += 1      # update the condition — without this → infinite loop
print(f"  loop ended, final count = {count}")


# ── SHOPSMART — retry loop with exponential backoff ───────────

"""
LLM APIs return HTTP 429 (Too Many Requests) when you call them too fast.
The correct response is to wait and retry — not to crash.

Exponential backoff: each wait is DOUBLE the previous one.
  Attempt 1 fails → wait 0.1s
  Attempt 2 fails → wait 0.2s
  Attempt 3 fails → wait 0.4s
  ...
This prevents hammering the API and gets you unblocked faster.

while is the right tool here because you don't know in advance
how many attempts will be needed before a success.
"""

random.seed(42)

query       = "Where is order #3042?"
max_retries = 4
attempt     = 0
response    = None
last_error  = None

print()
print("ShopSmart — retry with exponential backoff:")

while attempt < max_retries:
    print(f"  Attempt {attempt + 1}/{max_retries}...")

    if attempt < 2:                          # first two attempts fail
        last_error   = "HTTP 429: Rate limit exceeded"
        wait_seconds = 0.1 * (2 ** attempt)  # 0.1s, 0.2s, 0.4s ...
        print(f"    FAILED  — {last_error}")
        print(f"    Waiting {wait_seconds:.1f}s before retry...")
        time.sleep(wait_seconds)
        attempt += 1
        continue                             # skip rest, go back to while

    response = "[LLM] Order #3042 is In Transit, arriving Friday."
    print(f"    SUCCESS on attempt {attempt + 1}")
    break                                    # exit the loop immediately

if response:
    print(f"  Final: {response}")
else:
    print(f"  All {max_retries} attempts failed. Last error: {last_error}")


# ============================================================
# SECTION 5 — break AND continue
# ============================================================

"""
break and continue let you control a loop's flow mid-iteration.

  break    → exit the loop entirely right now
  continue → skip the rest of THIS iteration, jump to the next one

Mental model:
  break    = "I am done — stop the loop"
  continue = "Not this one — skip it and move on"
"""

print()
print("─" * 60)
print("SECTION 5 — break and continue")
print("─" * 60)

# Simple continue — skip even numbers
print()
print("Simple continue — print only odd numbers:")
for n in range(1, 9):
    if n % 2 == 0:
        continue           # even → skip
    print(f"  {n}", end=" ")
print()

# Simple break — stop at first number above 5
print()
print("Simple break — stop when n > 5:")
for n in range(1, 10):
    if n > 5:
        print(f"  → stopped at {n}")
        break
    print(f"  {n}", end=" ")
print()

# ShopSmart — collect exactly 3 high-rated reviews for a few-shot prompt
# In Module 00 Technique 02 you picked few-shot examples manually.
# Here Python selects them automatically:
#   continue → skip reviews with rating < 4
#   break    → stop once we have 3 collected

all_reviews = [
    {"review_id": 5001, "rating": 3, "title": "Its fine"},
    {"review_id": 5002, "rating": 5, "title": "Excellent!"},
    {"review_id": 5003, "rating": 4, "title": "Really good"},
    {"review_id": 5004, "rating": 2, "title": "Disappointed"},
    {"review_id": 5005, "rating": 5, "title": "Perfect product"},
    {"review_id": 5006, "rating": 4, "title": "Solid choice"},
    {"review_id": 5007, "rating": 1, "title": "Terrible"},
]

good_reviews   = []
max_to_collect = 3

print()
print("ShopSmart — auto-select 3 few-shot examples (break + continue):")

for review in all_reviews:
    if review["rating"] < 4:
        print(f"  SKIP  {review['review_id']} (rating={review['rating']})")
        continue                      # below threshold → skip

    good_reviews.append(review)
    stars = "★" * review["rating"] + "☆" * (5 - review["rating"])
    print(f"  KEEP  {review['review_id']} {stars} {review['title']}")

    if len(good_reviews) >= max_to_collect:
        print(f"  BREAK — {max_to_collect} collected, done")
        break                         # enough examples → stop

print(f"\n  Selected: {[r['title'] for r in good_reviews]}")


# ============================================================
# SECTION 6 — LIST COMPREHENSION
# ============================================================

"""
A list comprehension builds a list from a loop in ONE LINE.
It is not a new concept — it is a cleaner way to write the
accumulation pattern you already know:

  # Standard loop (what you've been writing):
  results = []
  for item in collection:
      if condition:
          results.append(transform(item))

  # List comprehension — same thing, one line:
  results = [transform(item) for item in collection if condition]

Three parts:
  [  WHAT TO PRODUCE   for ITEM in COLLECTION   if CONDITION  ]
       ↑                       ↑                      ↑
   expression           the loop variable         optional filter

The if condition is optional — leave it out if you want every item.

When to use comprehensions vs regular loops:
  Comprehension → simple transform or filter on one collection
  Regular loop  → complex logic, multiple steps, side effects
"""

print()
print("─" * 60)
print("SECTION 6 — List Comprehension")
print("─" * 60)


# ── Simple — squares of 1 to 5 ───────────────────────────────

# Standard loop version (Day 02 Section 2 pattern):
squares_loop = []
for n in range(1, 6):
    squares_loop.append(n * n)

# List comprehension — identical result, one line:
squares_comp = [n * n for n in range(1, 6)]

print()
print("Simple — squares with loop vs comprehension:")
print(f"  loop         : {squares_loop}")
print(f"  comprehension: {squares_comp}")
print(f"  same result  : {squares_loop == squares_comp}")


# ── Simple — filter even numbers ─────────────────────────────

numbers  = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
evens    = [n for n in numbers if n % 2 == 0]
print()
print(f"Simple — filter evens from {numbers}:")
print(f"  [n for n in numbers if n % 2 == 0] → {evens}")


# ── Simple — transform strings ────────────────────────────────

words     = ["hello", "world", "python"]
uppercase = [w.upper() for w in words]
print()
print(f"Simple — uppercase each word in {words}:")
print(f"  [w.upper() for w in words] → {uppercase}")


# ── ShopSmart — filter in-stock products ─────────────────────

"""
In production this comes from a database query.
The list comprehension applies a filter in one readable line.
"""

products = [
    {"name": "Classic Monitor",   "price": 205.21, "stock": 238},
    {"name": "Ultimate Perfume",  "price": 568.17, "stock": 10},
    {"name": "Budget Headphones", "price": 29.99,  "stock": 0},
    {"name": "Yoga Mat Pro",      "price": 45.00,  "stock": 150},
    {"name": "Luxury Cream",      "price": 89.00,  "stock": 0},
]

# Filter: only products where stock > 0
in_stock = [p for p in products if p["stock"] > 0]

print()
print("ShopSmart — in-stock products (filter comprehension):")
for p in in_stock:
    print(f"  {p['name']:25s} stock={p['stock']}")


# ── ShopSmart — extract just the names ───────────────────────

# Transform: pull out one field from every dict
names = [p["name"] for p in products]
print()
print("ShopSmart — extract product names (transform comprehension):")
print(f"  {names}")


# ── ShopSmart — filter + transform together ───────────────────

# Filter to affordable AND in-stock, then format as a prompt line
prompt_lines = [
    f"- {p['name']} (${p['price']:.2f})"
    for p in products
    if p["stock"] > 0 and p["price"] < 300
]

print()
print("ShopSmart — affordable in-stock items formatted for LLM prompt:")
for line in prompt_lines:
    print(f"  {line}")


# ── ShopSmart — high-rated review titles ─────────────────────

high_rated_titles = [
    r["title"]
    for r in all_reviews
    if r["rating"] >= 4
]

print()
print("ShopSmart — titles of 4★+ reviews for few-shot examples:")
print(f"  {high_rated_titles}")


# ============================================================
# SECTION 7 — DICT COMPREHENSION
# ============================================================

"""
A dict comprehension builds a dict from a loop in one line.
Same idea as list comprehension — but produces key-value pairs.

Syntax:
  {key_expr: value_expr for item in collection if condition}

When is this useful?
  You have a list and you want to build a fast lookup dict from it.
  Instead of searching the list every time (slow, O(n)),
  you build a dict keyed by ID and look up in O(1).
"""

print()
print("─" * 60)
print("SECTION 7 — Dict Comprehension")
print("─" * 60)


# ── Simple — number to its square ────────────────────────────

squares_dict = {n: n * n for n in range(1, 6)}

print()
print("Simple — number to its square:")
print(f"  {{n: n*n for n in range(1, 6)}} → {squares_dict}")
print(f"  squares_dict[3] = {squares_dict[3]}   ← instant lookup by key")


# ── Simple — word to its length ──────────────────────────────

words       = ["apple", "banana", "cherry", "date"]
word_lengths = {w: len(w) for w in words}

print()
print(f"Simple — word to its length from {words}:")
print(f"  {word_lengths}")


# ── ShopSmart — product lookup index ─────────────────────────

"""
When the LLM agent calls the "lookup_product" tool with a product_id,
you need to find that product instantly.

Searching a list every time is O(n) — slows as the list grows.
A dict keyed by product_id is O(1) — instant regardless of size.

Build the index once from the list using a dict comprehension.
"""

product_index = {p["name"]: p for p in products}

print()
print("ShopSmart — product lookup index (dict comprehension):")
print(f"  Keys: {list(product_index.keys())}")
classic = product_index["Classic Monitor"]
print(f"  product_index['Classic Monitor'] → price=${classic['price']}, stock={classic['stock']}")


# ── ShopSmart — agent routing result as dict ─────────────────

"""
Turn the routing results from Section 2 into a query→agent lookup dict.
Now you can instantly find which agent was assigned to any query.
"""

routing_index = {r["query"]: r["agent"] for r in results}

print()
print("ShopSmart — routing results as lookup dict:")
for query, agent in list(routing_index.items())[:3]:
    print(f"  '{query[:35]:35s}' → {agent}")


# ── ShopSmart — review ratings by ID ─────────────────────────

ratings_by_id = {r["review_id"]: r["rating"] for r in all_reviews}

print()
print("ShopSmart — review ratings by ID:")
print(f"  {ratings_by_id}")
print(f"  ratings_by_id[5002] = {ratings_by_id[5002]}   ← instant lookup")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 02:

1. if / elif / else — run different code based on a condition.
   Check most urgent conditions FIRST. Always write else.
   Use `in` to check substrings: "cancel" in query.lower()

2. for loop — repeat for each item in a collection.
   enumerate() gives index + value in one call.
   Accumulation pattern: results = [] → append inside loop.

3. while loop — repeat until condition is False.
   ALWAYS update what the condition checks — or infinite loop.
   Use when number of iterations is not known in advance (retry).

4. range(n) → 0, 1, ..., n-1
   range(start, stop, step) for full control.

5. break  → exit the loop entirely now.
   continue → skip this iteration, move to next.

6. List comprehension — one-line loop that builds a list:
   [expr for item in collection if condition]
   Use for simple transforms and filters. Regular loop for complex logic.

7. Dict comprehension — one-line loop that builds a dict:
   {key: value for item in collection if condition}
   Use to build a fast O(1) lookup index from a list.

CONNECTION TO MODULE 00:
  if/elif/else → the routing rules from ## Task section, now in Python
  while + retry → how production LLM services handle HTTP 429
  List comprehension → filtering search results before injecting into prompt
  Dict comprehension → building lookup indexes for tool calls in agents

NEXT: Day 03 — Functions and Data Structures
  Wrapping today's routing logic into a reusable function.
  *args, **kwargs, sorted(), map(), filter().
  Deep dive into all list, dict, set, tuple methods.
"""

print()
print("=" * 60)
print("Day 02 complete.")
print("Next: python modules/day03_functions_data_structures.py")
print("=" * 60)