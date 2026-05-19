"""
============================================================
Day 05 — Exception Handling + logging + Higher-Order Functions
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. try / except / else / finally
  2. Specific exception types to catch
  3. raise — create your own errors
  4. logging module — replace print() with proper logging
  5. Higher-order functions — function that takes/returns a function
  6. Building a retry wrapper as the natural HOF example

WHY HIGHER-ORDER FUNCTIONS TODAY?
  Day 06 teaches decorators (@property, @classmethod, @app.get).
  Decorators ARE higher-order functions — just with @ syntax.
  You cannot understand what @ means without this foundation.
  The retry wrapper you build here IS a decorator — naked form.

CONNECTION TO MODULE 00:
  LLM APIs return HTTP 429 (rate limit) — you must retry.
  LLM APIs return malformed JSON — you must handle JSONDecodeError.
  logging goes to CloudWatch in production (not print() which goes nowhere).

RUN THIS FILE:
  python modules/day05_exception_handling_logging.py
"""

import json
import logging
import time
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

print("=" * 60)
print("DAY 05 — Exception Handling + logging + Higher-Order Functions")
print("=" * 60)


# ============================================================
# SECTION 1 — THE logging MODULE
# ============================================================

"""
WHY logging INSTEAD OF print()?

print("something happened")     ← always runs, no level, no context

logging.info("LLM call started") ← only shows if level >= INFO
logging.error("API call failed") ← always shows (ERROR is high)

FIVE LEVELS (lowest → highest):
  DEBUG    → detailed dev info
  INFO     → normal operations
  WARNING  → unexpected but recoverable
  ERROR    → something failed
  CRITICAL → service is broken

In production you set level=INFO — DEBUG is invisible.
In development you set level=DEBUG — see everything.

In a container (ECS Fargate from our platform), print() goes nowhere.
logging goes to CloudWatch automatically via the log driver.
"""

logging.basicConfig(
    level  = logging.DEBUG,
    format = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
)

log = logging.getLogger(__name__)

print()
print("─" * 60)
print("SECTION 1 — logging levels")
print("─" * 60)
print()
log.debug("DEBUG   — only in development (level=DEBUG)")
log.info("INFO    — normal operation: LLM call started")
log.warning("WARNING — something unexpected: retry attempt 2/3")
log.error("ERROR   — operation failed: JSON parse error")


# ============================================================
# SECTION 2 — EXCEPTIONS
# ============================================================

"""
WHAT IS AN EXCEPTION?
An error that stops normal program execution.
When Python can't do what you asked, it "raises" an exception.
If you don't handle it, the program crashes.

COMMON EXCEPTION TYPES IN LLM ENGINEERING:
  FileNotFoundError  → open() on missing file
  KeyError           → dict["missing_key"]
  ValueError         → int("abc") — wrong type
  IndexError         → my_list[999] — out of bounds
  json.JSONDecodeError → json.loads("not json")
  ConnectionError    → API unreachable
  TimeoutError       → API too slow
"""

print()
print("─" * 60)
print("SECTION 2 — Exception types")
print("─" * 60)


# ── SIMPLE — KeyError ────────────────────────────────────────

"""
SIMPLE:
"""
data = {"name": "Alice"}
try:
    value = data["phone"]   # key doesn't exist
except KeyError as e:
    print(f"\nSimple KeyError: missing key {e}")


# ── SIMPLE — ValueError ──────────────────────────────────────

"""
SIMPLE:
"""
try:
    number = int("abc")
except ValueError as e:
    print(f"Simple ValueError: {e}")


# ── SIMPLE — json.JSONDecodeError ────────────────────────────

"""
SIMPLE:
"""
try:
    parsed = json.loads("this is not json")
except json.JSONDecodeError as e:
    print(f"Simple JSONDecodeError: {e}")


# ── SHOPSMART — FileNotFoundError ────────────────────────────

