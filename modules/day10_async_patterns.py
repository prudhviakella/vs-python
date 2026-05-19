"""
============================================================
Day 10 — Async Patterns: gather, wait_for, create_task
============================================================
Module 01: Python + Async + FastAPI for LLM Engineering
Vidya Sankalp | Applied GenAI Engineering

WHAT YOU WILL LEARN TODAY:
  1. asyncio.gather()      — run multiple coroutines IN PARALLEL
  2. return_exceptions=True — handle partial failures gracefully
  3. asyncio.wait_for()    — add a timeout to any coroutine
  4. asyncio.create_task() — fire-and-forget background work

WHY THIS MATTERS:
  An LLM agent often needs to call 3 tools before answering.

  Sequential  → 3 tools × 2 seconds each = 6 seconds
  Parallel    → all 3 tools simultaneously = 2 seconds

  asyncio.gather() gives you that 3× speedup for free.
  Every production LLM agent uses all three patterns in this file.

RUN THIS FILE:
  python modules/day10_async_patterns.py
"""

import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ============================================================
# SIMULATED TOOL FUNCTIONS
# ============================================================

"""
In later modules these become real MCP tools called by LangGraph agents.
Here they are simulated with asyncio.sleep() to show timing.
"""

async def tool_lookup_customer(customer_id: int) -> dict:
    """Simulate fetching a customer from the database (1.2s)."""
    log.info(f"→ lookup_customer({customer_id}) started")
    await asyncio.sleep(1.2)
    log.info(f"← lookup_customer({customer_id}) done")
    return {"customer_id": customer_id, "name": "Danielle Johnson", "email": "john21@example.net"}


async def tool_lookup_order(order_id: int) -> dict:
    """Simulate fetching an order from the database (1.5s)."""
    log.info(f"→ lookup_order({order_id}) started")
    await asyncio.sleep(1.5)
    log.info(f"← lookup_order({order_id}) done")
    return {"order_id": order_id, "status": "In Transit", "total": 1324.89}


async def tool_check_inventory(product_id: int) -> dict:
    """Simulate checking inventory (0.8s — cached, faster)."""
    log.info(f"→ check_inventory({product_id}) started")
    await asyncio.sleep(0.8)
    log.info(f"← check_inventory({product_id}) done")
    return {"product_id": product_id, "quantity": 238, "warehouse": "East Coast"}


async def tool_slow_shipping_api(order_id: int) -> dict:
    """Simulate a very slow external shipping API (8 seconds — will timeout)."""
    log.info(f"→ slow_shipping_api({order_id}) started")
    await asyncio.sleep(8.0)
    return {"tracking": "1Z999AA133781932"}


# ============================================================
# SECTION 1 — asyncio.gather()
# ============================================================

"""
WHAT IS asyncio.gather()?
Run multiple coroutines at the SAME TIME and wait for all to finish.

  results = await asyncio.gather(coro1, coro2, coro3)

- All coroutines start simultaneously
- gather() waits until ALL of them finish
- Returns results in the SAME ORDER as the coroutines were passed in,
  regardless of which one finished first
- Total time = max(individual times), not the sum

SEQUENTIAL (one after another):
  customer  = await tool_lookup_customer(1001)   # 1.2s
  order     = await tool_lookup_order(3001)       # 1.5s
  inventory = await tool_check_inventory(2001)   # 0.8s
  # Total: 3.5s

PARALLEL (all at once with gather):
  customer, order, inventory = await asyncio.gather(
      tool_lookup_customer(1001),
      tool_lookup_order(3001),
      tool_check_inventory(2001),
  )
  # Total: max(1.2, 1.5, 0.8) = 1.5s  ← 2.3x faster!
"""


async def run_tools_sequentially(customer_id, order_id, product_id):
    """Run three tools one after another (slow path — for comparison)."""
    customer  = await tool_lookup_customer(customer_id)
    order     = await tool_lookup_order(order_id)
    inventory = await tool_check_inventory(product_id)
    return customer, order, inventory


