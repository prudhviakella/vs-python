"""
============================================================
Day 09 — Async Fundamentals
============================================================
Module 01: Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. The event loop — what it is and why it exists
  2. async def + await — writing coroutines
  3. asyncio.run()    — the entry point for async programs
  4. Sync generators  — yield (prerequisite for async generators)
  5. async with       — async resource management
  6. Async generators — yield inside async def (preview of streaming)

WHY THIS MATTERS:
  A FastAPI service handling 100 concurrent users makes 100 concurrent
  LLM API calls. Each call takes 3-8 seconds. Without async, users
  queue up and wait. With async, all 100 calls happen simultaneously.

  The pattern you learn here is used in EVERY LLM streaming endpoint.

RUN THIS FILE:
  python modules/day09_async_fundamentals.py
"""

import asyncio
import time
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ============================================================
# SECTION 1 — THE EVENT LOOP
# ============================================================

"""
THE EVENT LOOP — the core concept.

ANALOGY: think of the event loop as a restaurant waiter.

SYNCHRONOUS (no event loop):
  The waiter takes Order A to the kitchen, stands at the counter
  watching the food cook for 8 minutes, then delivers it to Table A.
  Then takes Order B... Table B waits 16+ minutes.

ASYNCHRONOUS (with event loop):
  The waiter takes Order A to the kitchen, says "call me when ready",
  immediately takes Order B, then Order C...
  When kitchen calls "Order A ready!", the waiter picks it up.
  All three tables are served in ~8 minutes total.

KEY INSIGHT:
  asyncio does NOT use multiple threads.
  ONE thread. ONE event loop. Cooperative scheduling.
  When an async function hits `await`, it YIELDS control back
  to the event loop, which can then run another coroutine.

THIS IS WHY: time.sleep() inside async code blocks EVERYTHING.
  time.sleep(3)        → blocks the entire event loop for 3 seconds
  await asyncio.sleep(3) → yields to the event loop for 3 seconds
                           other coroutines can run during that time
"""


# ============================================================
# SECTION 2 — SYNC GENERATORS (prerequisite for async generators)
# ============================================================

"""
WHAT IS A GENERATOR?
A function that uses `yield` to produce values ONE AT A TIME.
Instead of building the whole list and returning it, a generator
produces one value, pauses, and waits for the caller to ask for next.

WHY LEARN THIS FIRST?
  Async generators (streaming LLM tokens) follow the same idea.
  Understanding sync generators makes async generators obvious.

SYNTAX:
  def my_generator():
      yield value1
      yield value2
      yield value3

  for item in my_generator():
      print(item)   ← receives one value at a time

A generator function returns a generator OBJECT (not a value).
Each time the caller asks for the next item, execution resumes
from the last `yield` and runs until the next `yield` (or return).
"""

def generate_prompt_chunks(document: str, chunk_size: int = 100):
    """
    Split a document into chunks, yielding one at a time.

    This is a generator: it yields chunks one by one instead of
    returning a list of all chunks at once.

    In RAG pipelines, documents are chunked before embedding.
    """
    start = 0
    while start < len(document):
        end   = min(start + chunk_size, len(document))
        chunk = document[start:end]
        yield chunk          # ← send this chunk to the caller, then pause
        start = end          # ← resume here when next() is called


def few_shot_generator(examples: list[dict], max_count: int = 3):
    """
    Yield formatted few-shot examples one at a time.

    `return` inside a generator ends the sequence (raises StopIteration).
    """
    for i, example in enumerate(examples):
        if i >= max_count:
            return    # stop early
        yield f"Input : {example['input']}\nOutput: {example['output']}"


# ============================================================
# SECTION 3 — async def + await
# ============================================================

"""
WRITING ASYNC FUNCTIONS:

  async def my_function():
      result = await some_slow_operation()
      return result

`async def` marks a function as a coroutine.
`await` yields control back to the event loop WHILE WAITING.

THE TWO MOST COMMON MISTAKES:

  MISTAKE 1 — forgetting await:
    result = fetch_llm_response(prompt)      ← returns a coroutine OBJECT!
    result = await fetch_llm_response(prompt) ← runs the coroutine, gets the value

  MISTAKE 2 — blocking the event loop:
    time.sleep(3)            ← blocks ALL other requests for 3 seconds
    await asyncio.sleep(3)   ← yields control, other requests can run
"""

async def simulate_llm_call(prompt: str, delay: float = 1.0) -> str:
    """
    Simulate an async LLM API call.

    await asyncio.sleep(delay) = "I'm waiting for the API response.
    Event loop: please run other coroutines while I wait."
    """
    log.info(f"→ LLM call started | prompt={prompt[:30]}...")
    await asyncio.sleep(delay)   # yields control to the event loop
    log.info(f"← LLM call done   | prompt={prompt[:30]}...")
    return f"[LLM] Response to: {prompt[:40]}"


async def simulate_db_query(customer_id: int) -> dict:
    """Simulate an async database query."""
    log.info(f"→ DB query started | customer_id={customer_id}")
    await asyncio.sleep(0.3)
    log.info(f"← DB query done   | customer_id={customer_id}")
    return {"customer_id": customer_id, "name": "Danielle Johnson", "city": "Port Matthew"}


# ============================================================
# SECTION 4 — async with
# ============================================================

