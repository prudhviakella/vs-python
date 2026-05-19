"""
fastapi_app — ShopSmart E-Commerce LLM Service
================================================
This is the __init__.py for the fastapi_app package.

It re-exports the most commonly used models so callers can write:
    from fastapi_app import CustomerRecord
Instead of:
    from fastapi_app.models import CustomerRecord

This is the standard Python package pattern for "clean imports."
"""

# Re-export key models from this package's top-level namespace
from fastapi_app.models import (
    CustomerRecord,
    ProductRecord,
    OrderRecord,
    ChatRequest,
    ChatResponse,
    TriageResult,
)

__all__ = [
    "CustomerRecord",
    "ProductRecord",
    "OrderRecord",
    "ChatRequest",
    "ChatResponse",
    "TriageResult",
]
