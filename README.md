# SensorGate

## Overview

SensorGate is a FastAPI-based IoT gateway service designed to collect, validate, and process data from IoT sensors. This service acts as a central data ingestion point that receives sensor data via REST API endpoints and publishes it to Google Cloud Pub/Sub for further processing by specialized data handlers.

## Architecture

```
IoT Sensors → SensorGate (REST API) → Google Cloud Pub/Sub → Data Processors
                    ↓
            Historical Data (InfluxDB)
```

The service follows a decoupled architecture where:
- **IoT Devices/Sensors** send their data to SensorGate via HTTP REST API
- **SensorGate** validates, processes, and forwards the data to Google Cloud Pub/Sub topics
- **Data Processors** subscribe to relevant topics and handle the sensor data accordingly
- **Historical Data** can be queried from InfluxDB for analytics and reporting

## Technology Stack

- **Framework**: FastAPI 0.116.2+
- **Language**: Python 3.12+
- **ASGI Server**: Uvicorn
- **Messaging**: Google Cloud Pub/Sub
- **Database**: InfluxDB (for historical data)
- **Validation**: Pydantic v2
- **Package Management**: Poetry
- **Deployment**: Docker, Google Cloud Run
- **Documentation**: OpenAPI/Swagger (auto-generated)

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Google Cloud Project with Pub/Sub API enabled
- InfluxDB instance (optional, for historical data)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/EgorkaKv/sensor-gate
cd SensorGate
```

2. **Install dependencies using Poetry:**
```bash
poetry install
poetry shell
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Configure Google Cloud authentication:**
```bash
# Option 1: Service account key
export SENSORGATE_GCP_CREDENTIALS_PATH=/path/to/service-account.json

# Option 2: Application default credentials
gcloud auth application-default login
```

5. **Run the development server:**
```bash
python main.py
# Or using uvicorn directly:
# uvicorn app.main:app --reload
```

The service will be available at `http://localhost:8000`

### Docker Quick Start

```bash
# Build the image
docker build -t sensorgate .

# Run with environment variables
docker run -p 8000:8000 \
  -e SENSORGATE_GCP_PROJECT_ID=your-project \
  -e SENSORGATE_PUBLIC_ACCESS=true \
  sensorgate
```

## API Documentation

### Interactive Documentation
Once the service is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Key Endpoints

#### Sensor Data Ingestion
```http
POST /api/v1/sensors/data
Content-Type: application/json
X-API-Key: your-api-key

{
  "device_id": 12345,
  "sensor_type": "temperature",
  "value": 23.5,
  "latitude": 55.7558,
  "longitude": 37.6176,
  "timestamp": "2024-01-15T12:30:00Z"
}
```

#### Health Checks
- `GET /health` - Comprehensive health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

#### Historical Data
- `GET /api/v1/history/devices` - List all devices
- `GET /api/v1/history/device/{device_id}` - Data for specific device
- `GET /api/v1/history/sensor-type/{sensor_type}` - Data by sensor type

#### Debug (Development Mode)
- `GET /api/v1/debug/mock-pubsub/messages` - View mock Pub/Sub messages
- `DELETE /api/v1/debug/mock-pubsub/messages` - Clear mock messages

## Configuration

### Environment Variables

All configuration is done through environment variables with the `SENSORGATE_` prefix:

```bash
# Required
SENSORGATE_GCP_PROJECT_ID=your-gcp-project-id

# Authentication (optional if public access enabled)
SENSORGATE_API_KEYS=key1,key2,key3
SENSORGATE_PUBLIC_ACCESS=false

# Application settings
SENSORGATE_DEBUG=false
SENSORGATE_HOST=0.0.0.0
SENSORGATE_PORT=8000

# Pub/Sub topics
SENSORGATE_PUBSUB_TOPIC_TEMPERATURE=sensor-temperature
SENSORGATE_PUBSUB_TOPIC_HUMIDITY=sensor-humidity
SENSORGATE_PUBSUB_TOPIC_NDIR=sensor-ndir

# InfluxDB (for historical data)
SENSORGATE_INFLUXDB_URL=https://your-influxdb-instance.com
SENSORGATE_INFLUXDB_TOKEN=your-token
SENSORGATE_INFLUXDB_ORG=your-org
SENSORGATE_INFLUXDB_BUCKET=iot-sensors

# Circuit breaker settings
SENSORGATE_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
SENSORGATE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

## Docker Deployment

```bash
docker build -t sensorgate .
docker run -p 8000:8000 --env-file .env sensorgate
```

## Supported Sensor Types

| Type          | Description          | Value Range     | Unit       |
|---------------|----------------------|-----------------|------------|
| `temperature` | Temperature readings | -273.15 to 1000 | °C         |
| `humidity`    | Humidity percentage  | 0 to 100        | %          |
| `ndir`        | NDIR CO2 sensor      | 0 to 50000      | ppm        |

## Development

### Local Development with Mock Services

For development without Google Cloud dependencies:

```bash
# Set environment variables for mock mode
export SENSORGATE_DEBUG=true
export SENSORGATE_PUBLIC_ACCESS=true
export SENSORGATE_GCP_PROJECT_ID=test-project

# Run the service
python main.py
```

This enables:
- Mock Pub/Sub service (no GCP credentials needed)
- Public access (no API keys required)
- Debug endpoints for message inspection

## Documentation

### Complete Documentation
- 📖 [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md) - Architecture and implementation details
- 🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment instructions
- ☁️ [Cloud Run Deployment](docs/CLOUD_RUN_DEPLOYMENT.md) - Google Cloud Run specific guide
- 🔧 [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md) - System design and patterns

### Feature-Specific Guides
- 🧪 [Mock Pub/Sub Guide](docs/MOCK_PUBSUB_GUIDE.md) - Local development setup
- 📊 [Historical Data API](docs/HISTORICAL_DATA_API.md) - InfluxDB integration
- 🔓 [Public Access Guide](docs/PUBLIC_ACCESS_GUIDE.md) - Development configuration

## Example Usage

### Python Client

```python
import requests
from datetime import datetime

# Send sensor data
response = requests.post(
    "http://localhost:8000/api/v1/sensors/data",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    },
    json={
        "device_id": 12345,
        "sensor_type": "temperature",
        "value": 23.5,
        "latitude": 55.7558,
        "longitude": 37.6176,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
)
print(response.json())
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/sensors/data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "2024-01-15T12:30:00Z"
  }'
```

### Common Issues

1. **Pub/Sub Connection Errors**
   - Verify GCP credentials and project ID
   - Ensure Pub/Sub API is enabled
   - Check topic names and permissions

2. **Authentication Failures**
   - Verify API key format and headers
   - Check if public access is enabled for testing
   - Review authentication configuration

3. **InfluxDB Connection Issues**
   - Verify InfluxDB credentials and URL
   - Check bucket and organization names
   - Ensure InfluxDB is accessible from your deployment

For detailed troubleshooting, see the [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md).

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Google Cloud Pub/Sub](https://cloud.google.com/pubsub)
- Time-series data with [InfluxDB](https://www.influxdata.com/)
- Deployment on [Google Cloud Run](https://cloud.google.com/run)

---

**SensorGate** - *Connecting IoT devices to the cloud, one sensor at a time* 🌐📡
