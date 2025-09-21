from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import Union

from pydantic import BaseModel, Field, field_validator


class SensorType(str, Enum):
    """Supported sensor types"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    NDIR = "ndir"


class SensorData(BaseModel):
    """Model for sensor data validation"""
    device_id: int = Field(..., description="Unique device identifier", gt=0)
    sensor_type: SensorType = Field(..., description="Type of sensor")
    value: Union[float, Decimal] = Field(..., description="Sensor reading value")
    latitude: Union[float, Decimal] = Field(..., description="Device latitude", ge=-90, le=90)
    longitude: Union[float, Decimal] = Field(..., description="Device longitude", ge=-180, le=180)
    timestamp: datetime = Field(..., description="Measurement timestamp")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is not in the future"""
        if v > datetime.now(UTC):
            raise ValueError("Timestamp cannot be in the future")
        return v

    @field_validator('value')
    @classmethod
    def validate_sensor_value(cls, v, info):
        """Validate sensor value based on sensor type"""
        if 'sensor_type' in info.data:
            sensor_type = info.data['sensor_type']

            if sensor_type == SensorType.TEMPERATURE:
                # Temperature in Celsius: -273.15 to 1000
                if not -273.15 <= v <= 1000:
                    raise ValueError("Temperature value out of valid range (-273.15 to 1000°C)")
            elif sensor_type == SensorType.HUMIDITY:
                # Humidity percentage: 0 to 100
                if not 0 <= v <= 100:
                    raise ValueError("Humidity value out of valid range (0 to 100%)")
            elif sensor_type == SensorType.NDIR:
                # NDIR CO2 sensor: 0 to 50000 ppm
                if not 0 <= v <= 50000:
                    raise ValueError("NDIR value out of valid range (0 to 50000 ppm)")

        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class SensorDataResponse(BaseModel):
    """Response model for successful sensor data submission"""
    message: str = "Data received successfully"
    device_id: int
    sensor_type: SensorType
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
