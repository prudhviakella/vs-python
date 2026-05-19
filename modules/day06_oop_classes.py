"""
============================================================
Day 06 — OOP Part I: Classes, @property, __repr__, isinstance
============================================================
Module 01 : Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. What is a class? What is an object?
  2. __init__, self — constructor and instance reference
  3. Instance methods
  4. @ decorators — now you know HOFs, @ makes complete sense
  5. @property — computed attributes
  6. __repr__ — what prints when you inspect an object
  7. isinstance() — type checking at runtime
  8. Custom exception classes (one-liners using inheritance)

CONNECTION TO DAY 05:
  In Day 05 you built a retry wrapper (HOF):
    def with_retry(fn): → returns a new function
    @with_retry
    def my_fn(): ...    → @ applies the HOF

  Today: @ is applied to methods inside a class.
  @property is Python's built-in HOF that turns a method
  into a readable attribute.

CONNECTION TO MODULE 00:
  PromptBuilder centralises the 5-section template in one object.
  Instead of assembling prompts as scattered f-strings everywhere,
  one class holds all the prompt logic — testable and versioned.

RUN THIS FILE:
  python modules/day06_oop_classes.py
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

print("=" * 60)
print("DAY 06 — OOP Part I: Classes")
print("=" * 60)


# ============================================================
# SECTION 1 — WHAT IS A CLASS?
# ============================================================

"""
WHAT IS A CLASS?
A class is a BLUEPRINT for creating objects.
An object (instance) is one specific thing built from that blueprint.

int, str, list, dict — these are all classes Python gives you.
  "hello".upper()   → the str CLASS has an upper() method
  [1,2,3].append(4) → the list CLASS has an append() method

Today you build YOUR OWN classes with YOUR OWN methods.

Syntax:
  class ClassName:
      def __init__(self, param1, param2):
          self.param1 = param1   # store on the instance
          self.param2 = param2

Creating an object:
  obj = ClassName(value1, value2)

Calling a method:
  result = obj.some_method()
"""

print()
print("─" * 60)
print("SECTION 1 — class, __init__, self")
print("─" * 60)


# ── SIMPLE — the simplest possible class ─────────────────────

"""
SIMPLE:
__init__ is the constructor — runs when you create an instance.
self refers to the specific instance being created.
self.name = name stores the value ON THAT instance.
"""

class Dog:
    """A simple dog class."""

    def __init__(self, name, breed):
        """Store name and breed on this instance."""
        self.name  = name    # instance variable
        self.breed = breed

    def bark(self):
        """Print a bark."""
        print(f"  {self.name} says: Woof!")

    def describe(self):
        """Return a description string."""
        return f"{self.name} is a {self.breed}"


dog1 = Dog("Rex",   "Labrador")
dog2 = Dog("Buddy", "Poodle")

print()
print("Simple class — two Dog instances:")
print(f"  dog1.name  = {dog1.name}")
print(f"  dog2.name  = {dog2.name}")
print(f"  dog1.describe() = {dog1.describe()}")
dog1.bark()


# ── SHOPSMART — PromptBuilder class ──────────────────────────

"""
SHOPSMART — PromptBuilder encapsulates the 5-section template.

In Day 03 you had build_system_prompt() as a standalone function.
As a class, you can:
  - Build the prompt step by step (add_rule, add_example)
  - Method chain: builder.add_rule("x").add_rule("y")
  - Inspect state: builder.rule_count, builder.char_count
  - Test it in isolation
