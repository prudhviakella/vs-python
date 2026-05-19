"""
============================================================
Day 07 — OOP Part II: Inheritance + Comprehensions
============================================================
Module 01: Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. Inheritance — one class extends another
  2. super()     — call the parent class's method
  3. Method override — replace a parent method in a child class
  4. @classmethod — brief mention (you see it in LangChain)
  5. ABC          — brief mention (you see it in LangChain)
  6. List comprehension — [x for x in items if condition]
  7. Dict comprehension — {k: v for k, v in items}

WHY THIS MATTERS:
  Every LangChain agent is a class that inherits from BaseTool or
  BaseRetriever. Understanding inheritance means you can read and
  write LangChain components confidently.
  Comprehensions replace 5-line for loops with 1 readable line.

RUN THIS FILE:
  python modules/day07_oop_inheritance.py
"""

import logging
from abc import ABC, abstractmethod   # ABC — brief intro below

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

print("=" * 60)
print("DAY 07 — OOP II: Inheritance + Comprehensions")
print("=" * 60)


# ============================================================
# SECTION 1 — INHERITANCE
# ============================================================

"""
WHAT IS INHERITANCE?
Inheritance lets one class EXTEND another class.
The child class gets all the methods of the parent class for free,
and can add new methods or replace (override) existing ones.

SYNTAX:
  class Child(Parent):
      pass   ← Child inherits everything from Parent

REAL EXAMPLE FROM THIS COURSE:
  BaseLLMClient              ← defines the interface (call, get_model)
    └── OpenAIClient         ← implements call() for OpenAI API
          └── ResearchAgent  ← overrides call() to add RAG search first

This is exactly the structure in LangChain:
  BaseLanguageModel
    └── BaseChatModel
          └── ChatOpenAI

WHY INHERIT?
  - Avoid repeating shared logic (write once in the parent)
  - Guarantee a consistent interface (all clients have call())
  - Swap implementations easily (switch OpenAI → Anthropic)
"""

print()
print("─" * 60)
print("SECTION 1 — Inheritance and super()")
print("─" * 60)


class LLMClient:
    """
    Base LLM client — shared config and the token estimate utility.

    Child classes (OpenAIClient, AnthropicClient) inherit these for free.
    They only need to implement call() and get_model_name().
    """

    def __init__(self, max_tokens=512, temperature=0.2):
        """Store config shared by all LLM clients."""
        self.max_tokens  = max_tokens
        self.temperature = temperature

    def count_tokens_estimate(self, text: str) -> int:
        """Rough estimate: 1 token ≈ 4 characters in English."""
        return len(text) // 4

    def call(self, prompt: str) -> str:
        """Send a prompt. Child classes must override this."""
        raise NotImplementedError("Subclasses must implement call()")

    def get_model_name(self) -> str:
        """Return the model identifier. Child classes must override this."""
        raise NotImplementedError("Subclasses must implement get_model_name()")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"model={self.get_model_name()!r}, "
            f"max_tokens={self.max_tokens})"
        )


class OpenAIClient(LLMClient):
    """
    LLM client for OpenAI models.

    Inherits __init__ config and count_tokens_estimate() from LLMClient.
    Implements call() and get_model_name() for the OpenAI API.
    """

    DEFAULT_MODEL = "gpt-4o"   # class variable — shared by all OpenAIClient instances

    def __init__(self, api_key, model=None, max_tokens=512, temperature=0.2):
        """
        super().__init__() calls the PARENT class __init__.

        Without super(): max_tokens and temperature would never be set!
        Always call super().__init__() when overriding __init__.
        """
        super().__init__(max_tokens=max_tokens, temperature=temperature)

        # OpenAI-specific attributes (not in the parent class)
        self._api_key = api_key
        self.model    = model or self.DEFAULT_MODEL

    def call(self, prompt: str) -> str:
        """Send a prompt to the OpenAI API. Implements the parent contract."""
        token_estimate = self.count_tokens_estimate(prompt)   # inherited from LLMClient
        log.info(f"OpenAI call | model={self.model} | ~{token_estimate} tokens")
        return f"[OpenAI {self.model}] Response to: {prompt[:50]}..."

    def get_model_name(self) -> str:
        """Return the OpenAI model identifier."""
        return self.model


"""
METHOD OVERRIDE:
A child class can REPLACE any parent method by defining it with the
same name. When you call obj.call(), Python finds the most specific
version first — the child's version wins.

super().call() — explicitly call the PARENT's version.
Use this when you want to run the parent's logic AND add something.
"""


