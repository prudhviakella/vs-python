# Module 01 — Python + Async + FastAPI
**Vidya Sankalp | Applied GenAI Engineering**

> 12 sessions · 1.5 hours each · Mon–Fri · 2.5 weeks · 18 hours total

---

## Project — ShopSmart LLM Customer Support API

Every code example in this module is built around a real e-commerce dataset (250 customers, 371 products, 500 orders). By Day 12 you have a running FastAPI service with SSE streaming, middleware, and a mock LLM support agent.

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env — fill in OPENAI_API_KEY and DB_* settings

# 4. Run a module
python modules/day01_setup_variables.py

# 5. Open a notebook
jupyter notebook notebooks/day01_setup_variables.ipynb

# 6. Run the FastAPI app (after Day 12)
uvicorn fastapi_app.main:app --reload --port 8000
# Open: http://localhost:8000/docs
```

---

## Structure

```
module01/
├── modules/                    ← Python .py files (one per day)
│   ├── day01_setup_variables.py
│   ├── day02_conditions_loops.py
│   ├── day03_functions_data_structures.py
│   ├── day04_file_io_json.py
│   ├── day05_exception_handling_logging.py
│   ├── day06_oop_classes.py
│   ├── day07_oop_inheritance.py
│   ├── day08_pydantic_database.py
│   ├── day09_async_fundamentals.py
│   ├── day10_async_patterns.py
│   └── day11_modules_packages_requests.py
│
├── notebooks/                  ← Jupyter notebooks (mirrors modules/)
│   └── day01_setup_variables.ipynb ... day11_*.ipynb
│
├── fastapi_app/                ← PACKAGE: FastAPI application (Day 12–13)
│   ├── __init__.py             ← re-exports key models
│   ├── main.py                 ← app entry point, lifespan, middleware, endpoints
│   ├── models.py               ← Pydantic models (ChatRequest, CustomerRecord ...)
│   ├── database.py             ← DB connection, CRUD functions
│   └── routers/                ← SUB-PACKAGE: route groups
│       ├── __init__.py
│       ├── customers.py        ← GET /customers/{id}, GET /customers/{id}/orders
│       └── products.py         ← GET /products/, GET /products/{id}
│
├── data/
│   ├── datasets/               ← CSV files (customers, products, orders ...)
│   └── knowledge_base/         ← Semantic JSON files (for RAG — Module 04)
│
├── prompts/
│   ├── system_prompt.txt       ← ShopSmart system prompt (loaded at startup)
│   └── few_shot_examples.json  ← Few-shot examples for the LLM
│
├── requirements.txt
├── .env.example                ← Copy to .env and fill in keys
└── README.md
```

---

## Session Map

| Day | Module File | Key Concepts |
|-----|-------------|--------------|
| 1 | `day01_setup_variables.py` | venv, pip, variables, type hints, f-strings, os.environ, dotenv |
| 2 | `day02_conditions_loops.py` | if/elif/else, for, while, range, break, continue, retry |
| 3 | `day03_functions_data_structures.py` | def, *args, **kwargs, lambda, list, dict, set, tuple |
| 4 | `day04_file_io_json.py` | with statement, file I/O, json.loads/.dumps, .get(), string methods |
| 5 | `day05_exception_handling_logging.py` | try/except/finally, custom exceptions, logging, retry backoff |
| 6 | `day06_oop_classes.py` | class, __init__, @property, __repr__, isinstance |
| 7 | `day07_oop_inheritance.py` | inheritance, super(), @classmethod, ABC mention, comprehensions |
| 8 | `day08_pydantic_database.py` | BaseModel, Field, model_validate_json, TypedDict, psycopg2 |
| 9 | `day09_async_fundamentals.py` | event loop, async/await, asyncio.run, sync generators, async with |
| 10 | `day10_async_patterns.py` | asyncio.gather, wait_for, create_task, async generators |
| 11 | `day11_modules_packages_requests.py` | module vs package, __init__.py, imports, requests library |
| 12 | `fastapi_app/` | FastAPI, lifespan, middleware, SSE streaming, BackgroundTasks |

---

## Data — E-Commerce Dataset

| File | Rows | Key Columns |
|------|------|-------------|
| customers.csv | 250 | customer_id, first_name, last_name, email, city, state |
| products.csv | 371 | product_id, product_name, category, brand, price, stock_quantity |
| orders.csv | 500 | order_id, customer_id, total_amount, order_status |
| reviews.csv | 678 | review_id, product_id, customer_id, rating, review_text |
| shipments.csv | — | order_id, carrier, tracking_number, status |
| + 8 more tables | — | inventory, payments, suppliers, warehouses, promotions … |

`data/knowledge_base/` contains semantic JSON files for each table — used in Module 04 RAG pipelines.

---

## FastAPI Endpoints (Day 12–13)

```
GET  /                    → service info
GET  /health              → liveness check
POST /chat                → send message, get JSON response
GET  /chat/stream         → SSE streaming (tokens arrive live)
GET  /customers/{id}      → customer lookup
GET  /customers/{id}/orders → customer's orders
GET  /products/           → list in-stock products (?category=Electronics)
GET  /products/{id}       → single product lookup
GET  /categories          → all product categories
```

After `uvicorn fastapi_app.main:app --reload`, visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

*Vidya Sankalp © 2026 — Prudhvi Akella*