async def run_tools_in_parallel(customer_id, order_id, product_id):
    """Run three tools simultaneously using asyncio.gather()."""
    customer, order, inventory = await asyncio.gather(
        tool_lookup_customer(customer_id),
        tool_lookup_order(order_id),
        tool_check_inventory(product_id),
    )
    return customer, order, inventory


# ============================================================
# SECTION 2 — return_exceptions=True
# ============================================================

"""
HANDLING PARTIAL FAILURES:

WITHOUT return_exceptions=True (default):
  If ANY coroutine raises an exception, gather() immediately
  raises that exception and cancels all remaining coroutines.
  You lose results from the successful ones.

WITH return_exceptions=True:
  gather() collects ALL results — successes AND exceptions.
  Exceptions are returned as values in the results list.
  You can then handle each result individually.

  results = await asyncio.gather(coro1, coro2, broken_coro, return_exceptions=True)
  → [result1, result2, SomeException("error message")]

In production: one broken tool should NOT crash the entire agent response.
"""

async def run_with_partial_failure(customer_id, order_id, product_id):
    """Demonstrate graceful handling when one tool fails."""

    async def broken_tool(product_id):
        """Simulate a tool that always fails."""
        await asyncio.sleep(0.3)
        raise ConnectionError(f"Inventory service unavailable for product {product_id}")

    results = await asyncio.gather(
        tool_lookup_customer(customer_id),
        tool_lookup_order(order_id),
        broken_tool(product_id),           # this one will fail
        return_exceptions=True,            # don't crash on failure
    )

    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            log.warning(f"Tool {i} failed: {result}")
            processed.append({"error": str(result)})
        else:
            processed.append(result)

    return processed


# ============================================================
# SECTION 3 — asyncio.wait_for()
# ============================================================

"""
WHAT IS asyncio.wait_for()?
Run a coroutine with a maximum time limit.
If the coroutine takes longer than the timeout, it is CANCELLED
and asyncio.TimeoutError is raised.

  result = await asyncio.wait_for(some_slow_coro(), timeout=3.0)

WHY THIS MATTERS:
  External APIs (shipping, payment, inventory) can hang indefinitely.
  A stuck tool call should NEVER block a user from getting a response.
  Always add a timeout to every external call.

PATTERN:
  try:
      result = await asyncio.wait_for(external_call(), timeout=3.0)
  except asyncio.TimeoutError:
      result = fallback_value   ← return something useful
"""


# ============================================================
# SECTION 4 — asyncio.create_task()
# ============================================================

"""
WHAT IS asyncio.create_task()?
Schedule a coroutine to run in the background WITHOUT waiting for it.

  task = asyncio.create_task(write_log_to_db(data))
  return response   ← return immediately, log write continues in background

The user gets the response immediately.
The log write happens on its own schedule.

This is the same pattern FastAPI's BackgroundTasks uses internally.

IMPORTANT: ALWAYS store the task reference!
  task = asyncio.create_task(...)    ← store in a variable
  # NOT:
  asyncio.create_task(...)           ← task may be garbage-collected before finishing!
"""

_background_tasks = set()   # keep task references alive

async def write_call_log(session_id: str, category: str, latency_ms: float) -> None:
    """Simulate writing a call record to the database (slow I/O)."""
    log.info(f"[BG] Writing log: session={session_id}, category={category}, latency={latency_ms}ms")
    await asyncio.sleep(0.5)   # simulate slow DB write
    log.info(f"[BG] Log written")


