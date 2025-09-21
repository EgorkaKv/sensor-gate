# SensorGate Documentation Index

Welcome to the SensorGate documentation! This index provides an overview of all available documentation and guides you to the right resource based on your needs.

## Quick Start

If you're new to SensorGate, start here:
1. Read the [README.md](../README.md) for project overview
2. Follow the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup
3. Check the [API Reference](API_REFERENCE.md) for endpoint details

## Documentation Structure

### 📖 Core Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [Technical Documentation](TECHNICAL_DOCUMENTATION.md) | Complete technical overview, architecture, and implementation details | Developers, DevOps, Architects |
| [API Reference](API_REFERENCE.md) | Detailed API endpoint documentation with examples | IoT developers, API consumers |
| [Architecture & Design](ARCHITECTURE.md) | System architecture, design patterns, and technical decisions | Senior developers, Architects |
| [Deployment Guide](DEPLOYMENT_GUIDE.md) | Step-by-step deployment instructions for various environments | DevOps, System administrators |

### 🚀 Getting Started

**For Developers:**
1. [Technical Documentation](TECHNICAL_DOCUMENTATION.md#development-guide) - Development setup
2. [Architecture & Design](ARCHITECTURE.md#design-principles) - Understanding the codebase
3. [API Reference](API_REFERENCE.md#example-usage) - Integration examples

**For DevOps:**
1. [Deployment Guide](DEPLOYMENT_GUIDE.md#kubernetes-deployment) - Production deployment
2. [Deployment Guide](DEPLOYMENT_GUIDE.md#troubleshooting) - Troubleshooting guide

**For IoT Developers:**
1. [API Reference](API_REFERENCE.md) - Complete API documentation
2. [API Reference](API_REFERENCE.md#example-usage) - Code examples
3. [Technical Documentation](TECHNICAL_DOCUMENTATION.md#api-endpoints) - Endpoint overview

## Key Features Covered

### 🏗️ Architecture & Design
- [System Architecture](ARCHITECTURE.md#system-architecture)
- [Component Interaction](ARCHITECTURE.md#component-interaction-flow)
- [Design Patterns](ARCHITECTURE.md#design-patterns)
- [Technology Choices](ARCHITECTURE.md#technology-choices--rationale)

### 🔧 Implementation Details
- [Project Structure](TECHNICAL_DOCUMENTATION.md#project-structure)
- [Core Components](TECHNICAL_DOCUMENTATION.md#core-components)
- [Configuration Management](TECHNICAL_DOCUMENTATION.md#configuration)
- [Error Handling](TECHNICAL_DOCUMENTATION.md#error-handling)

### 🚀 Deployment & Operations
- [Local Development](DEPLOYMENT_GUIDE.md#local-development)
- [Docker Deployment](DEPLOYMENT_GUIDE.md#docker-deployment)
- [Kubernetes Deployment](DEPLOYMENT_GUIDE.md#kubernetes-deployment)
- [Production Considerations](DEPLOYMENT_GUIDE.md#production-considerations)

### 🔐 Security
- [Authentication](TECHNICAL_DOCUMENTATION.md#authentication)
- [API Key Management](API_REFERENCE.md#authentication)
- [Security Architecture](ARCHITECTURE.md#security-architecture)

## Common Use Cases

### Setting Up Development Environment
```bash
# Follow these docs in order:
1. Technical Documentation → Development Guide
2. Deployment Guide → Local Development
3. API Reference → Example Usage
```

### Production Deployment
```bash
# Follow these docs in order:
1. Deployment Guide → Prerequisites
2. Deployment Guide → Kubernetes Deployment
3. Deployment Guide → Production Considerations
```

### API Integration
```bash
# Follow these docs in order:
1. API Reference → Authentication
2. API Reference → Sensor Data Endpoints
3. API Reference → Example Usage
4. Technical Documentation → Error Handling
```

### Troubleshooting Issues
```bash
# Check these resources:
1. Deployment Guide → Troubleshooting
2. Technical Documentation → Error Handling
3. API Reference → Error Responses
4. Technical Documentation → Health Check Endpoints
```

## Feature-Specific Guides

### Mock Pub/Sub Development
- [Mock Pub/Sub Guide](MOCK_PUBSUB_GUIDE.md) - Complete guide for local development with mock Pub/Sub

### Historical Data API
- [Historical Data API](HISTORICAL_DATA_API.md) - Working with InfluxDB and historical sensor data

### Public Access Configuration
- [Public Access Guide](PUBLIC_ACCESS_GUIDE.md) - Setting up development environments without authentication

## External Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

### Google Cloud
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

### InfluxDB
- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/)
- [InfluxDB Cloud](https://www.influxdata.com/products/influxdb-cloud/)

## Need Help?

If you can't find what you're looking for:
1. Check the [Technical Documentation](TECHNICAL_DOCUMENTATION.md) for comprehensive coverage
2. Review the [API Reference](API_REFERENCE.md) for specific endpoint details
3. Consult the [Architecture & Design](ARCHITECTURE.md) document for system understanding
4. Follow the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup issues

---

*This documentation is maintained alongside the SensorGate codebase. Please keep it updated when making changes to the system.*
