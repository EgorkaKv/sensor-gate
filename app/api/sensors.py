from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.models.sensor import SensorData, SensorDataResponse
from app.services.pubsub import PubSubService
from app.api.deps import get_pubsub_service, get_authenticated_request

router = APIRouter()
# logger = get_logger("sensor_api")


@router.post(
    "/sensors/data",
    response_model=SensorDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Sensor Data",
    tags=["Sensors"]
)
async def submit_sensor_data(
    sensor_data: SensorData,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> SensorDataResponse:
    """
    Submit sensor data from IoT devices.

    This endpoint receives sensor readings and forwards them to the appropriate
    Pub/Sub topic based on sensor type for further processing.

    **Supported Sensor Types:**
    - `temperature`: Temperature readings in Celsius (-273.15 to 1000°C)
    - `humidity`: Humidity percentage (0 to 100%)
    - `ndir`: NDIR CO2 sensor readings (0 to 50000 ppm)

    **Authentication:**
    - Requires valid API key in `X-API-Key` header

    **Request Body:**
    - `device_id`: Unique identifier for the IoT device (positive integer)
    - `sensor_type`: Type of sensor (temperature, humidity, ndir)
    - `value`: Sensor reading value (float/decimal)
    - `latitude`: Device location latitude (-90 to 90)
    - `longitude`: Device location longitude (-180 to 180)
    - `timestamp`: When the measurement was taken (ISO format)

    **Response:**
    - Confirmation of successful data reception and processing
    """
    try:

        # Convert to dictionary for Pub/Sub
        sensor_dict = sensor_data.dict()
        sensor_dict['sensor_type'] = sensor_data.sensor_type.value
        sensor_dict['timestamp'] = sensor_data.timestamp.isoformat()

        # Publish to Pub/Sub
        try:
            message_id = pubsub_service.publish_sensor_data(
                sensor_type=sensor_data.sensor_type.value,
                data=sensor_dict
            )


        except Exception as pubsub_error:


            print('Pub/Sub error:', pubsub_error)

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to process sensor data. Please try again later."
            )

        return SensorDataResponse(
            device_id=sensor_data.device_id,
            sensor_type=sensor_data.sensor_type,
            processed_at=datetime.utcnow()
        )

    except ValidationError as validation_error:
        # Log validation error
        print('Validation error:', validation_error)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data validation failed: {validation_error}"
        )

    except Exception as unexpected_error:
        print('Unexpected error:', unexpected_error)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing sensor data"
        )


@router.get(
    "/sensors/types",
    summary="Get Supported Sensor Types",
    tags=["Sensors"]
)
async def get_supported_sensor_types(
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> Dict[str, Any]:
    """
    Get list of supported sensor types and their validation rules.

    **Authentication:**
    - Requires valid API key in `X-API-Key` header

    **Response:**
    - List of supported sensor types with validation constraints
    """
    return {
        "supported_types": [
            {
                "type": "temperature",
                "description": "Temperature sensor readings in Celsius",
                "value_range": {
                    "min": -273.15,
                    "max": 1000,
                    "unit": "°C"
                }
            },
            {
                "type": "humidity",
                "description": "Humidity sensor readings as percentage",
                "value_range": {
                    "min": 0,
                    "max": 100,
                    "unit": "%"
                }
            },
            {
                "type": "ndir",
                "description": "NDIR CO2 sensor readings",
                "value_range": {
                    "min": 0,
                    "max": 50000,
                    "unit": "ppm"
                }
            }
        ],
        "validation_rules": {
            "device_id": "Positive integer",
            "latitude": "Float between -90 and 90",
            "longitude": "Float between -180 and 180",
            "timestamp": "ISO format datetime, not in future"
        }
    }
