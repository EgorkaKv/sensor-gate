# SensorGate Technical Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Authentication](#authentication)
7. [Error Handling](#error-handling)
8. [Deployment](#deployment)
9. [Development Guide](#development-guide)

## Architecture Overview

SensorGate is a FastAPI-based IoT gateway service designed to collect sensor data from IoT devices and forward it to Google Cloud Pub/Sub for further processing. The service follows a microservices architecture pattern with clear separation of concerns.

### High-Level Architecture

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐    Pub/Sub    ┌─────────────────┐
│   IoT Devices   │ ──────────────→ │   SensorGate     │ ─────────────→ │ Data Processors │
│   (Sensors)     │                 │   Service        │               │   (Consumers)   │
└─────────────────┘                 └──────────────────┘               └─────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.116.2+
- **Runtime**: Python 3.12+
- **ASGI Server**: Uvicorn
- **Messaging**: Google Cloud Pub/Sub
- **Validation**: Pydantic v2
- **Retry Logic**: Tenacity
- **Package Management**: Poetry

## Project Structure

```
SensorGate/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sensor.py          # Pydantic models
│   │   └── history.py         # Historical data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pubsub.py         # Google Cloud Pub/Sub client
│   │   ├── mock_pubsub.py    # Mock Pub/Sub for development
│   │   ├── auth.py           # Authentication service
│   │   └── influxdb.py       # InfluxDB client for historical data
│   └── api/
│       ├── __init__.py
│       ├── deps.py           # FastAPI dependencies
│       ├── health.py         # Health check endpoints
│       ├── sensors.py        # Sensor data endpoints
│       ├── history.py        # Historical data endpoints
│       └── debug.py          # Debug endpoints (mock Pub/Sub)
├── docs/                     # Documentation
├── tests/                    # Test files
├── main.py                   # Application entry point
├── pyproject.toml           # Project configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # Project overview
```

## Core Components

### 1. Configuration Management (`app/config.py`)

The configuration system uses Pydantic Settings to manage environment variables with validation and type safety.

**Key Features:**
- Environment variable validation
- Type conversion
- Default values
- Configurable prefixes (`SENSORGATE_`)

**Critical Settings:**
- `gcp_project_id`: Google Cloud project ID
- `api_keys`: Comma-separated list of valid API keys
- `pubsub_topic_*`: Topic names for different sensor types
- `circuit_breaker_*`: Circuit breaker configuration

### 2. Data Models (`app/models/sensor.py`)

Pydantic models provide data validation and serialization.

**SensorData Model:**
```python
{
    "device_id": int,          # Unique device identifier (>0)
    "sensor_type": str,        # "temperature", "humidity", "ndir"
    "value": float,            # Sensor reading value
    "latitude": float,         # GPS latitude (-90 to 90)
    "longitude": float,        # GPS longitude (-180 to 180)
    "timestamp": datetime      # ISO format, not in future
}
```

**Validation Rules:**
- Temperature: -273.15°C to 1000°C
- Humidity: 0% to 100%
- NDIR CO2: 0 to 50000 ppm

### 3. Pub/Sub Service (`app/services/pubsub.py`)

Manages Google Cloud Pub/Sub communication with reliability patterns.

**Key Features:**
- Circuit breaker pattern for fault tolerance
- Exponential backoff retry logic
- Topic routing based on sensor type
- Health monitoring
- **Mock Pub/Sub for local development**

**Mock Pub/Sub Support:**
- Automatic activation in debug mode
- Full API compatibility with Google Cloud Pub/Sub
- Debug endpoints for message inspection
- Memory-efficient message storage with limits

**Circuit Breaker States:**
- `CLOSED`: Normal operation
- `OPEN`: Service unavailable, requests fail fast
- `HALF_OPEN`: Testing service recovery

**Mock vs Real Pub/Sub:**
The service automatically switches between real and mock Pub/Sub based on configuration:
- Mock: Used in debug mode or when explicitly enabled
- Real: Used in production with actual GCP credentials

### 4. Authentication Service (`app/services/auth.py`)

Provides API key-based authentication with public access support.

**Authentication Methods:**
- Header-based: `X-API-Key: your-api-key`
- Bearer token: `Authorization: Bearer your-api-key`
- Public access: When enabled, no authentication required

**Security Features:**
- Configurable API keys
- Public access mode for development/testing
- Configurable authentication enforcement

### 5. Historical Data Service (`app/services/influxdb.py`)

Manages InfluxDB connections for retrieving historical sensor data.

**Key Features:**
- InfluxDB 2.x integration
- Query optimization for time-series data
- Aggregation support
- Filtering by device, sensor type, and time range

## API Endpoints

### Sensor Data Endpoints

#### POST `/api/v1/sensors/data`
Submit sensor data from IoT devices.

**Headers:**
- `X-API-Key: <api-key>` (required unless public access enabled)
- `Content-Type: application/json`

**Request Body:**
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

**Response (201):**
```json
{
    "message": "Data received successfully",
    "device_id": 12345,
    "sensor_type": "temperature",
    "processed_at": "2024-01-15T12:30:01Z"
}
```

#### GET `/api/v1/sensors/types`
Get supported sensor types and validation rules.

### Historical Data Endpoints

#### GET `/api/v1/history/devices`
Get list of all device IDs that have historical data.

#### GET `/api/v1/history/device/{device_id}`
Get historical data for a specific device.

#### GET `/api/v1/history/sensor-type/{sensor_type}`
Get historical data for all devices of a specific sensor type.

### Health Check Endpoints

#### GET `/api/v1/health`
Comprehensive health check including dependencies.

#### GET `/api/v1/health/live`
Kubernetes liveness probe (basic service status).

#### GET `/api/v1/health/ready`
Kubernetes readiness probe (includes dependency checks).

### Debug Endpoints (Mock Pub/Sub)

#### GET `/api/v1/debug/mock-pubsub/messages`
Get messages from mock Pub/Sub (debug mode only).

#### DELETE `/api/v1/debug/mock-pubsub/messages`
Clear all messages from mock Pub/Sub (debug mode only).

## Configuration

### Environment Variables

All configuration is done through environment variables with the `SENSORGATE_` prefix:

#### Required Variables:
```bash
SENSORGATE_GCP_PROJECT_ID=your-gcp-project-id
# API keys only required if public access is disabled
SENSORGATE_API_KEYS=key1,key2,key3
```

#### Optional Variables:
```bash
# Application
SENSORGATE_DEBUG=false
SENSORGATE_HOST=0.0.0.0
SENSORGATE_PORT=8000
SENSORGATE_PUBLIC_ACCESS=false

# Pub/Sub Topics
SENSORGATE_PUBSUB_TOPIC_TEMPERATURE=sensor-temperature
SENSORGATE_PUBSUB_TOPIC_HUMIDITY=sensor-humidity
SENSORGATE_PUBSUB_TOPIC_NDIR=sensor-ndir

# Circuit Breaker
SENSORGATE_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
SENSORGATE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# InfluxDB Configuration
SENSORGATE_INFLUXDB_URL=https://your-influxdb-instance.com
SENSORGATE_INFLUXDB_TOKEN=your-influxdb-token
SENSORGATE_INFLUXDB_ORG=your-organization
SENSORGATE_INFLUXDB_BUCKET=iot-sensors
```

### Google Cloud Authentication

Two methods for GCP authentication:

1. **Service Account Key File:**
   ```bash
   SENSORGATE_GCP_CREDENTIALS_PATH=/path/to/service-account.json
   ```

2. **Default Application Credentials:**
   ```bash
   gcloud auth application-default login
   ```

## Authentication

### API Key Management

API keys are configured via environment variable:
```bash
SENSORGATE_API_KEYS=prod-key-123,dev-key-456,test-key-789
```

### Public Access Mode

For development and testing, public access can be enabled:
```bash
SENSORGATE_PUBLIC_ACCESS=true
```

When enabled, all endpoints can be accessed without authentication.

### Security Considerations

- API keys should be cryptographically random (32+ chars)
- Use different keys for different environments
- Rotate keys regularly
- Use HTTPS in production
- Enable public access only in safe environments

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful GET requests
- `201 Created`: Successful POST requests
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid API key
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server-side errors
- `503 Service Unavailable`: Pub/Sub circuit breaker open

### Error Response Format

```json
{
    "detail": "Error description",
    "error_code": "VALIDATION_ERROR",
    "timestamp": "2024-01-15T12:30:00Z"
}
```

## Deployment

### Docker Deployment

```bash
docker build -t sensorgate .
docker run -p 8000:8000 --env-file .env sensorgate
```

### Google Cloud Run

```bash
gcloud run deploy sensorgate \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment Setup

1. Copy `.env.example` to `.env`
2. Configure required environment variables
3. Set up Google Cloud Pub/Sub topics
4. Configure InfluxDB connection
5. Deploy and test endpoints

## Development Guide

### Local Development Setup

1. **Install Poetry**: `pip install poetry`
2. **Install dependencies**: `poetry install`
3. **Activate environment**: `poetry shell`
4. **Copy environment file**: `cp .env.example .env`
5. **Configure variables**: Edit `.env` file
6. **Run application**: `uvicorn app.main:app --reload`

### Mock Pub/Sub Development

For local development without GCP:
```bash
SENSORGATE_DEBUG=true
SENSORGATE_PUBLIC_ACCESS=true
```

This enables:
- Mock Pub/Sub service
- Public access (no API keys required)
- Debug endpoints for message inspection

### Testing

Run tests with:
```bash
poetry run pytest
```

### Code Quality

- **Linting**: `poetry run ruff check`
- **Formatting**: `poetry run ruff format`
- **Type checking**: `poetry run mypy app/`
