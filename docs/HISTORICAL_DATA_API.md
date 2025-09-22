# Historical Data API Guide

## Overview

SensorGate now supports retrieving historical sensor data from InfluxDB Cloud. New endpoints have been added for various query scenarios.

## New Endpoints

### 1. Retrieve Historical Data
**GET** `/api/v1/sensors/history`

Base endpoint for retrieving historical data with filtering.

**Parameters:**
- `start_time` (required): Start time in ISO 8601 format
- `end_time` (required): End time in ISO 8601 format
- `sensor_type` (optional): Sensor type (temperature, humidity, ndir)
- `device_id` (optional): Specific device ID
- `latitude_min/max` (optional): Latitude filter
- `longitude_min/max` (optional): Longitude filter

**Example request:**
```http
GET /api/v1/sensors/history?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&sensor_type=temperature
```

### 2. Retrieve Aggregated Data
**GET** `/api/v1/sensors/history/aggregated`

Retrieve aggregated data with various aggregation types.

**Additional parameters:**
- `aggregation`: Aggregation type (mean, min, max, count, sum, first, last)

**Example request:**
```http
GET /api/v1/sensors/history/aggregated?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&aggregation=mean&sensor_type=temperature
```

### 3. Data by Sensor Type
**GET** `/api/v1/sensors/history/by-sensor-type/{sensor_type}`

Retrieve data for all devices of a specific sensor type.

**Example request:**
```http
GET /api/v1/sensors/history/by-sensor-type/temperature?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z
```

### 4. Data by Device ID
**GET** `/api/v1/sensors/history/by-device/{device_id}`

Retrieve data for a specific device.

**Example request:**
```http
GET /api/v1/sensors/history/by-device/12345?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z
```

### 5. List All Devices
**GET** `/api/v1/sensors/devices`

Retrieve a list of all devices with metadata.

**Parameters:**
- `sensor_type` (optional): Filter by sensor type

**Example request:**
```http
GET /api/v1/sensors/devices?sensor_type=temperature
```

### 6. Sensor Type Statistics
**GET** `/api/v1/sensors/stats`

Retrieve general statistics for all sensor types.

**Example request:**
```http
GET /api/v1/sensors/stats
```

## Response Formats

### Historical Data
```json
{
  "data": [
    {
      "timestamp": "2024-01-15T12:30:00Z",
      "device_id": 12345,
      "sensor_type": "temperature",
      "value": 23.5,
      "latitude": 55.7558,
      "longitude": 37.6176
    }
  ],
  "total_count": 150,
  "query_params": {...},
  "execution_time_ms": 125.5
}
```

### Aggregated Data
```json
{
  "data": [
    {
      "sensor_type": "temperature",
      "device_id": 12345,
      "aggregation_type": "mean",
      "value": 23.2,
      "count": 150,
      "start_time": "2024-01-15T12:00:00Z",
      "end_time": "2024-01-15T13:00:00Z"
    }
  ],
  "total_count": 150,
  "query_params": {...},
  "execution_time_ms": 89.3
}
```

### Device List
```json
{
  "devices": [
    {
      "device_id": 12345,
      "sensor_types": ["temperature", "humidity"],
      "first_seen": "2024-01-01T00:00:00Z",
      "last_seen": "2024-01-15T12:59:59Z",
      "total_measurements": 5240,
      "last_location": {
        "latitude": 55.7558,
        "longitude": 37.6176
      }
    }
  ],
  "total_count": 25,
  "sensor_type_filter": "temperature"
}
```

## Usage Examples

### Python Client
```python
import requests
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://your-sensorgate-domain/api/v1"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

# Get data from the last hour
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

params = {
    "start_time": start_time.isoformat() + "Z",
    "end_time": end_time.isoformat() + "Z",
    "sensor_type": "temperature"
}

response = requests.get(
    f"{API_BASE_URL}/sensors/history",
    headers=headers,
    params=params
)

if response.status_code == 200:
    data = response.json()
    print(f"Retrieved {data['total_count']} data points")
    for point in data['data']:
        print(f"Device {point['device_id']}: {point['value']}°C at {point['timestamp']}")
```

### cURL Examples
```bash
# Get temperature data from the last hour
curl -X GET "http://your-domain/api/v1/sensors/history?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&sensor_type=temperature" \
  -H "X-API-Key: your-api-key"

# Get aggregated data (mean)
curl -X GET "http://your-domain/api/v1/sensors/history/aggregated?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&aggregation=mean" \
  -H "X-API-Key: your-api-key"

# Get device list
curl -X GET "http://your-domain/api/v1/sensors/devices" \
  -H "X-API-Key: your-api-key"
```

## InfluxDB Configuration

Add to your `.env` file:

```env
# InfluxDB settings
SENSORGATE_INFLUXDB_URL=https://us-east-1-1.aws.cloud2.influxdata.com
SENSORGATE_INFLUXDB_TOKEN=GdqEFmuTLknVX_WxJgeJVekhjKN555UBk2A38zFmKdvpz473K64HsYGukC_XtDQXvOF6gX2hafgI9YfqHSDGFw==
SENSORGATE_INFLUXDB_ORG=IoT-lab3
SENSORGATE_INFLUXDB_BUCKET=iot-sensors
SENSORGATE_INFLUXDB_USERNAME=root
SENSORGATE_INFLUXDB_PASSWORD=influx321pass
```

## Health Check

The updated health check now includes InfluxDB verification:

```http
GET /api/v1/health
```

The response will include status for both Pub/Sub and InfluxDB connections.

## Monitoring

New metrics have been added for historical queries:
- `sensorgate_sensor_data_received_total{sensor_type="history_query"}`
- `sensorgate_sensor_data_processed_total{sensor_type="history_query"}`
- `sensorgate_sensor_data_errors_total{sensor_type="history_query"}`

Similarly for other query types (aggregated_query, device_list, sensor_stats).