"""

class PromptBuilder:
    """
    Builds a structured 5-section LLM system prompt.

    Sections (from Module 00 Technique 01):
      ## Role, ## Context, ## Task, ## Output Format, ## Examples
    """

    def __init__(self, role: str, domain: str, output_format: str = "plain text"):
        """
        Args:
            role         : Who the LLM is (specific role + domain)
            domain       : Business context
            output_format: How the LLM should format its response
        """
        self.role          = role
        self.domain        = domain
        self.output_format = output_format
        self._rules        = []    # _ prefix = treat as private
        self._examples     = []

    def add_rule(self, rule: str) -> "PromptBuilder":
        """Add a MUST/MUST NOT rule. Returns self for method chaining."""
        self._rules.append(rule)
        return self   # returning self enables: builder.add_rule("a").add_rule("b")

    def add_example(self, user_input: str, expected_output: str) -> "PromptBuilder":
        """Add a few-shot example pair. Returns self for method chaining."""
        self._examples.append({"input": user_input, "output": expected_output})
        return self

    def render(self) -> str:
        """Build and return the complete system prompt string."""
        rules_block = "\n".join(f"- {r}" for r in self._rules) or "(no rules)"
        examples_block = ""
        for ex in self._examples:
            examples_block += f"Input : {ex['input']}\nOutput: {ex['output']}\n\n"

        return (
            f"## Role\nYou are a {self.role} for {self.domain}.\n\n"
            f"## Task\n{rules_block}\n\n"
            f"## Output Format\n{self.output_format}\n\n"
            f"## Examples\n{examples_block or '(no examples)'}"
        )


builder = PromptBuilder(
    role          = "customer support specialist",
    domain        = "ShopSmart e-commerce",
    output_format = 'JSON: {"category", "confidence", "reason"}',
)
builder.add_rule("You MUST NOT make up order details or prices")
builder.add_rule("You MUST always include the order ID in your response")
builder.add_example(
    "Where is order #3042?",
    '{"category": "TRACK_ORDER", "confidence": "high", "reason": "order location query"}'
)

print()
print("ShopSmart — PromptBuilder:")
print(f"  domain        : {builder.domain}")
print(f"  rules added   : {len(builder._rules)}")
print()
print("  Rendered prompt:")
print(builder.render()[:200] + "...")


# ============================================================
# SECTION 2 — DECORATORS (@ explained properly)
# ============================================================

"""
WHAT DOES @ MEAN?

In Day 05 you learned that a higher-order function:
  - Takes a function as input
  - Returns a NEW function as output

@ is just shorthand for applying a HOF to a function.

  @property
  def char_count(self):
      return len(self.render())

  is EXACTLY the same as:

  def char_count(self):
      return len(self.render())
  char_count = property(char_count)

  property() is a Python built-in HOF that returns a descriptor.
  The descriptor intercepts attribute access (obj.char_count)
  and calls the original function behind the scenes.

EVERY @ you see works the same way:
  @property          → property(fn)
  @classmethod       → classmethod(fn)
  @staticmethod      → staticmethod(fn)
  @app.get("/")      → app.get("/")(fn)   ← FastAPI registers the route
  @field_validator   → field_validator(fn) ← Pydantic validation
"""

print()
print("─" * 60)
print("SECTION 2 — Decorators: @ explained")
print("─" * 60)


# ── SIMPLE — @ is shorthand ───────────────────────────────────

"""
SIMPLE — prove that @ is just shorthand:
"""
def uppercase(fn):
    """HOF from Day 05 — wraps fn to uppercase its return value."""
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs).upper()
    return wrapper


# Without @:
def greet_plain(name):
    return f"hello {name}"
greet_plain = uppercase(greet_plain)   # manual application

# With @:
@uppercase
def greet_decorated(name):
    return f"hello {name}"

print()
print("Simple — @ is just shorthand:")
print(f"  greet_plain('alice')     = '{greet_plain('alice')}'")
print(f"  greet_decorated('alice') = '{greet_decorated('alice')}'")
print(f"  (They are identical — @ just looks cleaner)")


# ============================================================
# SECTION 3 — @property
# ============================================================

"""
@property turns a method into a READ-ONLY attribute.

WITHOUT @property: builder.get_char_count()   ← must write ()
WITH @property:    builder.char_count          ← reads like a variable

USE @property when:
  - The value is computed from other attributes (not stored)
  - Read-only access is correct
  - The name reads better as a noun (char_count, not get_char_count)