class ResearchAgent(OpenAIClient):
    """
    An LLM agent that searches a knowledge base before calling the LLM.

    Overrides call() to add:
    1. Search the knowledge base for relevant context
    2. Inject context into the prompt (RAG pattern)
    3. Then call the LLM with the enriched prompt

    This is a simplified version of what LangGraph agents do.
    """

    def __init__(self, api_key, knowledge_base, model=None):
        super().__init__(api_key=api_key, model=model)   # chain up to OpenAIClient
        self._knowledge_base = knowledge_base            # RAG: documents to search

    def _search(self, query: str, top_k: int = 2) -> list:
        """Simple keyword search over the knowledge base."""
        query_lower = query.lower()
        results = []
        for doc in self._knowledge_base:
            content = doc.get("content", "").lower()
            if any(word in content for word in query_lower.split()):
                results.append(doc)
        return results[:top_k]

    def call(self, prompt: str) -> str:
        """
        Override: search first, then inject context, then call the LLM.

        super().call(enriched_prompt) calls OpenAIClient.call() — the parent.
        We add the search step BEFORE delegating the actual LLM call.
        """
        docs = self._search(prompt)

        if docs:
            context = "\n".join(f"[Doc] {d['content'][:100]}" for d in docs)
            enriched = f"<context>\n{context}\n</context>\n\n{prompt}"
            log.info(f"ResearchAgent: injected {len(docs)} context docs")
        else:
            enriched = prompt
            log.warning("ResearchAgent: no matching docs found")

        # Delegate the actual LLM call to the parent (OpenAIClient)
        return super().call(enriched)

    def __repr__(self):
        return f"ResearchAgent(model={self.model!r}, kb_docs={len(self._knowledge_base)})"


# Test the class hierarchy
knowledge_base = [
    {"content": "Classic Monitor is a 27-inch 4K display priced at $205.21, brand ProGear"},
    {"content": "ShopSmart return policy: 30 days from delivery, original packaging required"},
    {"content": "Ultimate Perfume is a luxury fragrance, price $568.17, in stock: 10 units"},
]

client = OpenAIClient(api_key="sk-mock", model="gpt-4o")
agent  = ResearchAgent(api_key="sk-mock", knowledge_base=knowledge_base)

print()
print("Class hierarchy — repr:")
print(f"  {client}")
print(f"  {agent}")

print()
print("OpenAIClient.call() — direct LLM call:")
print(f"  {client.call('Tell me about the Classic Monitor')}")

print()
print("ResearchAgent.call() — search + inject + LLM call:")
print(f"  {agent.call('What is the price of Classic Monitor?')}")


# ============================================================
# SECTION 2 — @classmethod AND ABC (brief mentions)
# ============================================================

"""
@classmethod — BRIEF MENTION (you will see this in LangChain)

A @classmethod uses `cls` (the CLASS) instead of `self` (the instance).
The most common use: alternative constructors ("factory methods")
that create an instance from a different input format.

You already saw this in Day 06's from_csv_row(cls, row) pattern.

  class ProductReview:
      @classmethod
      def from_csv_row(cls, row: dict) -> "ProductReview":
          return cls(
              review_id = int(row["review_id"]),
              rating    = int(row["rating"]),
              ...
          )
  # Usage:
  review = ProductReview.from_csv_row(csv_row_dict)

You do not need to write @classmethod often in Module 01.
Know it exists so you recognise it in LangChain source code.

─────────────────────────────────────────────────────────────

ABC (Abstract Base Class) — BRIEF MENTION

ABC forces child classes to implement specific methods.
If a child class doesn't, Python raises TypeError at instantiation.

LangChain uses ABC everywhere:
  class BaseTool(ABC):
      @abstractmethod
      def _run(self, query: str) -> str: ...

  class MyCustomTool(BaseTool):
      def _run(self, query: str) -> str:
          return "result"   ← must implement this or get TypeError

In this file, LLMClient uses raise NotImplementedError() instead.
ABC is the formal Python mechanism for the same concept.
"""

print()
print("─" * 60)
print("SECTION 2 — @classmethod + ABC (brief)")
print("─" * 60)

# Brief ABC demo — just enough to recognise the pattern
class BaseAgent(ABC):
    """ABC that forces child classes to implement respond()."""

    @abstractmethod
    def respond(self, query: str) -> str:
        """Must be implemented by every subclass."""
        ...   # abstract — no body

class SupportAgent(BaseAgent):
    def respond(self, query: str) -> str:
        return f"[Support] {query[:40]}..."

agent_instance = SupportAgent()
print()
print("ABC demo:")
print(f"  SupportAgent().respond('Hello') = {agent_instance.respond('Hello')}")
print("  (trying to instantiate BaseAgent() directly would raise TypeError)")


