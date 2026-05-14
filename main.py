from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from product import Product
from prometheus_client import Gauge, REGISTRY
from fastapi.middleware.cors import CORSMiddleware
from product_data import PRODUCTS

app = FastAPI(
    title="Products Microservice",
    version="1.0.4",
    description="Sample FastAPI microservice with Prometheus metrics"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://127.0.0.1:3000",
        "https://your-frontend-domain.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Custom Metric
# ---------------------------------------------------
if "total_products" in REGISTRY._names_to_collectors:
    TOTAL_PRODUCTS_GAUGE = REGISTRY._names_to_collectors["total_products"]
else:
    TOTAL_PRODUCTS_GAUGE = Gauge(
        "total_products",
        "Current total number of products"
    )

# Set initial value immediately
TOTAL_PRODUCTS_GAUGE.set(len(PRODUCTS))


# -------------------------------------------------------------------
# Instrumentator
# -------------------------------------------------------------------

instrumentator = Instrumentator()

instrumentator.instrument(app).expose(app)

# -------------------------------------------------------------------
# Health Endpoint
# -------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "products-microservice",
        "version": "1.0.4"
    }

# -------------------------------------------------------------------
# Products Endpoint
# -------------------------------------------------------------------

@app.get("/products")
async def get_products():
    # products_requests_total.inc()
    TOTAL_PRODUCTS_GAUGE.set(len(PRODUCTS))

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

    # update gauge
    TOTAL_PRODUCTS_GAUGE.set(len(PRODUCTS))

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