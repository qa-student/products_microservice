from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import uvicorn
from pydantic import BaseModel
from typing import Optional
from product import Product


app = FastAPI(
    title="Products Microservice",
    version="1.0.0",
    description="Sample FastAPI microservice with Prometheus metrics"
)

# -------------------------------------------------------------------
# Prometheus Custom Metrics
# -------------------------------------------------------------------

# products_requests_total = Counter(
#     "products_requests_total",
#     "Total number of requests to the products endpoint"
# )

# -------------------------------------------------------------------
# Sample Product Data
# -------------------------------------------------------------------

PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Mouse",
        "price": 24.99,
        "category": "Electronics"
    },
    {
        "id": 2,
        "name": "Mechanical Keyboard",
        "price": 89.99,
        "category": "Electronics"
    },
    {
        "id": 3,
        "name": "Water Bottle",
        "price": 14.50,
        "category": "Home"
    },
    {
        "id": 4,
        "name": "Running Shoes",
        "price": 120.00,
        "category": "Sports"
    }
]

# -------------------------------------------------------------------
# Metrics Endpoint
# -------------------------------------------------------------------

Instrumentator().instrument(app).expose(app)

# This automatically exposes:
# GET /metrics

# -------------------------------------------------------------------
# Health Endpoint
# -------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "products-microservice",
        "version": "1.0.0"
    }

# -------------------------------------------------------------------
# Products Endpoint
# -------------------------------------------------------------------

@app.get("/products")
async def get_products():
    # products_requests_total.inc()

    return JSONResponse(
        content={
            "count": len(PRODUCTS),
            "products": PRODUCTS
        }
    )


@app.get("/products/{product_id}")
async def get_product_by_id(product_id: int):

    for product in PRODUCTS:
        if product["id"] == product_id:
            return JSONResponse(content=product)

    return JSONResponse(
        status_code=404,
        content={
            "message": f"Product with id {product_id} not found"
        }
    )


@app.post("/products")
async def add_product(product: Product):

    new_id = max(p["id"] for p in PRODUCTS) + 1 if PRODUCTS else 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category
    }

    PRODUCTS.append(new_product)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Product created successfully",
            "product": new_product
        }
    )

# ---------------------------------------------------
# Liveness Probe
# ---------------------------------------------------

@app.get("/live")
async def liveness_probe():
    return {
        "status": "alive"
    }

# ---------------------------------------------------
# Readiness Probe
# ---------------------------------------------------

@app.get("/ready")
async def readiness_probe():

    # Example dependency checks
    database_connected = True
    cache_connected = True

    if not database_connected or not cache_connected:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready"
            }
        )

    return {
        "status": "ready"
    }

# -------------------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Products Microservice is running"
    }

# -------------------------------------------------------------------
# Run Application
# -------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )