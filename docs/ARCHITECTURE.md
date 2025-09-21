# Architecture & Design Document

## Overview

This document describes the architectural decisions, design patterns, and technical choices made in the SensorGate project. It serves as a reference for future development and helps understand the rationale behind the current implementation.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               SensorGate Service                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   FastAPI   │  │    Auth     │  │   Health    │  │    Configuration    │ │
│  │  Endpoints  │  │  Service    │  │   Checks    │  │    Management       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Data      │  │  Business   │  │   Pub/Sub   │  │    InfluxDB         │ │
│  │ Validation  │  │   Logic     │  │  Service    │  │    Service          │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Error     │  │   Circuit   │  │    Retry    │  │   Mock Pub/Sub      │ │
│  │  Handling   │  │  Breaker    │  │ Mechanism   │  │   (Development)     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
┌─────────────┐    HTTP Request    ┌─────────────────┐
│ IoT Device  │ ─────────────────→ │ FastAPI Router  │
└─────────────┘                    └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Auth Middleware │
                                   └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Data Validation │
                                   └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Pub/Sub Service │
                                   └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Google Cloud    │
                                   │ Pub/Sub         │
                                   └─────────────────┘
```

## Design Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:
- **API Layer**: HTTP request/response handling
- **Service Layer**: Business logic and external integrations
- **Data Layer**: Validation and serialization
- **Infrastructure Layer**: Configuration and health monitoring

### 2. Dependency Injection

FastAPI's dependency injection system is used throughout:
```python
# Dependencies are injected rather than imported directly
async def submit_sensor_data(
    sensor_data: SensorData,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
    api_key: str = Depends(get_authenticated_request)
) -> SensorDataResponse:
```

### 3. Configuration as Code

All configuration is externalized and validated:
```python
class Settings(BaseSettings):
    # Type-safe configuration with validation
    gcp_project_id: str
    api_keys: List[str] = []
    
    class Config:
        env_prefix = "SENSORGATE_"
```

### 4. Fail Fast Principle

Errors are detected and handled as early as possible in the request pipeline:
```python
# Validation happens before business logic
@app.post("/api/v1/sensors/data")
async def submit_data(sensor_data: SensorData):  # Pydantic validates here
    # Business logic only runs with valid data
    await pubsub_service.publish(sensor_data)
```

### 5. Resilience Patterns

The system implements several resilience patterns:
- **Circuit Breaker**: Prevents cascading failures
- **Retry Logic**: Handles transient errors
- **Graceful Degradation**: Mock services for development

## Design Patterns

### 1. Repository Pattern

Services encapsulate external system interactions:
```python
class PubSubService:
    async def publish(self, topic: str, message: dict) -> bool:
        # Encapsulates Pub/Sub complexity
        pass

class InfluxDBService:
    async def query_historical_data(self, filters: dict) -> List[dict]:
        # Encapsulates InfluxDB complexity
        pass
```

### 2. Factory Pattern

Service instances are created through factories:
```python
def get_pubsub_service(settings: Settings) -> PubSubService:
    if settings.debug:
        return MockPubSubService()
    return RealPubSubService(settings.gcp_project_id)
```

### 3. Strategy Pattern

Different authentication strategies based on configuration:
```python
class AuthService:
    def get_strategy(self, settings: Settings) -> AuthStrategy:
        if settings.public_access:
            return PublicAccessStrategy()
        return APIKeyStrategy(settings.api_keys)