DO NOT use @property for expensive operations or side effects.
"""

print()
print("─" * 60)
print("SECTION 3 — @property")
print("─" * 60)


# ── SIMPLE — @property ───────────────────────────────────────

"""
SIMPLE — a Circle class with computed area and perimeter:
"""
import math

class Circle:
    def __init__(self, radius):
        self.radius = radius   # only stored value

    @property
    def area(self):
        """Computed from radius — no () needed when accessing."""
        return round(math.pi * self.radius ** 2, 2)

    @property
    def perimeter(self):
        return round(2 * math.pi * self.radius, 2)


c = Circle(5)
print()
print("Simple — @property:")
print(f"  c.radius    = {c.radius}   (stored)")
print(f"  c.area      = {c.area}   (computed — no ())")
print(f"  c.perimeter = {c.perimeter}   (computed — no ())")


# ── SHOPSMART — @property on PromptBuilder ───────────────────

"""
SHOPSMART — add properties to PromptBuilder:
"""

class PromptBuilderV2(PromptBuilder):
    """PromptBuilder with @property additions."""

    @property
    def char_count(self) -> int:
        """Character count of the rendered prompt."""
        return len(self.render())

    @property
    def rule_count(self) -> int:
        """Number of rules currently added."""
        return len(self._rules)

    @property
    def is_valid(self) -> bool:
        """True if prompt has a role and at least one rule."""
        return bool(self.role) and len(self._rules) >= 1

    def __repr__(self) -> str:
        """
        Controls what print(obj) shows.

        WITHOUT __repr__:
          <__main__.PromptBuilderV2 object at 0x7f3a...>  (useless!)

        WITH __repr__:
          PromptBuilderV2(role='support specialist', rules=2, chars=312)
        """
        return (
            f"PromptBuilderV2("
            f"role={self.role!r}, "      # !r adds quotes around strings
            f"rules={self.rule_count}, "
            f"chars={self.char_count})"
        )


builder2 = PromptBuilderV2(
    role   = "customer support specialist",
    domain = "ShopSmart",
    output_format = 'JSON: {"category", "confidence"}'
)
builder2.add_rule("You MUST NOT invent order details")
builder2.add_rule("You MUST mention the order ID in every response")

print()
print("ShopSmart — @property on PromptBuilderV2:")
print(f"  repr      : {builder2}")           # calls __repr__
print(f"  char_count: {builder2.char_count}") # @property — no ()
print(f"  rule_count: {builder2.rule_count}") # @property — no ()
print(f"  is_valid  : {builder2.is_valid}")   # @property — no ()


# ============================================================
# SECTION 4 — isinstance()
# ============================================================

"""
isinstance(obj, ClassName) → True if obj is an instance of ClassName
                              or any SUBCLASS of ClassName.

Use when a function needs to handle multiple input types.
You will see this everywhere in LangChain source code.

isinstance(obj, SomeClass)      → True for subclasses too ✓
type(obj) == SomeClass          → False for subclasses    ✗
Always prefer isinstance().
"""

print()
print("─" * 60)
print("SECTION 4 — isinstance()")
print("─" * 60)


# ── SIMPLE — isinstance ───────────────────────────────────────

"""
SIMPLE:
"""
values = [42, 3.14, "hello", True, [1, 2], {"key": "val"}]
print()
print("Simple isinstance():")
for v in values:
    print(f"  {str(v):15s} → int:{isinstance(v, int)}  str:{isinstance(v, str)}  list:{isinstance(v, list)}")


# ── SHOPSMART — type dispatch ─────────────────────────────────

"""
SHOPSMART — format a review for an LLM prompt regardless of input type.
This pattern is how LangChain accepts strings, Documents, or dicts.
"""

class ProductReview:
    """A product review from reviews.csv."""
    def __init__(self, review_id, rating, title, text, verified=False):
        if rating not in (1, 2, 3, 4, 5):
            raise ValueError(f"Rating must be 1–5, got: {rating}")
        self.review_id = review_id
        self.rating    = rating
        self.title     = title.strip()
        self.text      = text.strip()
        self.verified  = verified

    @property
    def stars(self) -> str:
        return "★" * self.rating + "☆" * (5 - self.rating)

    @property
    def is_positive(self) -> bool:
        return self.rating >= 4

    def to_context(self) -> str:
        """Format as <context> block for Module 00 Technique 05 (RAG Grounding)."""
        badge = "[Verified] " if self.verified else ""
        return (
            f"<context>\n"
            f"  {self.stars} {badge}{self.title}\n"
            f"  {self.text[:100]}\n"
            f"</context>"
        )

    def __repr__(self) -> str:
        return f"ProductReview(id={self.review_id}, rating={self.rating})"


def format_for_prompt(item) -> str:
    """Handle ProductReview, dict, or str — same output shape."""
    if isinstance(item, ProductReview):
        return item.to_context()

    elif isinstance(item, dict):
        rating = int(item.get("rating", 0))
        stars  = "★" * rating + "☆" * (5 - rating)
        return f"<context>\n  {stars} {item.get('title', 'No title')}\n  {item.get('text', '')[:80]}\n</context>"

    elif isinstance(item, str):
        return f"<context>{item}</context>"

    else:
        raise TypeError(f"Expected ProductReview, dict or str. Got: {type(item).__name__}")


print()
print("ShopSmart — isinstance() type dispatch:")

review = ProductReview(5001, 4, "Really good value", "Works perfectly.", verified=True)
raw_dict = {"rating": "3", "title": "It's fine", "text": "Does the job."}
raw_str  = "Short review text"

for item in [review, raw_dict, raw_str]:
    result = format_for_prompt(item)
    print(f"\n  Input : {type(item).__name__}")
    print(f"  Output: {result[:80]}...")


# ============================================================
# SECTION 5 — CUSTOM EXCEPTION CLASSES
# ============================================================

"""
CUSTOM EXCEPTIONS — simple classes that inherit from Exception.

