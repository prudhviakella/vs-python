"""
fastapi_app/routers/customers.py — Customer API Routes
========================================================
Contains all /customers/* endpoints.

In main.py this router is included as:
    from fastapi_app.routers import customers
    app.include_router(customers.router, prefix="/customers", tags=["customers"])

The prefix="/customers" means:
    @router.get("/{customer_id}") → responds to GET /customers/{customer_id}
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from fastapi_app.models import CustomerRecord, OrderRecord

log = logging.getLogger(__name__)

# APIRouter groups related endpoints
# In main.py: app.include_router(router, prefix="/customers")
router = APIRouter()


@router.get("/{customer_id}", response_model=CustomerRecord)
async def get_customer(
    customer_id: int,
    conn=Depends(lambda: None),   # simplified — main.py injects the real dependency
) -> CustomerRecord:
    """
    Get a customer by ID.

    FastAPI automatically:
    - Extracts {customer_id} from the URL path
    - Validates it is an integer (returns 422 if not)
    - Serialises the CustomerRecord response to JSON

    Returns HTTP 404 if the customer is not found.
    """
    # In a real app: from fastapi_app.database import get_customer
    # customer = get_customer(conn, customer_id)

    # Simulated response for demo purposes
    if customer_id == 1001:
        return CustomerRecord(
            customer_id=1001, first_name="Danielle", last_name="Johnson",
            email="john21@example.net", city="Port Matthew", state="CO",
        )

    # raise HTTPException returns HTTP 404 with the detail message
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Customer {customer_id} not found",
    )


@router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: int) -> list[dict]:
    """Get recent orders for a customer."""
    # Simulated response
    return [
        {"order_id": 3001, "status": "Delivered", "total": 205.21},
        {"order_id": 3042, "status": "In Transit", "total": 1324.89},
    ]