# ============================================================
# SECTION 3 — LIST COMPREHENSIONS
# ============================================================

"""
WHAT IS A LIST COMPREHENSION?
A concise one-line syntax for building a list from another collection.

SYNTAX:
  [expression   for item in collection   if condition]
   ↑             ↑                         ↑
   what to       loop over                 optional filter
   produce       each item

EQUIVALENT for loop:
  result = []
  for item in collection:
      if condition:
          result.append(expression)

WHEN TO USE:
  - Simple transforms: [x.lower() for x in words]
  - Filters: [r for r in reviews if r["rating"] >= 4]
  - Building dicts and sets (shown below)

WHEN NOT TO USE:
  - Complex multi-step logic (use a for loop — readability wins)
  - Side effects like print() or log() inside the comprehension
"""

print()
print("─" * 60)
print("SECTION 3 — List comprehensions")
print("─" * 60)

# Raw product data (from products.csv)
products = [
    {"product_id": "2001", "product_name": "Classic Monitor",   "category": "Electronics", "price": "205.21", "stock_quantity": "238"},
    {"product_id": "2002", "product_name": "Ultimate Perfume",  "category": "Beauty",      "price": "568.17", "stock_quantity": "10"},
    {"product_id": "2003", "product_name": "Budget Headphones", "category": "Electronics", "price": "29.99",  "stock_quantity": "0"},
    {"product_id": "2004", "product_name": "Yoga Mat Pro",      "category": "Sports",      "price": "45.00",  "stock_quantity": "150"},
    {"product_id": "2005", "product_name": "Luxury Cream",      "category": "Beauty",      "price": "89.00",  "stock_quantity": "55"},
]

# ── Filter: in-stock products only ────────────────────────────
in_stock = [
    p for p in products
    if int(p["stock_quantity"]) > 0
]
print()
print(f"In-stock products ({len(in_stock)} of {len(products)}):")
for p in in_stock:
    print(f"  {p['product_name']:25s}  stock={p['stock_quantity']}")

# ── Transform: extract just the names ─────────────────────────
names = [p["product_name"] for p in products]
print()
print(f"Product names only: {names}")

# ── Filter + Transform: names of Electronics in stock ─────────
electronics = [
    p["product_name"]
    for p in products
    if p["category"] == "Electronics" and int(p["stock_quantity"]) > 0
]
print()
print(f"In-stock Electronics: {electronics}")

# ── Practical: build prompt lines for each product ────────────
prompt_lines = [
    f"- {p['product_name']} (${float(p['price']):.2f}, stock={p['stock_quantity']})"
    for p in in_stock
]
prompt_text = "\n".join(prompt_lines)
print()
print("Product context for LLM prompt:")
print(prompt_text)


# ── Dict comprehension ────────────────────────────────────────

"""
DICT COMPREHENSION:
  {key_expr: value_expr for item in collection}

USE CASE: build a fast lookup index.
  Instead of searching a list every time (slow),
  build a dict keyed by ID (instant lookup).
"""

product_index = {
    int(p["product_id"]): p
    for p in products
}

print()
print("Dict comprehension — product lookup index:")
print(f"  Keys: {list(product_index.keys())}")
print(f"  Lookup product 2001: {product_index[2001]['product_name']}")
print(f"  Lookup product 2004: {product_index[2004]['product_name']}")


# ── Set comprehension ─────────────────────────────────────────

"""
SET COMPREHENSION:
  {expression for item in collection}

Use when you want unique values only.
"""

categories = {p["category"] for p in products}   # duplicates removed automatically
print()
print(f"Unique categories (set comprehension): {categories}")


# ============================================================
# SUMMARY
# ============================================================

"""
KEY TAKEAWAYS:

1. class Child(Parent):
   Child inherits all Parent methods for free.

2. super().__init__() — always call this in a child's __init__
   to run the parent's setup code.

3. Method override: define the same method name in the child.
   super().method() — explicitly call the parent version.

4. @classmethod — alternative constructor (factory method).
   Uses cls instead of self. Recognise it in LangChain code.

5. ABC — forces child classes to implement abstract methods.
   from abc import ABC, abstractmethod
   Recognise it in LangChain source code.

6. List comprehension:
   [expr for item in collection if condition]
   → filter + transform in one readable line

7. Dict comprehension:
   {key: value for item in collection}
   → fast lookup index built from a list

NEXT: Day 08 — Pydantic v2 + Database
  (validating LLM responses with models, and loading the CSV data
  into a real Postgres database)
"""

print()
print("=" * 60)
print("Day 07 complete. Run: python modules/day08_pydantic_database.py")
print("=" * 60)