Now that you know classes, custom exceptions are trivial:
  class LLMError(Exception):
      pass   ← no new methods needed — just a new name

Why create them?
  Built-in: except Exception → you know almost nothing
  Custom:   except LLMRateLimitError → you know exactly what happened

You can also add extra attributes to carry context:
  class LLMRateLimitError(Exception):
      def __init__(self, message, retry_after=1.0):
          super().__init__(message)
          self.retry_after = retry_after
"""

print()
print("─" * 60)
print("SECTION 5 — Custom Exception Classes")
print("─" * 60)


# ── SIMPLE — basic custom exception ──────────────────────────

"""
SIMPLE:
"""
class NegativeNumberError(Exception):
    """Raised when a negative number is provided where positive is required."""
    pass

def sqrt(n):
    if n < 0:
        raise NegativeNumberError(f"Cannot take sqrt of {n}")
    return n ** 0.5

print()
print("Simple — custom exception:")
for n in [4, -9]:
    try:
        print(f"  sqrt({n}) = {sqrt(n)}")
    except NegativeNumberError as e:
        print(f"  NegativeNumberError: {e}")


# ── SHOPSMART — LLM error taxonomy ───────────────────────────

"""
SHOPSMART — the LLM error taxonomy from Module 00 architecture
slides, now as Python custom exception classes.
"""

class LLMError(Exception):
    """Base class for all LLM-related errors. Catch this to handle any LLM error."""
    pass

class LLMRateLimitError(LLMError):
    """HTTP 429 — retryable. retry_after tells you how long to wait."""
    def __init__(self, message: str, retry_after: float = 1.0):
        super().__init__(message)
        self.retry_after = retry_after

class LLMAuthError(LLMError):
    """HTTP 401 — NOT retryable. Fix the API key."""
    pass

class LLMJSONParseError(LLMError):
    """LLM returned invalid JSON — sometimes retryable with a cleaner prompt."""
    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


print()
print("ShopSmart — LLM custom exceptions:")

try:
    raise LLMRateLimitError("HTTP 429: Too Many Requests", retry_after=2.5)
except LLMRateLimitError as e:
    print(f"  LLMRateLimitError: {e}")
    print(f"  retry_after = {e.retry_after}s")
except LLMError as e:
    print(f"  Generic LLMError: {e}")   # catches any LLM subclass

try:
    raise LLMAuthError("HTTP 401: Invalid API key")
except LLMAuthError:
    print(f"  LLMAuthError — NOT retrying, fix the API key")

try:
    raise LLMJSONParseError("LLM returned markdown instead of JSON", raw_response="```python...")
except LLMJSONParseError as e:
    print(f"  LLMJSONParseError: {e}")
    print(f"  raw_response starts with: {e.raw_response[:20]}")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS FROM DAY 06:

1. class defines a blueprint. An instance is one concrete object.
   customer_1 = Customer(1001, "Danielle", ...)

2. __init__(self, ...) runs when you create an instance.
   self.name = name stores the value on THIS specific instance.

3. @ is shorthand for applying a HOF:
   @property
   def char_count(self): ...
   is: char_count = property(char_count)

4. @property turns a method into a read-only attribute.
   obj.char_count  not  obj.char_count()
   Use for computed values that are cheap to calculate.

5. __repr__ controls what print(obj) shows.
   Without it: <ClassName object at 0x...>  (useless)
   With it   : ClassName(key=val, ...)      (useful)

6. isinstance(obj, ClassName) → True for subclasses too.
   Use when a function handles multiple input types.

7. Custom exceptions — one-line classes:
   class LLMRateLimitError(LLMError): pass
   Now you can catch by name and add extra attributes.

NEXT: Day 07 — OOP Part II: Inheritance
  How ResearchAgent extends LLMClient.
  How LangChain's BaseTool, BaseRetriever, BaseMemory work.
  List/dict/set comprehensions.
"""

print()
print("=" * 60)
print("Day 06 complete.")
print("Next: python modules/day07_oop_inheritance.py")
print("=" * 60)
