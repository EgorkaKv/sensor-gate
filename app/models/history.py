from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.models.sensor import SensorType


class AggregationType(str, Enum):
    """Available aggregation types for historical data"""
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    SUM = "sum"
    FIRST = "first"
    LAST = "last"


class HistoryQueryParams(BaseModel):
    """Query parameters for historical data requests"""
    start_time: datetime = Field(..., description="Start time for data query (ISO 8601)")
    end_time: datetime = Field(..., description="End time for data query (ISO 8601)")
    sensor_type: Optional[SensorType] = Field(None, description="Filter by sensor type")
    device_id: Optional[int] = Field(None, description="Filter by specific device ID", gt=0)
    latitude_min: Optional[float] = Field(None, description="Minimum latitude for location filter", ge=-90, le=90)
    latitude_max: Optional[float] = Field(None, description="Maximum latitude for location filter", ge=-90, le=90)
    longitude_min: Optional[float] = Field(None, description="Minimum longitude for location filter", ge=-180, le=180)
    longitude_max: Optional[float] = Field(None, description="Maximum longitude for location filter", ge=-180, le=180)
    aggregation: Optional[AggregationType] = Field(AggregationType.MEAN, description="Aggregation type for data")

    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator('latitude_max')
    @classmethod
    def validate_latitude_range(cls, v, info):
        """Validate latitude range"""
        if v is not None and 'latitude_min' in info.data and info.data['latitude_min'] is not None:
            if v <= info.data['latitude_min']:
                raise ValueError("latitude_max must be greater than latitude_min")
        return v

    @field_validator('longitude_max')
    @classmethod
    def validate_longitude_range(cls, v, info):
        """Validate longitude range"""
        if v is not None and 'longitude_min' in info.data and info.data['longitude_min'] is not None:
            if v <= info.data['longitude_min']:
                raise ValueError("longitude_max must be greater than longitude_min")
        return v


class HistoricalDataPoint(BaseModel):
    """Single historical data point"""
    timestamp: datetime = Field(..., description="Measurement timestamp")
    device_id: int = Field(..., description="Device identifier")
    sensor_type: SensorType = Field(..., description="Type of sensor")
    value: float = Field(..., description="Sensor reading value")
    latitude: float = Field(..., description="Device latitude")
    longitude: float = Field(..., description="Device longitude")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AggregatedDataPoint(BaseModel):
    """Aggregated historical data point"""
    sensor_type: SensorType = Field(..., description="Type of sensor")
    device_id: Optional[int] = Field(None, description="Device identifier (if filtered by device)")
    aggregation_type: AggregationType = Field(..., description="Type of aggregation applied")
    value: float = Field(..., description="Aggregated value")
    count: int = Field(..., description="Number of data points aggregated")
    start_time: datetime = Field(..., description="Start time of aggregation period")
    end_time: datetime = Field(..., description="End time of aggregation period")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HistoricalDataResponse(BaseModel):
    """Response model for historical data queries"""
    data: List[HistoricalDataPoint] = Field(..., description="Historical data points")
    total_count: int = Field(..., description="Total number of data points")
    query_params: Dict[str, Any] = Field(..., description="Query parameters used")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class AggregatedDataResponse(BaseModel):
    """Response model for aggregated historical data queries"""
    data: List[AggregatedDataPoint] = Field(..., description="Aggregated data points")
    total_count: int = Field(..., description="Total number of original data points")
    query_params: Dict[str, Any] = Field(..., description="Query parameters used")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class DeviceInfo(BaseModel):
    """Device information model"""
    device_id: int = Field(..., description="Device identifier")
    sensor_types: List[SensorType] = Field(..., description="Types of sensors on this device")
    first_seen: datetime = Field(..., description="First data point timestamp")
    last_seen: datetime = Field(..., description="Last data point timestamp")
    total_measurements: int = Field(..., description="Total number of measurements")
    last_location: Dict[str, float] = Field(..., description="Last known location")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeviceListResponse(BaseModel):
    """Response model for device list queries"""
    devices: List[DeviceInfo] = Field(..., description="List of devices")
    total_count: int = Field(..., description="Total number of devices")
    sensor_type_filter: Optional[SensorType] = Field(None, description="Applied sensor type filter")


class SensorTypeStats(BaseModel):
    """Statistics for a sensor type"""
    sensor_type: SensorType = Field(..., description="Type of sensor")
    device_count: int = Field(..., description="Number of devices with this sensor type")
    total_measurements: int = Field(..., description="Total measurements for this sensor type")
    first_measurement: datetime = Field(..., description="First measurement timestamp")
    last_measurement: datetime = Field(..., description="Last measurement timestamp")
    value_stats: Dict[str, float] = Field(..., description="Value statistics (min, max, mean)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SensorTypeStatsResponse(BaseModel):
    """Response model for sensor type statistics"""
    stats: List[SensorTypeStats] = Field(..., description="Statistics by sensor type")
    total_devices: int = Field(..., description="Total number of unique devices")
    total_measurements: int = Field(..., description="Total number of measurements")
    time_range: Dict[str, datetime] = Field(..., description="Overall time range of data")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
