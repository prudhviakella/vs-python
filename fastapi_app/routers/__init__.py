"""
fastapi_app/routers/__init__.py
================================
This __init__.py makes the routers/ directory a Python sub-package.

The routers are split into separate files by resource type (customers, products, orders).
Each file defines an APIRouter that is included in main.py.

This structure is the standard FastAPI pattern for larger applications.
In Module 01, a single-file FastAPI app is fine.
This structure is shown so students understand it when they see it in the wild.
"""
