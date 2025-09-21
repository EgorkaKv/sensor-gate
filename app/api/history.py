import time
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.history import (
    HistoryQueryParams, HistoricalDataResponse, AggregatedDataResponse,
    DeviceListResponse, SensorTypeStatsResponse, AggregationType
)
from app.models.sensor import SensorType
from app.services.influxdb import InfluxDBService
from app.api.deps import get_authenticated_request

router = APIRouter()


async def get_influxdb_service() -> InfluxDBService:
    """FastAPI dependency to get InfluxDB service instance"""
    from app.services.influxdb import influxdb_service
    return influxdb_service


@router.get(
    "/sensors/history",
    response_model=HistoricalDataResponse,
    summary="Get Historical Sensor Data",
    tags=["History"]
)
async def get_historical_data(
    start_time: datetime = Query(..., description="Start time (ISO 8601 format)"),
    end_time: datetime = Query(..., description="End time (ISO 8601 format)"),
    sensor_type: Optional[SensorType] = Query(None, description="Filter by sensor type"),
    device_id: Optional[int] = Query(None, description="Filter by device ID", gt=0),
    latitude_min: Optional[float] = Query(None, description="Minimum latitude", ge=-90, le=90),
    latitude_max: Optional[float] = Query(None, description="Maximum latitude", ge=-90, le=90),
    longitude_min: Optional[float] = Query(None, description="Minimum longitude", ge=-180, le=180),
    longitude_max: Optional[float] = Query(None, description="Maximum longitude", ge=-180, le=180),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> HistoricalDataResponse:
    """
    Retrieve historical sensor data with optional filtering.

    **Parameters:**
    - `start_time`: Start time for data query (ISO 8601 format, e.g., '2024-01-15T12:00:00Z')
    - `end_time`: End time for data query (ISO 8601 format)
    - `sensor_type`: Optional filter by sensor type (temperature, humidity, ndir)
    - `device_id`: Optional filter by specific device ID
    - `latitude_min/max`: Optional location-based filtering by latitude range
    - `longitude_min/max`: Optional location-based filtering by longitude range

    **Response:**
    - List of historical data points matching the criteria
    - Total count and execution time information

    **Examples:**
    - Get all temperature data for last hour:
      `?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&sensor_type=temperature`
    - Get data from specific device:
      `?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&device_id=12345`
    """
    start_query_time = time.time()

    try:
        # Create query parameters
        query_params = HistoryQueryParams(
            start_time=start_time,
            end_time=end_time,
            sensor_type=sensor_type,
            device_id=device_id,
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max
        )


        # Query historical data
        data_points = await influxdb_service.query_historical_data(query_params)

        execution_time = (time.time() - start_query_time) * 1000

        response = HistoricalDataResponse(
            data=data_points,
            total_count=len(data_points),
            query_params=query_params.model_dump(),
            execution_time_ms=execution_time
        )

        return response

    except ValueError as validation_error:

        print('Validation error:', validation_error)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query validation failed: {validation_error}"
        )

    except Exception as e:

        print('get_historical_data Unexpected error:', e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical data"
        )


@router.get(
    "/sensors/history/aggregated",
    response_model=AggregatedDataResponse,
    summary="Get Aggregated Historical Data",
    tags=["History"]
)
async def get_aggregated_data(
    start_time: datetime = Query(..., description="Start time (ISO 8601 format)"),
    end_time: datetime = Query(..., description="End time (ISO 8601 format)"),
    aggregation: AggregationType = Query(AggregationType.MEAN, description="Aggregation type"),
    sensor_type: Optional[SensorType] = Query(None, description="Filter by sensor type"),
    device_id: Optional[int] = Query(None, description="Filter by device ID", gt=0),
    latitude_min: Optional[float] = Query(None, description="Minimum latitude", ge=-90, le=90),
    latitude_max: Optional[float] = Query(None, description="Maximum latitude", ge=-90, le=90),
    longitude_min: Optional[float] = Query(None, description="Minimum longitude", ge=-180, le=180),
    longitude_max: Optional[float] = Query(None, description="Maximum longitude", ge=-180, le=180),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> AggregatedDataResponse:
    """
    Retrieve aggregated historical sensor data.

    **Aggregation Types:**
    - `mean`: Average value
    - `min`: Minimum value
    - `max`: Maximum value
    - `count`: Number of measurements
    - `sum`: Sum of all values
    - `first`: First measurement
    - `last`: Last measurement

    **Parameters:**
    Similar to historical data endpoint, with additional aggregation parameter.

    **Response:**
    - Aggregated data points with statistics
    - Original data point count and execution time
    """
    start_query_time = time.time()

    try:
        # Create query parameters
        query_params = HistoryQueryParams(
            start_time=start_time,
            end_time=end_time,
            sensor_type=sensor_type,
            device_id=device_id,
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max,
            aggregation=aggregation
        )


        # Query aggregated data
        aggregated_points = await influxdb_service.query_aggregated_data(query_params)

        # Calculate total original data points
        total_original_count = sum(point.count for point in aggregated_points)

        execution_time = (time.time() - start_query_time) * 1000


        response = AggregatedDataResponse(
            data=aggregated_points,
            total_count=total_original_count,
            query_params=query_params.model_dump(),
            execution_time_ms=execution_time
        )


        return response

    except ValueError as validation_error:


        print('get_aggregated_data Validation error:', validation_error)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query validation failed: {validation_error}"
        )

    except Exception as e:



        print('get_aggregated_data Unexpected error:', e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve aggregated data"
        )


