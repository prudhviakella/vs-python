"""
fastapi_app/routers/products.py — Product API Routes
======================================================
Contains all /products/* endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, status

from fastapi_app.models import ProductRecord

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ProductRecord])
async def list_products(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    limit   : int           = Query(default=10, ge=1, le=100),
) -> list[ProductRecord]:
    """
    List products with optional category filter.

    Query parameters are defined as function parameters with Query():
    GET /products?category=Electronics&limit=5

    FastAPI automatically validates:
    - limit must be between 1 and 100 (ge=1, le=100)
    """

    # Simulated product data matching products.csv schema
    all_products = [
        ProductRecord(product_id=2001, product_name="Classic Monitor",   category="Electronics", brand="ProGear",     price=205.21, stock_quantity=238),
        ProductRecord(product_id=2002, product_name="Ultimate Perfume",  category="Beauty",      brand="LuxScent",    price=568.17, stock_quantity=10),
        ProductRecord(product_id=2003, product_name="Budget Headphones", category="Electronics", brand="SoundBasic",  price=29.99,  stock_quantity=0),
        ProductRecord(product_id=2004, product_name="Yoga Mat Pro",      category="Sports",      brand="FitGear",     price=45.00,  stock_quantity=150),
    ]

    if category:
        filtered = [p for p in all_products if p.category and p.category.lower() == category.lower()]
    else:
        filtered = [p for p in all_products if p.is_in_stock]

    return filtered[:limit]


@router.get("/{product_id}", response_model=ProductRecord)
async def get_product(product_id: int) -> ProductRecord:
    """Get a single product by ID."""
    if product_id == 2001:
        return ProductRecord(
            product_id=2001, product_name="Classic Monitor", category="Electronics",
            brand="ProGear", price=205.21, stock_quantity=238,
            description="High-resolution 27-inch display perfect for professional work.",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product {product_id} not found",
    )