```

### 4. Observer Pattern

Components emit events without knowing consumers:
```python
# Components emit events without knowing who consumes them
await pubsub_service.publish(topic, sensor_data)
# Multiple consumers can process the same event
```

## Technology Choices & Rationale

### 1. FastAPI vs Flask/Django

**Choice**: FastAPI

**Rationale**:
- Native async/await support for high concurrency
- Automatic API documentation generation
- Built-in request/response validation with Pydantic
- Type hints throughout for better development experience
- Performance comparable to Node.js and Go

### 2. Pydantic v2 vs v1

**Choice**: Pydantic v2

**Rationale**:
- Significant performance improvements
- Better error messages and validation
- Enhanced datetime handling
- Performance improvements in v2

### 3. Google Cloud Pub/Sub vs Other Message Queues

**Choice**: Google Cloud Pub/Sub

**Rationale**:
- Managed service (no infrastructure management)
- Auto-scaling and high availability
- Strong ordering guarantees
- Integration with other GCP services
- At-least-once delivery semantics

### 4. InfluxDB vs Other Time-Series Databases

**Choice**: InfluxDB

**Rationale**:
- Purpose-built for time-series data
- Excellent compression for IoT data
- Rich query language (Flux)
- Cloud-native with InfluxDB Cloud
- Good performance for historical queries

## Data Flow Architecture

### 1. Sensor Data Ingestion Flow

```
IoT Device → FastAPI → Validation → Pub/Sub → Data Processors
     │            │           │          │            │
     │            │           │          │            └─ Analytics
     │            │           │          │            └─ Storage (InfluxDB)
     │            │           │          │            └─ Alerts
     │            │           │          └─ Topic routing by sensor type
     │            │           └─ Pydantic validation with business rules
     │            └─ Authentication and rate limiting
     └─ JSON payload with sensor reading
```

### 2. Historical Data Query Flow

```
Client Request → Authentication → InfluxDB Query → Response
      │               │               │              │
      │               │               │              └─ JSON formatted data
      │               │               └─ Time-series aggregation
      │               └─ API key validation
      └─ HTTP GET with query parameters
```

## Performance Considerations

### 1. Async I/O Design

All I/O operations are async to maximize throughput:
```python
# Non-blocking I/O operations
async def process_sensor_data(data: SensorData):
    # Concurrent operations where possible
    tasks = [
        pubsub_service.publish(topic, data),
        audit_service.log_request(data)
    ]
    await asyncio.gather(*tasks)
```

### 2. Connection Pooling

Services use connection pooling for external systems:
- HTTP clients with connection pooling
- Database connections managed by async pools

### 3. Resource Management

- Memory-conscious operations
- Proper resource cleanup
- Bounded queues and timeouts

### 4. Caching Strategy

- Configuration cached at startup
- Health check results cached briefly
- No data caching (real-time requirements)

## Security Architecture

### 1. Authentication Layers

```
Public Internet → API Gateway → Authentication → Application
       │              │              │              │
       │              │              │              └─ Business logic
       │              │              └─ API key validation
       │              └─ HTTPS termination
       └─ TLS encryption in transit
```

### 2. Data Protection

- API keys stored as environment variables
- No sensitive data in logs
- Input validation prevents injection attacks
- HTTPS for all communications

### 3. Access Control

- API key-based authentication
- Public access mode for development
- No user-based permissions (device-level only)

## Observability Strategy

The system focuses on operational visibility through:

### 1. Health Monitoring

- Comprehensive health checks
- Dependency status monitoring
- Circuit breaker state tracking

### 2. Error Handling

- Structured error responses
- Proper HTTP status codes
- Error categorization and handling

### 3. Development Tools

- Mock services for local development
- Debug endpoints for troubleshooting
- Comprehensive API documentation

## Scalability Considerations

### 1. Horizontal Scaling

The service is designed to scale horizontally:
- Stateless application design
- No shared state between instances
- External state in managed services (Pub/Sub, InfluxDB)

### 2. Performance Optimization

- Async I/O for high concurrency
- Efficient serialization with Pydantic
- Connection pooling for external services

### 3. Resource Limits

- Circuit breakers prevent resource exhaustion
- Configurable timeouts and retry policies

## Future Architecture Considerations

### 1. Microservices Evolution

Current monolithic design can evolve to microservices:
- Historical data service can be separated
- Authentication service can be externalized
- Each sensor type could have dedicated services

### 2. Event-Driven Architecture

Enhanced event-driven patterns:
- Event sourcing for audit trails
- CQRS for read/write optimization
- Saga pattern for complex workflows

### 3. Advanced Resilience

- Multi-region deployment
- Advanced circuit breaker patterns
- Chaos engineering integration

---

This architecture supports the current requirements while maintaining flexibility for future enhancements and scaling needs.
