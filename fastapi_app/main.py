"""
fastapi_app/main.py — ShopSmart LLM Customer Support API
==========================================================
Module 01 Day 12: FastAPI Basics + Streaming + Middleware
Vidya Sankalp | Applied GenAI Engineering

HOW TO RUN:
    uvicorn fastapi_app.main:app --reload --port 8000

THEN VISIT:
    http://localhost:8000/docs     ← interactive API docs (Swagger UI)
    http://localhost:8000/redoc    ← alternative API docs

ENDPOINTS:
    POST /chat              → send a message, get a response
    GET  /chat/stream       → SSE streaming (tokens arrive one by one)
    GET  /customers/{id}    → look up a customer
    GET  /products/         → list in-stock products
    GET  /products/{id}     → look up a product
    GET  /health            → liveness check

ARCHITECTURE — what this file demonstrates:
    @app.lifespan           → one-time startup: build the agent, connect to DB
    BaseHTTPMiddleware      → request logging + rate limiting
    CORSMiddleware          → allow browser clients to call this API
    EventSourceResponse     → SSE streaming (async generator → browser)
    BackgroundTasks         → fire-and-forget call logging (don't block response)
    app.include_router()    → modular routes from routers/customers.py etc.
"""

import asyncio
import json
import logging
import time
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_app.models import ChatRequest, ChatResponse, TriageResult
from fastapi_app.routers import customers, products

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

