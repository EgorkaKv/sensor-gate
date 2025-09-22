from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.services.pubsub import PubSubService
from app.services.influxdb import InfluxDBService
from app.api.deps import get_pubsub_service

router = APIRouter()


async def get_influxdb_service() -> InfluxDBService:
    """FastAPI dependency to get InfluxDB service instance"""
    from app.services.influxdb import influxdb_service
    return influxdb_service


@router.get("/health", summary="Health Check", tags=["Health"])
async def health_check(
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service)
) -> Dict[str, Any]:
    """
    Check the health status of the SensorGate service and its dependencies.

    Returns:
        - Service status
        - Pub/Sub connectivity status
        - InfluxDB connectivity status
        - Configuration info
        - System metrics
    """
    # Check PubSub health
    pubsub_health = pubsub_service.health_check()

    # Check InfluxDB health
    influxdb_health = influxdb_service.health_check()

    # Determine overall health
    overall_status = "healthy"
    if pubsub_health["status"] != "healthy" or influxdb_health["status"] != "healthy":
        overall_status = "degraded"

    return {
        "service": "SensorGate",
        "version": settings.app_version,
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "pubsub": pubsub_health,
            "influxdb": influxdb_health
        },
        "config": {
            "supported_sensor_types": list(settings.sensor_topic_mapping.keys()),
            "debug_mode": settings.debug,
            "public_access_enabled": settings.public_access_enabled,
            "features": {
                "data_ingestion": True,
                "historical_queries": True,
                "device_management": True,
            }
        }
    }


@router.get("/health/live", summary="Liveness Probe", tags=["Health"])
async def liveness_probe() -> Dict[str, str]:
    """
    Simple liveness probe for Kubernetes or container orchestrators.

    Returns basic service status without dependency checks.
    """
    return {
        "status": "alive",
        "service": "SensorGate",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready", summary="Readiness Probe", tags=["Health"])
async def readiness_probe(
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service)
) -> Dict[str, Any]:
    """
    Readiness probe that checks if service is ready to handle requests.

    Includes dependency checks (Pub/Sub and InfluxDB connectivity).
    """
    pubsub_health = pubsub_service.health_check()
    influxdb_health = influxdb_service.health_check()

    is_ready = (pubsub_health["status"] == "healthy" and
                influxdb_health["status"] == "healthy")

    return {
        "status": "ready" if is_ready else "not_ready",
        "service": "SensorGate",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "pubsub": pubsub_health["status"],
            "influxdb": influxdb_health["status"]
        }
    }

