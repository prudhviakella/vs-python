"""
fastapi_app/models.py — Pydantic Models for the ShopSmart LLM Service
=======================================================================
All request/response and database models in one place.

These models serve three purposes:
1. FastAPI request validation — incoming HTTP request bodies
2. FastAPI response serialisation — outgoing HTTP responses
3. Database row validation — data coming from the Postgres database
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr


# ── API Request / Response Models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    Body of a POST /chat request.

    FastAPI automatically validates incoming JSON against this model.
    If any field is missing or invalid, FastAPI returns HTTP 422 (Unprocessable Entity).
    """

    message    : str  = Field(min_length=1, max_length=2000, description="The customer's message")
    session_id : str  = Field(default="default", description="Conversation session ID for multi-turn")
    customer_id: Optional[int] = Field(default=None, description="Customer ID if known")
    stream     : bool = Field(default=False, description="Set True to stream tokens via SSE")


class ChatResponse(BaseModel):
    """
    Body of the POST /chat response.

    FastAPI serialises this model to JSON automatically.
    response_model=ChatResponse in the @app.post decorator enforces this.
    """

    response   : str
    category   : Optional[str] = None   # routing category: TRACK_ORDER, BILLING, etc.
    session_id : str = "default"
    tokens_used: Optional[int] = None   # LLM usage for monitoring


class TriageResult(BaseModel):
    """LLM triage classification output — validated from LLM JSON response."""

    category  : Literal["TRACK_ORDER", "BILLING", "RETURNS", "PRODUCT", "OTHER"]
    confidence: Literal["high", "medium", "low"]
    reason    : str = Field(min_length=5)


# ── Database Models ───────────────────────────────────────────────────────────

class CustomerRecord(BaseModel):
    """Validated customer record from the customers table."""

    customer_id: int   = Field(gt=0)
    first_name : str   = Field(min_length=1)
    last_name  : str   = Field(min_length=1)
    email      : str
    city       : Optional[str] = None
    state      : Optional[str] = None
    country    : str = "USA"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class ProductRecord(BaseModel):
    """Validated product record from the products table."""

    product_id    : int   = Field(gt=0)
    product_name  : str
    category      : Optional[str] = None
    brand         : Optional[str] = None
    price         : float = Field(ge=0)
    stock_quantity: int   = Field(ge=0, default=0)
    description   : Optional[str] = None

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def price_str(self) -> str:
        return f"${self.price:.2f}"


class OrderRecord(BaseModel):
    """Validated order record from the orders table."""

    order_id      : int
    customer_id   : int
    total_amount  : float = Field(ge=0)
    payment_method: Optional[str] = None
    order_status  : str
    shipping_city : Optional[str] = None
    shipping_state: Optional[str] = None