"""
SHOPSMART — loading a prompt file that might not exist:
"""
print()
print("ShopSmart — FileNotFoundError:")
try:
    with open(BASE_DIR / "prompts" / "system_prompt.txt", encoding="utf-8") as f:
        prompt = f.read().strip()
    log.info(f"Loaded system prompt ({len(prompt)} chars)")
    print(f"  Loaded: {len(prompt)} chars")
except FileNotFoundError as e:
    log.warning(f"Prompt file not found: {e}")
    prompt = "You are a helpful customer support agent."
    print(f"  File missing — using default prompt")


# ============================================================
# SECTION 3 — try / except / else / finally
# ============================================================

"""
FULL EXCEPTION HANDLING PATTERN:

  try:
      risky code
  except SpecificError as e:
      handle that specific error
  except AnotherError as e:
      handle this other error
  else:
      runs ONLY if NO exception occurred in try
  finally:
      ALWAYS runs — whether exception happened or not

  else   → post-success validation
  finally → cleanup: close files, log timing, release resources
"""

print()
print("─" * 60)
print("SECTION 3 — try / except / else / finally")
print("─" * 60)


# ── SIMPLE — full pattern ─────────────────────────────────────

"""
SIMPLE — dividing numbers with full exception handling:
"""
def safe_divide(a, b):
    """Divide a by b — handles ZeroDivisionError."""
    try:
        result = a / b
    except ZeroDivisionError as e:
        print(f"  Cannot divide by zero: {e}")
        return None
    else:
        print(f"  {a} / {b} = {result}")
        return result
    finally:
        print(f"  (finally block always runs)")

print()
print("Simple — try/except/else/finally:")
safe_divide(10, 2)
print()
safe_divide(10, 0)


# ── SHOPSMART — parsing LLM JSON with full handling ──────────

"""
SHOPSMART — the exact pattern for parsing LLM responses.
"""
def parse_llm_json(raw: str, expected_fields: list) -> dict:
    """
    Parse an LLM JSON response with full error handling.
    Handles markdown fences, JSONDecodeError, missing fields.
    """
    import time as _time
    start = _time.perf_counter()
    parsed = {}

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(cleaned)
        log.info(f"JSON parsed: {list(parsed.keys())}")

    except json.JSONDecodeError as e:
        log.error(f"LLM returned invalid JSON: {e}")
        log.error(f"Raw response: {raw[:100]}")
        raise   # re-raise — caller must handle this

    else:
        # Runs only if no exception — validate expected fields
        missing = [f for f in expected_fields if f not in parsed]
        if missing:
            log.warning(f"LLM response missing fields: {missing}")

    finally:
        elapsed = round((_time.perf_counter() - start) * 1000, 1)
        log.debug(f"parse_llm_json() finished in {elapsed}ms")

    return parsed


print()
print("ShopSmart — parse_llm_json():")

test_cases = [
    ('{"category": "TRACK_ORDER", "confidence": "high", "reason": "order query"}',
     ["category", "confidence", "reason"]),
    ('```json\n{"category": "BILLING"}\n```',
     ["category", "confidence"]),   # missing "confidence"
]

for raw, fields in test_cases:
    try:
        result = parse_llm_json(raw, fields)
        print(f"  Parsed: {result}")
    except json.JSONDecodeError:
        print(f"  Failed to parse")


# ============================================================
# SECTION 4 — raise
# ============================================================

"""
raise — create your own error and stop execution intentionally.

WHY?
When you detect a problem early, it is better to fail loudly
than to continue with bad data and produce a silent wrong answer.

You can raise any built-in exception with a custom message.
In Day 06 you will create custom exception CLASSES.
"""

print()
print("─" * 60)
print("SECTION 4 — raise")
print("─" * 60)


# ── SIMPLE — raise ───────────────────────────────────────────

"""
SIMPLE:
"""
def check_age(age):
    if age < 0:
        raise ValueError(f"Age cannot be negative: {age}")
    if age > 150:
        raise ValueError(f"Age {age} is unrealistic")
    return f"Valid age: {age}"