async def handle_query_with_background_log(query: str, session_id: str) -> str:
    """
    Handle a user query and fire a background log write.

    The user does NOT wait for the log — they get the response immediately.
    """
    start = time.perf_counter()

    # Simulate LLM call
    await asyncio.sleep(0.3)
    response   = f"[LLM] Response to: {query}"
    latency_ms = round((time.perf_counter() - start) * 1000)

    # Fire the log write as a background task
    task = asyncio.create_task(
        write_call_log(session_id, "TRACK_ORDER", latency_ms)
    )
    _background_tasks.add(task)                          # keep reference alive
    task.add_done_callback(_background_tasks.discard)    # clean up when done

    log.info("Response returned. Background log task scheduled.")
    return response


# ============================================================
# DEMO
# ============================================================

async def main():
    print("=" * 60)
    print("DAY 10 — Async Patterns")
    print("=" * 60)

    # gather: sequential vs parallel
    print()
    print("─" * 60)
    print("asyncio.gather() — sequential vs parallel")
    print("─" * 60)

    CUSTOMER_ID, ORDER_ID, PRODUCT_ID = 1001, 3001, 2001

    print()
    print("Sequential (one after another):")
    start = time.perf_counter()
    seq   = await run_tools_sequentially(CUSTOMER_ID, ORDER_ID, PRODUCT_ID)
    seq_time = round(time.perf_counter() - start, 2)
    print(f"  Time: {seq_time}s")

    print()
    print("Parallel (all at once with gather):")
    start = time.perf_counter()
    par   = await run_tools_in_parallel(CUSTOMER_ID, ORDER_ID, PRODUCT_ID)
    par_time = round(time.perf_counter() - start, 2)
    print(f"  Time: {par_time}s")

    print()
    print(f"  Sequential: {seq_time}s")
    print(f"  Parallel  : {par_time}s")
    print(f"  Speedup   : {seq_time / par_time:.1f}×")
    print(f"  Customer  : {par[0]['name']}")
    print(f"  Order     : {par[1]['status']}")
    print(f"  Inventory : {par[2]['quantity']} units")

    # partial failure
    print()
    print("─" * 60)
    print("return_exceptions=True — partial failure")
    print("─" * 60)
    partial = await run_with_partial_failure(CUSTOMER_ID, ORDER_ID, PRODUCT_ID)
    print()
    for i, result in enumerate(partial):
        status = "ERROR" if "error" in result else "OK"
        print(f"  Tool {i}: {status} — {result}")

    # wait_for timeout
    print()
    print("─" * 60)
    print("asyncio.wait_for() — timeout after 2 seconds")
    print("─" * 60)
    print()
    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            tool_slow_shipping_api(ORDER_ID),
            timeout=2.0
        )
        print(f"  Result: {result}")
    except asyncio.TimeoutError:
        elapsed = round(time.perf_counter() - start, 2)
        fallback = {"tracking": "unavailable", "message": "Tracking service slow — try again later"}
        log.warning(f"Shipping API timed out after {elapsed}s. Using fallback.")
        print(f"  Fallback: {fallback}")

    # create_task fire and forget
    print()
    print("─" * 60)
    print("asyncio.create_task() — fire and forget")
    print("─" * 60)
    print()
    start    = time.perf_counter()
    response = await handle_query_with_background_log("Where is order #3042?", "sess_abc")
    resp_ms  = round((time.perf_counter() - start) * 1000)
    print(f"  Response returned in {resp_ms}ms: {response}")
    print(f"  (Background log task still running...)")

    await asyncio.sleep(1.0)   # let the background task finish before script exits
    print(f"  (Background task finished)")

    print()
    print("─" * 60)
    print("KEY TAKEAWAYS")
    print("─" * 60)
    print()
    print("  asyncio.gather(c1, c2, c3)            → parallel, wait for all")
    print("  asyncio.gather(..., return_exceptions=True) → partial failure safe")
    print("  await asyncio.wait_for(coro, timeout)  → cancel if too slow")
    print("  task = asyncio.create_task(coro)       → fire and forget")
    print("  Always store the task reference → prevent garbage collection")

    print()
    print("=" * 60)
    print("Day 10 complete. Run: python modules/day11_modules_packages_requests.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
