# SensorGate

## Overview

SensorGate is a FastAPI-based IoT gateway service designed to collect and process data from IoT sensors. This service acts as a central data ingestion point that receives sensor data via REST API endpoints and publishes it to a Pub/Sub messaging system for further processing by specialized data handlers.

## Architecture

```
IoT Sensors → SensorGate (REST API) → Pub/Sub → Data Processors
```

The service follows a decoupled architecture where:
- **IoT Devices/Sensors** send their data to SensorGate via HTTP REST API
- **SensorGate** validates, processes, and forwards the data to a Pub/Sub system
- **Data Processors** subscribe to relevant topics and handle the sensor data accordingly

## Features

- 🌐 RESTful API endpoints for sensor data ingestion
- 📊 Real-time data processing and validation
- 🔄 Pub/Sub integration for scalable data distribution
- ⚡ High-performance FastAPI framework
- 🐍 Python 3.12+ support
- 📝 Comprehensive API documentation (auto-generated)

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **ASGI Server**: Uvicorn
- **Package Management**: Poetry
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd SensorGate
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

4. Run the development server:
```bash
uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`

### API Documentation

Once the service is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## Development Status

🚧 **This project is currently in active development**

The following features are planned or under development:
- Sensor data validation schemas
- Pub/Sub integration
- Authentication and authorization
- Rate limiting and throttling
- Monitoring and logging
- Database integration for data persistence
- Comprehensive test suite

## Contributing

This project is part of a larger IoT ecosystem. More detailed contribution guidelines will be added as the project matures.

## License

[License information to be added]

## Contact

**Author**: EgorkaKv  
**Email**: yehor.kvasenko@gmail.com

---

*This README will be updated as the project evolves and new features are implemented.*
