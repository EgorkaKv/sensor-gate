from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.pubsub import PubSubService
from app.api.deps import get_pubsub_service, get_authenticated_request

router = APIRouter()


@router.get(
    "/debug/pubsub/messages",
    summary="Get Mock Pub/Sub Messages",
    tags=["Debug"]
)
async def get_mock_pubsub_messages(
    topic_name: Optional[str] = None,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Get all mock Pub/Sub messages for debugging.

    **Only available when using mock Pub/Sub (debug mode or explicitly enabled)**

    **Parameters:**
    - `topic_name`: Optional filter by specific topic name

    **Response:**
    - All published messages grouped by topic
    - Message metadata including timestamps and IDs
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug endpoints are only available in debug mode"
        )

    mock_data = pubsub_service.get_mock_data()
    if mock_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mock Pub/Sub is not enabled. Set SENSORGATE_DEBUG=true or SENSORGATE_USE_PUBSUB_MOCK=true"
        )


    messages = mock_data.get("published_messages", {})
    stats = mock_data.get("stats", {})

    if topic_name:
        messages = {topic_name: messages.get(topic_name, [])}

    return {
        "messages": messages,
        "stats": stats,
        "filter": {"topic_name": topic_name} if topic_name else None,
        "using_mock": True
    }


@router.get(
    "/debug/pubsub/stats",
    summary="Get Mock Pub/Sub Statistics",
    tags=["Debug"]
)
async def get_mock_pubsub_stats(
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Get mock Pub/Sub statistics and usage information.

    **Only available when using mock Pub/Sub (debug mode or explicitly enabled)**

    **Response:**
    - Total message count
    - Messages per topic
    - Topic statistics
    - Mock configuration info
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug endpoints are only available in debug mode"
        )

    mock_data = pubsub_service.get_mock_data()
    if mock_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mock Pub/Sub is not enabled"
        )


    return {
        "stats": mock_data.get("stats", {}),
        "configuration": {
            "debug_mode": settings.debug,
            "use_pubsub_mock": settings.use_pubsub_mock,
            "pubsub_mock_auto_enable": settings.pubsub_mock_auto_enable,
            "topic_mapping": settings.sensor_topic_mapping
        },
        "using_mock": True
    }


@router.delete(
    "/debug/pubsub/messages",
    summary="Clear Mock Pub/Sub Messages",
    tags=["Debug"]
)
async def clear_mock_pubsub_messages(
    topic_name: Optional[str] = None,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Clear mock Pub/Sub messages for testing.

    **Only available when using mock Pub/Sub (debug mode or explicitly enabled)**

    **Parameters:**
    - `topic_name`: Optional - clear only specific topic (if not provided, clears all)

    **Response:**
    - Confirmation of cleared messages
    - Updated statistics
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug endpoints are only available in debug mode"
        )

    success = pubsub_service.clear_mock_data(topic_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mock Pub/Sub is not enabled"
        )



    # Get updated stats
    mock_data = pubsub_service.get_mock_data()
    updated_stats = mock_data.get("stats", {}) if mock_data else {}

    return {
        "message": f"Mock messages cleared for topic: {topic_name}" if topic_name else "All mock messages cleared",
        "cleared_topic": topic_name,
        "updated_stats": updated_stats,
        "using_mock": True
    }


@router.get(
    "/debug/pubsub/topic/{topic_name}/messages",
    summary="Get Messages for Specific Topic",
    tags=["Debug"]
)
async def get_topic_messages(
    topic_name: str,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Get all messages for a specific topic.

    **Only available when using mock Pub/Sub (debug mode or explicitly enabled)**

    **Path Parameters:**
    - `topic_name`: Name of the topic (e.g., 'sensor-temperature', 'sensor-humidity', 'sensor-ndir')

    **Response:**
    - All messages for the specified topic
    - Message count and topic statistics
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug endpoints are only available in debug mode"
        )

    mock_data = pubsub_service.get_mock_data()
    if mock_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mock Pub/Sub is not enabled"
        )

    messages = mock_data.get("published_messages", {})
    topic_messages = messages.get(topic_name, [])

    if not topic_messages and topic_name not in messages:
        # Check if topic name is valid
        valid_topics = list(settings.sensor_topic_mapping.values())
        if topic_name not in valid_topics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_name}' not found. Valid topics: {valid_topics}"
            )


    return {
        "topic_name": topic_name,
        "messages": topic_messages,
        "message_count": len(topic_messages),
        "valid_topic": topic_name in settings.sensor_topic_mapping.values(),
        "using_mock": True
    }


@router.get(
    "/debug/config",
    summary="Get Debug Configuration",
    tags=["Debug"]
)
async def get_debug_config(
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Get current debug and mock configuration.

    **Only available in debug mode**

    **Response:**
    - Current debug settings
    - Mock configuration
    - Service status
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug endpoints are only available in debug mode"
        )

    # Determine if mock is active
    using_mock = settings.use_pubsub_mock or (settings.pubsub_mock_auto_enable and settings.debug)

    return {
        "debug_mode": settings.debug,
        "mock_configuration": {
            "use_pubsub_mock": settings.use_pubsub_mock,
            "pubsub_mock_auto_enable": settings.pubsub_mock_auto_enable,
            "using_mock": using_mock
        },
        "service_info": {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "log_level": settings.log_level,
            "metrics_enabled": settings.metrics_enabled
        },
        "pubsub_topics": settings.sensor_topic_mapping,
        "debug_endpoints": {
            "messages": "/api/v1/debug/pubsub/messages",
            "stats": "/api/v1/debug/pubsub/stats",
            "clear": "/api/v1/debug/pubsub/messages (DELETE)",
            "topic_messages": "/api/v1/debug/pubsub/topic/{topic_name}/messages"
        }
    }
