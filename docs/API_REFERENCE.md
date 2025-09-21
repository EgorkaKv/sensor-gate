# API Reference

## Overview

The SensorGate API provides RESTful endpoints for IoT devices to submit sensor data and for administrators to monitor system health.

**Base URL**: `http://your-domain/api/v1`  
**Authentication**: API Key (X-API-Key header)  
**Content Type**: `application/json`

## Authentication

All API endpoints require authentication via API key in the request header:

```http
X-API-Key: your-api-key-here
```

## Sensor Data Endpoints

### Submit Sensor Data

Submit sensor readings from IoT devices.

**Endpoint**: `POST /sensors/data`

**Request Headers**:
```http
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "2024-01-15T12:30:00Z"
}
```

**Field Descriptions**:
- `device_id` (integer, required): Unique identifier for the IoT device. Must be positive.
- `sensor_type` (string, required): Type of sensor. Valid values: `temperature`, `humidity`, `ndir`
- `value` (number, required): Sensor reading value. Range depends on sensor type.
- `latitude` (number, required): GPS latitude coordinate (-90 to 90)
- `longitude` (number, required): GPS longitude coordinate (-180 to 180)
- `timestamp` (string, required): ISO 8601 formatted timestamp. Cannot be in the future.

**Sensor Value Ranges**:
- `temperature`: -273.15 to 1000 (Celsius)
- `humidity`: 0 to 100 (percentage)
- `ndir`: 0 to 50000 (ppm CO2)

**Success Response** (201 Created):
```json
{
    "message": "Data received successfully",
    "device_id": 12345,
    "sensor_type": "temperature",
    "processed_at": "2024-01-15T12:30:01.123Z"
}
```

**Error Responses**:

*401 Unauthorized*:
```json
{
    "detail": "Missing API key. Provide X-API-Key header."
}
```

*422 Unprocessable Entity*:
```json
{
    "detail": "Data validation failed: Temperature value out of valid range (-273.15 to 1000°C)"
}
```

*503 Service Unavailable*:
```json
{
    "detail": "Failed to process sensor data. Please try again later."
}
```

### Get Supported Sensor Types

Retrieve information about supported sensor types and their validation rules.

**Endpoint**: `GET /sensors/types`

**Request Headers**:
```http
X-API-Key: your-api-key
```

**Success Response** (200 OK):
```json
{
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
```

## Health Check Endpoints

### Comprehensive Health Check

Get detailed health status of the service and its dependencies.

**Endpoint**: `GET /health`

**Success Response** (200 OK):
```json
{
    "service": "SensorGate",
    "version": "0.1.0",
    "status": "healthy",
    "timestamp": "2024-01-15T12:30:00.000Z",
    "checks": {
        "pubsub": {
            "status": "healthy",
            "circuit_breaker_state": "CLOSED",
            "project_id": "your-gcp-project",
            "available_topics": [
                "sensor-temperature",
                "sensor-humidity",
                "sensor-ndir"
            ]
        }
    },
    "config": {
        "supported_sensor_types": ["temperature", "humidity", "ndir"],
        "metrics_enabled": true,
        "debug_mode": false
    }
}
```

### Liveness Probe

Simple endpoint for Kubernetes liveness checks.

**Endpoint**: `GET /health/live`

**Success Response** (200 OK):
```json
{
    "status": "alive",
    "service": "SensorGate",
    "timestamp": "2024-01-15T12:30:00.000Z"
}
```

### Readiness Probe

Endpoint for Kubernetes readiness checks with dependency validation.

**Endpoint**: `GET /health/ready`

**Success Response** (200 OK):
```json
{
    "status": "ready",
    "service": "SensorGate",
    "timestamp": "2024-01-15T12:30:00.000Z",
    "dependencies": {
        "pubsub": "healthy"
    }
}
```

**Failure Response** (200 OK with not_ready status):
```json
{
    "status": "not_ready",
    "service": "SensorGate",
    "timestamp": "2024-01-15T12:30:00.000Z",
    "dependencies": {
        "pubsub": "unhealthy"
    }
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success (GET requests)
- `201` - Created (POST requests)
- `400` - Bad Request (malformed JSON)
- `401` - Unauthorized (missing/invalid API key)
- `422` - Unprocessable Entity (validation errors)
- `500` - Internal Server Error (unexpected errors)
- `503` - Service Unavailable (Pub/Sub issues)

### Error Response Format

All error responses follow this format:
```json
{
    "detail": "Human-readable error message"
}
```

For validation errors, the detail may include specific field information:
```json
{
    "detail": "Data validation failed: [{'loc': ['value'], 'msg': 'Temperature value out of valid range', 'type': 'value_error'}]"
}
```

## Rate Limiting

Currently, rate limiting is not implemented at the API level. Clients should implement their own rate limiting to avoid overwhelming the service.

**Recommended client-side limits**:
- Maximum 100 requests per second per API key
- Maximum 1000 requests per minute per device

## Example Usage

### Python Client Example

```python
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://your-sensorgate-domain/api/v1"
API_KEY = "your-api-key-here"

# Headers
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Send temperature data
sensor_data = {
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

response = requests.post(
    f"{API_BASE_URL}/sensors/data",
    headers=headers,
    json=sensor_data
)

if response.status_code == 201:
    print("Data sent successfully:", response.json())
else:
    print("Error:", response.status_code, response.json())
```

### cURL Example

```bash
curl -X POST "http://your-sensorgate-domain/api/v1/sensors/data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "2024-01-15T12:30:00Z"
  }'
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const apiClient = axios.create({
    baseURL: 'http://your-sensorgate-domain/api/v1',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key-here'
    }
});

async function sendSensorData(deviceId, sensorType, value, lat, lng) {
    try {
        const response = await apiClient.post('/sensors/data', {
            device_id: deviceId,
            sensor_type: sensorType,
            value: value,
            latitude: lat,
            longitude: lng,
            timestamp: new Date().toISOString()
        });
        
        console.log('Success:', response.data);
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Usage
sendSensorData(12345, 'temperature', 23.5, 55.7558, 37.6176);
```

## OpenAPI/Swagger Documentation

When running in debug mode, interactive API documentation is available at:
- Swagger UI: `http://your-domain/docs`
- ReDoc: `http://your-domain/redoc`
- OpenAPI JSON: `http://your-domain/openapi.json`