print()
print("Simple — raise:")
for age in [25, -5, 200]:
    try:
        print(f"  {check_age(age)}")
    except ValueError as e:
        print(f"  ValueError: {e}")


# ── SHOPSMART — validate API key before use ──────────────────

"""
SHOPSMART — fail fast before the LLM call rather than getting
a confusing HTTP 401 thirty seconds later.
"""
def validate_api_key(key: str) -> str:
    """Validate API key format before making the LLM call."""
    if not key:
        raise ValueError("API key is empty — set OPENAI_API_KEY in .env")
    if not key.startswith("sk-"):
        raise ValueError(f"API key format wrong (expected 'sk-...'): {key[:8]}...")
    if len(key) < 20:
        raise ValueError(f"API key too short ({len(key)} chars) — check .env")
    return key

print()
print("ShopSmart — validate_api_key():")
test_keys = ["", "not-a-key", "sk-short", "sk-" + "x" * 45]
for key in test_keys:
    try:
        valid = validate_api_key(key)
        print(f"  VALID: sk-...{valid[-4:]}")
    except ValueError as e:
        print(f"  ERROR: {e}")


# ============================================================
# SECTION 5 — HIGHER-ORDER FUNCTIONS
# ============================================================

"""
HIGHER-ORDER FUNCTION: a function that either:
  - Takes a function as an argument  (sorted key=, map, filter)
  - Returns a function as its result  ← NEW TODAY

You already saw the first type in Day 03 (sorted, map, filter).
Today you learn the second type — which is what makes decorators possible.

WHY IS THIS IMPORTANT?
A decorator (@property, @app.get, @field_validator) is JUST
a higher-order function called with @ syntax.

Before you see @, you need to understand:
  fn = some_wrapper(fn)    ← the @ line does exactly this

MENTAL MODEL:
  @with_retry
  def call_llm(prompt): ...

  is EXACTLY the same as:

  def call_llm(prompt): ...
  call_llm = with_retry(call_llm)
"""

print()
print("─" * 60)
print("SECTION 5 — Higher-Order Functions")
print("─" * 60)


# ── SIMPLE — function that returns a function ─────────────────

"""
SIMPLE — the naked concept:
A function that returns another function.
"""
def make_multiplier(factor):
    """
    Takes a number (factor) as input.
    Returns a NEW FUNCTION that multiplies its argument by factor.
    """
    def multiply(x):
        return x * factor
    return multiply   # return the FUNCTION OBJECT (no parentheses)


double = make_multiplier(2)   # double is now a function
triple = make_multiplier(3)   # triple is now a function

print()
print("Simple — function returning a function:")
print(f"  make_multiplier(2) → double function")
print(f"  double(5)  = {double(5)}")
print(f"  triple(5)  = {triple(5)}")


# ── SIMPLE — wrapper function (the decorator shape) ──────────

"""
SIMPLE — a wrapper that adds behaviour around any function:

This is THE pattern of a decorator — stripped to its bare form.
"""
def shout(fn):
    """
    Higher-order function:
      INPUT  → a function fn
      OUTPUT → a NEW function that calls fn and uppercases the result
    """
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)   # call the original function
        return result.upper()          # add behaviour: uppercase
    return wrapper                     # return the new wrapper function

def greet(name):
    return f"hello, {name}"

# Manual way to use the wrapper
louder_greet = shout(greet)

print()
print("Simple — wrapper function (decorator shape):")
print(f"  greet('alice')        = '{greet('alice')}'")
print(f"  louder_greet('alice') = '{louder_greet('alice')}'")

# @ syntax does EXACTLY the same thing:
@shout
def greet_loud(name):
    return f"hello, {name}"

print(f"  @shout greet_loud('bob') = '{greet_loud('bob')}'")
print(f"  (@ is just: greet_loud = shout(greet_loud))")


# ── SHOPSMART — retry wrapper as a higher-order function ──────

"""
SHOPSMART — the most useful HOF in LLM engineering.

Takes any function and returns a new version of it
that automatically retries on ConnectionError or TimeoutError.

This works for ANY function — not just LLM calls.
"""

