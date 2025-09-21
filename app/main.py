from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
# from app.middleware.metrics import MetricsMiddleware
from app.api import health, sensors, history, debug


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="IoT Gateway service for collecting and processing sensor data",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    # lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(health.router)
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(debug.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic service information"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled",
        "health_url": "/health",
        "authentication": {
            "public_access_enabled": settings.public_access_enabled,
            "api_key_required": not settings.public_access_enabled and len(settings.api_keys) > 0
        },
        "features": {
            "sensor_data_ingestion": True,
            "historical_data_query": True,
            "device_management": True,
            "aggregated_analytics": True
        }
    }