BASE_DIR   = Path(__file__).parent.parent
PROMPT_DIR = BASE_DIR / "prompts"


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1: LIFESPAN — STARTUP AND SHUTDOWN
# ═════════════════════════════════════════════════════════════════════════════
#
# @app.lifespan is the modern FastAPI pattern (replaces @app.on_event("startup")).
# Code BEFORE the `yield` runs once when the server starts (cold start).
# Code AFTER the `yield` runs once when the server shuts down (cleanup).
#
# Why build the agent once at startup (not on every request)?
# - Building an LLM agent loads models, connects to DBs, compiles the graph
# - This can take 2-5 seconds — unacceptable on every request
# - Build once → store in app.state → share across all requests
#
# In Module 05 (LangGraph), this is where you build the compiled agent graph.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup → serve → shutdown.

    app.state is a simple namespace for storing application-level objects.
    These objects are shared across all requests (singleton pattern).
    """

    # ── STARTUP ────────────────────────────────────────────────────────────────
    log.info("Starting ShopSmart LLM Service...")

    # Load the system prompt from the file at startup.
    # This file is read ONCE — not on every request.
    try:
        system_prompt_path = PROMPT_DIR / "system_prompt.txt"
        if system_prompt_path.exists():
            with open(system_prompt_path, encoding="utf-8") as f:
                app.state.system_prompt = f.read().strip()
            log.info(f"System prompt loaded ({len(app.state.system_prompt)} chars)")
        else:
            app.state.system_prompt = "You are a helpful customer support agent."
            log.warning("system_prompt.txt not found — using default prompt")
    except Exception as e:
        log.error(f"Failed to load system prompt: {e}")
        app.state.system_prompt = "You are a helpful customer support agent."

    # Load few-shot examples
    try:
        few_shot_path = PROMPT_DIR / "few_shot_examples.json"
        if few_shot_path.exists():
            with open(few_shot_path, encoding="utf-8") as f:
                app.state.few_shot_examples = json.load(f).get("examples", [])
            log.info(f"Loaded {len(app.state.few_shot_examples)} few-shot examples")
        else:
            app.state.few_shot_examples = []
    except Exception as e:
        log.warning(f"Could not load few-shot examples: {e}")
        app.state.few_shot_examples = []

    # In Module 05 this is where you would:
    # app.state.agent = build_langgraph_agent(system_prompt=app.state.system_prompt)
    # app.state.db_conn = await connect_to_postgres()
    log.info("ShopSmart LLM Service ready on port 8000")

    # ── SERVE — yields control back to FastAPI ─────────────────────────────────
    yield

    # ── SHUTDOWN ───────────────────────────────────────────────────────────────
    log.info("Shutting down ShopSmart LLM Service...")
    # In Module 05: await app.state.db_conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2: MIDDLEWARE STACK
# ═════════════════════════════════════════════════════════════════════════════
#
# Middleware wraps EVERY request/response.
# Order matters: middleware runs top-to-bottom on the way IN (request),
# and bottom-to-top on the way OUT (response).
#
# Stack (order added to app):
#   1. LoggingMiddleware   → log every request + response time
#   2. RateLimiterMiddleware → reject too-frequent requests from same IP
#   3. CORSMiddleware      → add CORS headers (allow browser clients)
#
# Incoming request:  LoggingMiddleware → RateLimiter → CORS → endpoint
# Outgoing response: CORS → RateLimiter → LoggingMiddleware → client

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request with method, path, status code, and latency.

    Example log output:
        INFO  POST /chat | 200 OK | 342ms
        INFO  GET  /products/ | 200 OK | 8ms
        WARN  POST /chat | 429 Too Many Requests | 1ms
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        dispatch() is called for every incoming request.

        Args:
            request  : The incoming HTTP request.
            call_next: Function that passes the request to the next layer
                       (next middleware or the actual endpoint).

        Returns:
            The HTTP response.
        """

        start_time = time.perf_counter()

        # Pass the request down the stack to the next middleware / endpoint
        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000)

        # Log at WARNING level for 4xx/5xx, INFO for 2xx/3xx
        log_fn = log.warning if response.status_code >= 400 else log.info
        log_fn(
            f"{request.method:4s} {request.url.path:30s} | "
            f"{response.status_code} | {latency_ms}ms"
        )

        # Add latency to response headers (useful for client-side monitoring)
        response.headers["X-Process-Time-Ms"] = str(latency_ms)

        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter: max N requests per IP per minute.

    This is a teaching example — production rate limiting uses Redis
    (atomic counters, works across multiple server instances).

    How it works:
    - Track request count per IP per minute window
    - If over the limit: return 429 Too Many Requests
    - Reset counts every 60 seconds
    """

    def __init__(self, app, max_requests: int = 30):
        super().__init__(app)
        self.max_requests = max_requests
        self._counts: dict[str, int] = defaultdict(int)   # IP → count
        self._window_start: float = time.time()             # start of current window

    async def dispatch(self, request: Request, call_next) -> Response:
        # Reset counts every 60 seconds
        now = time.time()
        if now - self._window_start > 60:
            self._counts.clear()
            self._window_start = now

        # Get client IP (real apps use X-Forwarded-For behind a proxy)
        client_ip = request.client.host if request.client else "unknown"

        self._counts[client_ip] += 1

        if self._counts[client_ip] > self.max_requests:
            log.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Limit: {self.max_requests}/minute"},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3: CREATE THE FASTAPI APP
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title       = "ShopSmart LLM Customer Support API",
    description = "Module 01 final project — FastAPI + LLM + E-commerce data",
    version     = "1.0.0",
    lifespan    = lifespan,   # connect the lifespan context manager
)

# ── Add middleware (order: last added = outermost) ─────────────────────────────
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimiterMiddleware, max_requests=60)

# CORSMiddleware: allow browser JavaScript to call this API from any origin.
# In production: restrict allow_origins to your frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["*"],    # Allow all origins (restrict in production)
    allow_methods    = ["*"],    # Allow all HTTP methods
    allow_headers    = ["*"],    # Allow all headers
    allow_credentials= False,
)

# ── Include routers from sub-modules ──────────────────────────────────────────
# Each router handles a group of related endpoints.
# prefix="/customers" means all routes in customers.router start with /customers
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router,  prefix="/products",  tags=["products"])


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4: LLM SIMULATION HELPERS
# ═════════════════════════════════════════════════════════════════════════════
#
# In Module 05 these are replaced by real LangGraph agent calls.
# Here we simulate the LLM to keep Day 12 focused on FastAPI concepts.

async def simulate_llm_triage(message: str) -> TriageResult:
    """
    Simulate LLM triage classification.

    In production: calls the LangGraph agent with the customer message.
    Here: keyword matching to simulate LLM output.

    Args:
        message: The customer's raw message text.

    Returns:
        A validated TriageResult Pydantic model.
    """

    await asyncio.sleep(0.3)   # simulate LLM latency

    msg = message.lower()

    if any(w in msg for w in ["cancel", "refund", "money back"]):
        category, confidence = "RETURNS", "high"
    elif any(w in msg for w in ["order", "track", "delivery", "ship", "where"]):
        category, confidence = "TRACK_ORDER", "high"
    elif any(w in msg for w in ["invoice", "charge", "payment", "bill"]):
        category, confidence = "BILLING", "medium"
    elif any(w in msg for w in ["product", "specification", "review", "stock"]):
        category, confidence = "PRODUCT", "medium"
    else:
        category, confidence = "OTHER", "low"

    return TriageResult(
        category   = category,
        confidence = confidence,
        reason     = f"Keywords detected in message indicate {category}",
    )


async def simulate_llm_response(
    message      : str,
    triage       : TriageResult,
    system_prompt: str,
) -> str:
    """
    Simulate the LLM generating a customer support response.

    Args:
        message      : Customer's message.
        triage       : Triage classification result.
        system_prompt: The system prompt from app.state.

    Returns:
        A customer-facing response string.
    """

    await asyncio.sleep(0.8)   # simulate LLM generation time

    responses = {
        "TRACK_ORDER": "I can help you track your order. Could you please share your order ID?",
        "RETURNS"    : "I'd be happy to help with your return. Returns are accepted within 30 days of delivery in original packaging.",
        "BILLING"    : "For billing questions, I can pull up your invoice. Please share your order ID.",
        "PRODUCT"    : "I can look up product details for you. Which product are you interested in?",
        "OTHER"      : "Thank you for contacting ShopSmart support. How can I assist you today?",
    }

    return responses.get(triage.category, "How can I help you today?")


async def token_stream_generator(
    message      : str,
    triage       : TriageResult,
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields response tokens one at a time.

    This is the SSE streaming mechanism:
    1. Each `yield` sends one "event" to the browser
    2. The browser's EventSource API receives each event immediately
    3. The user sees text appearing token by token

    FastAPI wraps this generator in EventSourceResponse,
    which handles the SSE protocol (data: ...\n\n format).

    Yields:
        Dict with "data" key — EventSourceResponse sends this as: data: {...}
    """

    full_response = await simulate_llm_response(message, triage, system_prompt)
    words = full_response.split()

    for i, word in enumerate(words):
        # Simulate token generation delay (real LLMs: 30-60 tokens/second)
        await asyncio.sleep(0.12)

        # Yield one word (token) at a time
        # EventSourceResponse formats this as:  data: {"token": "word"}\n\n
        yield {
            "data": json.dumps({
                "token": word + (" " if i < len(words) - 1 else ""),
                "done" : False,
            })
        }

    # Send a final "done" event so the client knows the stream is finished
    yield {
        "data": json.dumps({
            "token": "",
            "done" : True,
            "category": triage.category,
        })
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5: BACKGROUND TASK
# ═════════════════════════════════════════════════════════════════════════════

async def log_llm_call(
    session_id: str,
    message   : str,
    category  : str,
    latency_ms: float,
) -> None:
    """
    Write an LLM call record to the log (fire-and-forget).

    This runs AFTER the response has been sent to the client.
    The user is NOT waiting for this — it runs in the background.

    In production: write to a database or analytics service.
    BackgroundTasks is FastAPI's built-in mechanism for this pattern.
    """

    # Simulate a slow write (database insert, analytics event, etc.)
    await asyncio.sleep(0.1)

    log.info(
        f"[CALL LOG] session={session_id} | category={category} "
        f"| latency={latency_ms}ms | query={message[:50]}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6: ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Liveness check — returns OK if the service is running.

    Used by load balancers and monitoring tools to verify the service is up.
    Should be fast (<10ms) and never fail unless the process is dead.
    """
    return {
        "status"        : "ok",
        "service"       : "ShopSmart LLM API",
        "prompt_loaded" : bool(getattr(app.state, "system_prompt", None)),
        "examples_count": len(getattr(app.state, "few_shot_examples", [])),
    }


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request         : ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """
    Main chat endpoint — send a customer message, get a response.

    Flow:
    1. Validate the request (FastAPI + Pydantic handle this automatically)
    2. Triage the message (classify intent)
    3. Generate a response
    4. Schedule a background log write (don't wait for it)
    5. Return the response to the client

    FastAPI handles:
    - JSON parsing of the request body
    - Validation against ChatRequest model (returns 422 on failure)
    - Serialisation of ChatResponse to JSON
    - Background task scheduling via BackgroundTasks

    Args:
        request         : Validated ChatRequest (FastAPI injects this)
        background_tasks: FastAPI's background task scheduler

    Returns:
        ChatResponse with the LLM's answer.
    """

    start_time = time.perf_counter()
    system_prompt = getattr(app.state, "system_prompt", "You are a helpful assistant.")

    # Step 1: Triage (run in parallel with any other prep work)
    triage = await simulate_llm_triage(request.message)
    log.info(f"Triage: {triage.category} ({triage.confidence}) for session {request.session_id}")

    # Step 2: Generate response
    response_text = await simulate_llm_response(request.message, triage, system_prompt)

    latency_ms = round((time.perf_counter() - start_time) * 1000)

    # Step 3: Schedule background log (fire and forget)
    # add_task() schedules the coroutine to run AFTER the response is sent
    # The client does NOT wait for this
    background_tasks.add_task(
        log_llm_call,
        session_id = request.session_id,
        message    = request.message,
        category   = triage.category,
        latency_ms = latency_ms,
    )

    # Step 4: Return response (background log runs after this)
    return ChatResponse(
        response   = response_text,
        category   = triage.category,
        session_id = request.session_id,
        tokens_used= len(response_text.split()),   # rough estimate
    )


@app.get("/chat/stream", tags=["chat"])
async def chat_stream(
    message   : str,
    session_id: str = "default",
) -> EventSourceResponse:
    """
    SSE streaming endpoint — tokens arrive in the browser one by one.

    Server-Sent Events (SSE) protocol:
    - The browser opens a persistent HTTP connection
    - The server pushes events as they arrive
    - Each event is formatted as: data: {json}\n\n
    - The browser's EventSource API handles reconnection automatically

    How to consume this endpoint from JavaScript:
        const source = new EventSource('/chat/stream?message=Hello');
        source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.done) { source.close(); return; }
            document.getElementById('response').innerHTML += data.token;
        };

    Args:
        message   : The customer's message (URL query parameter).
        session_id: Session ID for tracking.

    Returns:
        EventSourceResponse — a streaming HTTP response.
    """

    system_prompt = getattr(app.state, "system_prompt", "You are a helpful assistant.")

    # Triage first (fast, blocking — we need the category before streaming)
    triage = await simulate_llm_triage(message)
    log.info(f"Stream triage: {triage.category} for session {session_id}")

    # Return EventSourceResponse wrapping the async generator
    # FastAPI/sse-starlette handles the SSE protocol formatting automatically
    return EventSourceResponse(
        token_stream_generator(message, triage, system_prompt)
    )


# ── Additional utility endpoints ──────────────────────────────────────────────

@app.get("/categories", tags=["products"])
async def list_categories() -> list[str]:
    """
    Return all unique product categories.
    In production: query the database. Here: return static data.
    """
    return [
        "Electronics", "Beauty", "Sports", "Clothing",
        "Home & Garden", "Toys & Games", "Books", "Automotive",
    ]


@app.get("/", tags=["system"])
async def root() -> dict:
    """Root endpoint — shows available endpoints."""
    return {
        "message"  : "ShopSmart LLM Customer Support API",
        "docs"     : "/docs",
        "health"   : "/health",
        "endpoints": {
            "POST /chat"          : "Send a message to the support agent",
            "GET  /chat/stream"   : "Stream tokens via SSE",
            "GET  /customers/{id}": "Look up a customer",
            "GET  /products/"     : "List in-stock products",
            "GET  /products/{id}" : "Get a specific product",
        },
    }