@router.get(
    "/sensors/history/by-sensor-type/{sensor_type}",
    response_model=HistoricalDataResponse,
    summary="Get Historical Data by Sensor Type",
    tags=["History"]
)
async def get_data_by_sensor_type(
    sensor_type: SensorType,
    start_time: datetime = Query(..., description="Start time (ISO 8601 format)"),
    end_time: datetime = Query(..., description="End time (ISO 8601 format)"),
    latitude_min: Optional[float] = Query(None, description="Minimum latitude", ge=-90, le=90),
    latitude_max: Optional[float] = Query(None, description="Maximum latitude", ge=-90, le=90),
    longitude_min: Optional[float] = Query(None, description="Minimum longitude", ge=-180, le=180),
    longitude_max: Optional[float] = Query(None, description="Maximum longitude", ge=-180, le=180),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> HistoricalDataResponse:
    """
    Get historical data for all devices of a specific sensor type.

    **Path Parameters:**
    - `sensor_type`: Type of sensor (temperature, humidity, ndir)

    **Query Parameters:**
    - `start_time`: Start time for data query
    - `end_time`: End time for data query
    - Location filters (optional)

    **Response:**
    - All historical data points for the specified sensor type
    - Includes data from all devices with that sensor type
    """
    return await get_historical_data(
        start_time=start_time,
        end_time=end_time,
        sensor_type=sensor_type,
        device_id=None,
        latitude_min=latitude_min,
        latitude_max=latitude_max,
        longitude_min=longitude_min,
        longitude_max=longitude_max,
        influxdb_service=influxdb_service,
        api_key=api_key
    )


@router.get(
    "/sensors/history/by-device/{device_id}",
    response_model=HistoricalDataResponse,
    summary="Get Historical Data by Device ID",
    tags=["History"]
)
async def get_data_by_device(
    device_id: int,
    start_time: datetime = Query(..., description="Start time (ISO 8601 format)"),
    end_time: datetime = Query(..., description="End time (ISO 8601 format)"),
    sensor_type: Optional[SensorType] = Query(None, description="Filter by sensor type"),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> HistoricalDataResponse:
    """
    Get historical data for a specific device.

    **Path Parameters:**
    - `device_id`: Unique device identifier

    **Query Parameters:**
    - `start_time`: Start time for data query
    - `end_time`: End time for data query
    - `sensor_type`: Optional filter by sensor type

    **Response:**
    - All historical data points for the specified device
    - Can be filtered by sensor type if device has multiple sensors
    """
    return await get_historical_data(
        start_time=start_time,
        end_time=end_time,
        sensor_type=sensor_type,
        device_id=device_id,
        latitude_min=None,
        latitude_max=None,
        longitude_min=None,
        longitude_max=None,
        influxdb_service=influxdb_service,
        api_key=api_key
    )


@router.get(
    "/sensors/devices",
    response_model=DeviceListResponse,
    summary="Get All Device IDs",
    tags=["Devices"]
)
async def get_all_devices(
    sensor_type: Optional[SensorType] = Query(None, description="Filter devices by sensor type"),
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> DeviceListResponse:
    """
    Get list of all device IDs with their information.

    **Query Parameters:**
    - `sensor_type`: Optional filter to get only devices with specific sensor type

    **Response:**
    - List of devices with metadata:
      - Device ID
      - Available sensor types
      - First and last measurement timestamps
      - Total number of measurements
      - Last known location

    **Examples:**
    - Get all devices: `GET /api/v1/sensors/devices`
    - Get only temperature devices: `GET /api/v1/sensors/devices?sensor_type=temperature`
    """
    start_query_time = time.time()

    try:

        # Get device list
        devices = await influxdb_service.get_device_list(sensor_type)

        execution_time = (time.time() - start_query_time) * 1000


        response = DeviceListResponse(
            devices=devices,
            total_count=len(devices),
            sensor_type_filter=sensor_type
        )

        return response

    except Exception as e:

        print('get_all_devices Unexpected error:', e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device list"
        )


@router.get(
    "/sensors/stats",
    response_model=SensorTypeStatsResponse,
    summary="Get Sensor Type Statistics",
    tags=["Statistics"]
)
async def get_sensor_stats(
    influxdb_service: InfluxDBService = Depends(get_influxdb_service),
    api_key: Optional[str] = Depends(get_authenticated_request)
) -> SensorTypeStatsResponse:
    """
    Get comprehensive statistics for all sensor types.

    **Response:**
    - Statistics by sensor type:
      - Number of devices
      - Total measurements
      - Time range of data
      - Value statistics (min, max, mean)
    - Overall system statistics

    **Use Cases:**
    - System overview and monitoring
    - Data quality assessment
    - Capacity planning
    """
    start_query_time = time.time()

    try:


        # Get sensor type statistics
        sensor_stats = await influxdb_service.get_sensor_type_stats()

        execution_time = (time.time() - start_query_time) * 1000

        # Calculate overall statistics
        total_devices = sum(stat.device_count for stat in sensor_stats)
        total_measurements = sum(stat.total_measurements for stat in sensor_stats)

        # Find overall time range
        if sensor_stats:
            first_measurement = min(stat.first_measurement for stat in sensor_stats)
            last_measurement = max(stat.last_measurement for stat in sensor_stats)
            time_range = {
                "first_measurement": first_measurement,
                "last_measurement": last_measurement
            }
        else:
            time_range = {
                "first_measurement": datetime.now(UTC),
                "last_measurement": datetime.now(UTC)
            }

        response = SensorTypeStatsResponse(
            stats=sensor_stats,
            total_devices=total_devices,
            total_measurements=total_measurements,
            time_range=time_range
        )

        return response

    except Exception as e:
        print('get_sensor_stats Unexpected error:', e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sensor statistics"
        )