"""
async with — the async version of the with statement (Day 04).

SYNC  with open("file") as f:    → opens and closes a file synchronously
ASYNC with httpx.AsyncClient() as client: → opens and closes an HTTP client async

The concept is identical — automatic cleanup when the block exits.
The difference: the open/close operations themselves can be awaited.

USE async with FOR:
  - httpx.AsyncClient (async HTTP requests to LLM APIs)
  - Async database connections
  - Any resource whose setup/teardown involves I/O
"""

async def fetch_product_data(product_id: int) -> dict:
    """
    Fetch product data using httpx.AsyncClient.

    In production: real URL like https://api.shopsmart.com/products/{id}
    Here: simulated with a delay.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # client is opened when the block starts
        # client is automatically closed when the block exits (even on error)
        await asyncio.sleep(0.2)   # simulate network latency

        return {
            "product_id"  : product_id,
            "product_name": "Classic Monitor",
            "price"       : 205.21,
            "in_stock"    : True,
        }
    # client.aclose() has been called automatically here


# ============================================================
# SECTION 5 — ASYNC GENERATORS (streaming preview)
# ============================================================

"""
ASYNC GENERATOR = async def + yield

This is the EXACT mechanism used to stream LLM tokens in FastAPI.

How streaming works:
  1. The LLM generates one token at a time (not the whole response at once)
  2. Each token is yielded as soon as it's ready
  3. The browser receives and displays each token immediately
  4. The user sees text appearing word by word

In Day 12 you wrap this in EventSourceResponse for SSE streaming.
"""

async def stream_response_tokens(prompt: str, num_tokens: int = 6):
    """
    Async generator that yields one word (token) at a time.

    async for token in stream_response_tokens("Hello"):
        print(token, end="", flush=True)
    """
    words = f"The answer to your query about {prompt[:20]} is here".split()

    for word in words[:num_tokens]:
        await asyncio.sleep(0.1)   # simulate token generation delay
        yield word + " "           # yield one token to the caller


# ============================================================
# DEMO — asyncio.run() starts everything
# ============================================================

"""
asyncio.run(coroutine)
  = create an event loop
  + run the coroutine to completion
  + close the event loop

Call this ONCE from synchronous code (e.g. at the bottom of your script).
Inside async functions: just use `await`, not asyncio.run().
"""

async def main():
    """Main async entry point for Day 09 demo."""

    print("=" * 60)
    print("DAY 09 — Async Fundamentals")
    print("=" * 60)

    # Sync generators
    print()
    print("─" * 60)
    print("Sync generators (yield)")
    print("─" * 60)

    doc = "The quick brown fox jumps over the lazy dog. " * 2
    print()
    print("Chunking document with generator:")
    for i, chunk in enumerate(generate_prompt_chunks(doc, chunk_size=50)):
        print(f"  Chunk {i}: '{chunk}'")

    examples = [
        {"input": "Where is my order?", "output": "Please share your order ID."},
        {"input": "I want a refund.",    "output": "I'll start the return process."},
        {"input": "What is on sale?",    "output": "Check our promotions page."},
    ]
    print()
    print("Few-shot generator (max 2):")
    for ex_text in few_shot_generator(examples, max_count=2):
        print(f"  {ex_text}")

    # async def + await
    print()
    print("─" * 60)
    print("async def + await")
    print("─" * 60)

    start = time.perf_counter()
    response = await simulate_llm_call("What is the price of Classic Monitor?", delay=0.5)
    elapsed  = round((time.perf_counter() - start) * 1000)
    print()
    print(f"Single async LLM call:")
    print(f"  Response: {response}")
    print(f"  Elapsed : {elapsed}ms")

    # Sequential async (to compare with parallel in Day 10)
    print()
    print("Sequential async calls (one after another):")
    queries = ["Query A", "Query B", "Query C"]
    start   = time.perf_counter()
    for q in queries:
        r = await simulate_llm_call(q, delay=0.3)
    seq_time = round(time.perf_counter() - start, 2)
    print(f"  Sequential time: {seq_time}s  (Day 10 shows parallel = faster)")

    # async with
    print()
    print("─" * 60)
    print("async with — fetch product data")
    print("─" * 60)

    products = []
    for pid in [2001, 2002, 2003]:
        p = await fetch_product_data(pid)
        products.append(p)
        print(f"  Fetched product {p['product_id']}: {p['product_name']}")

    # async generator
    print()
    print("─" * 60)
    print("Async generator — streaming tokens")
    print("─" * 60)
    print()
    print("  Streaming: ", end="", flush=True)
    async for token in stream_response_tokens("Classic Monitor price"):
        print(token, end="", flush=True)
    print()

    # DB query
    print()
    print("─" * 60)
    print("Async DB query simulation")
    print("─" * 60)
    customer = await simulate_db_query(1001)
    print()
    print(f"  Customer: {customer['name']} from {customer['city']}")


    print()
    print("KEY TAKEAWAYS:")
    print("  1. await = 'I am waiting; event loop, run something else.'")
    print("  2. time.sleep() blocks everything; await asyncio.sleep() does not.")
    print("  3. asyncio.run(main()) — start the event loop from sync code.")
    print("  4. async with — same as with, but works for async resources.")
    print("  5. Async generator: async def fn(): yield → async for x in fn()")
    print()
    print("NEXT: Day 10 — Async Patterns (gather, wait_for, create_task)")
    print("=" * 60)
    print("Day 09 complete. Run: python modules/day10_async_patterns.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