def with_retry(fn, max_retries: int = 3, backoff: float = 0.5):
    """
    Higher-order function:
      INPUT  → any function fn
      OUTPUT → a new function that retries fn on failure

    The returned wrapper:
      - calls fn
      - on ConnectionError or TimeoutError: waits and retries
      - on success: returns the result immediately
      - after max_retries: raises the last error
    """
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(max_retries):
            try:
                log.info(f"Attempt {attempt + 1}/{max_retries}: {fn.__name__}()")
                return fn(*args, **kwargs)   # call the original function

            except (ConnectionError, TimeoutError) as e:
                last_error = e
                wait = backoff * (2 ** attempt)   # exponential: 0.5, 1.0, 2.0
                log.warning(f"  Failed: {e}. Waiting {wait:.1f}s...")
                time.sleep(wait)

        raise last_error   # all retries exhausted

    return wrapper


# Simulate an LLM API call that succeeds on the 3rd attempt
random.seed(42)
call_count = [0]

def call_llm_api(prompt: str) -> str:
    """Simulated LLM API call — fails first 2 attempts."""
    call_count[0] += 1
    if call_count[0] < 3:
        raise ConnectionError("HTTP 429: Rate limit exceeded")
    return f"[LLM] Response to: {prompt[:30]}..."


# Wrap it manually (same as using @ decorator)
call_llm_safe = with_retry(call_llm_api, max_retries=4, backoff=0.1)

print()
print("ShopSmart — with_retry() HOF:")
try:
    response = call_llm_safe("Where is order #3042?")
    print(f"  Final response: {response}")
except ConnectionError as e:
    print(f"  All retries failed: {e}")


# ── SHOPSMART — retry using @ decorator syntax ────────────────

"""
SHOPSMART — using @ syntax for the same result:
"""

def with_retry_decorator(max_retries=3, backoff=0.5):
    """
    Decorator factory — returns a decorator.
    This lets you write: @with_retry_decorator(max_retries=4)
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_error = e
                    wait = backoff * (2 ** attempt)
                    time.sleep(wait)
            raise last_error
        return wrapper
    return decorator


@with_retry_decorator(max_retries=3, backoff=0.1)
def parse_json_response(raw: str) -> dict:
    """Parse a JSON response — retries if the format is temporarily broken."""
    return json.loads(raw)


print()
print("ShopSmart — @with_retry_decorator syntax:")
try:
    result = parse_json_response('{"category": "TRACK_ORDER"}')
    print(f"  Parsed: {result}")
except Exception as e:
    print(f"  Failed: {e}")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 05:

1. try / except / else / finally:
   try     → run risky code
   except  → handle specific errors (always name the type)
   else    → runs only if try succeeded
   finally → ALWAYS runs (cleanup, timing)

2. raise ValueError("message") → fail fast with a clear message
   Use it when you detect a problem early to prevent bad data
   from silently propagating through your system.

3. logging > print() in production:
   log = logging.getLogger(__name__)
   log.info() / log.warning() / log.error()
   Goes to CloudWatch — print() goes nowhere in a container.

4. Higher-order functions:
   A function that TAKES a function → sorted(key=fn), map, filter
   A function that RETURNS a function → the decorator pattern

5. The decorator pattern (naked form):
   def wrapper(fn):
       def inner(*args, **kwargs):
           return fn(*args, **kwargs)   # + extra behaviour
       return inner

   @wrapper
   def my_fn(): ...
   # is EXACTLY: my_fn = wrapper(my_fn)

DAY 06 PREVIEW:
  Now that you know HOFs, @property makes complete sense:
    @property
    def char_count(self):
        return len(self.render())
  is: char_count = property(char_count)
  property() is a built-in that returns a descriptor object.

NEXT: Day 06 — OOP Part I: Classes
  Decorators explained. @property, @classmethod, isinstance.
"""

print()
print("=" * 60)
print("Day 05 complete.")
print("Next: python modules/day06_oop_classes.py")
print("=" * 60)
