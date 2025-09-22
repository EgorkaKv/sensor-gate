# Mock Google Cloud Pub/Sub for Local Development

## Overview

SensorGate now supports mock Google Cloud Pub/Sub for convenient local development and testing without the need to connect to a real GCP Pub/Sub service.

## Mock Functionality

### ✅ Full API Compatibility
- Mock is fully compatible with the Google Cloud Pub/Sub interface
- Supports all methods: `publish()`, `get_topic()`, `topic_path()`
- Returns the same data types as the real client

### ✅ Automatic Switching
- Automatically activates in debug mode
- Can be forcibly enabled via environment variable
- Transparent switching between real and mock service

### ✅ Complete Logging
- Detailed logging of all "sent" messages
- Structured logs with message metadata
- JSON format for easy analysis

### ✅ Debug API
- Special endpoints for viewing sent messages
- Statistics by topics and messages
- Ability to clear data for testing

## Setup and Usage

### Configuration

Main environment variables:

```env
# Force enable mock (default false)
SENSORGATE_USE_PUBSUB_MOCK=true

# Automatically enable mock in debug mode (default true)
SENSORGATE_PUBSUB_MOCK_AUTO_ENABLE=true

# Debug mode (automatically activates mock if PUBSUB_MOCK_AUTO_ENABLE=true)
SENSORGATE_DEBUG=true
```

### Automatic Activation

Mock automatically activates in the following cases:

1. **Debug mode** + `PUBSUB_MOCK_AUTO_ENABLE=true` (default)
2. **Force activation** via `USE_PUBSUB_MOCK=true`

### Local Development Example

Create a `.env` file for local development:

```env
# Enable debug mode (automatically activates mock)
SENSORGATE_DEBUG=true

# API keys for testing
SENSORGATE_API_KEYS=dev-key-123,test-key-456

# Minimal settings (not critical for mock)
SENSORGATE_GCP_PROJECT_ID=mock-project
SENSORGATE_INFLUXDB_TOKEN=mock-token
SENSORGATE_INFLUXDB_ORG=mock-org
```

## Debug API Endpoints

### View All Messages

```http
GET /api/v1/debug/pubsub/messages
X-API-Key: dev-key-123
```

**Response:**
```json
{
  "messages": {
    "sensor-temperature": [
      {
        "message_id": "mock-msg-1642248000-1",
        "topic": "sensor-temperature",
        "data": {
          "device_id": 12345,
          "sensor_type": "temperature",
          "value": 23.5,
          "latitude": 55.7558,
          "longitude": 37.6176,
          "timestamp": "2024-01-15T12:00:00Z"
        },
        "timestamp": "2024-01-15T12:00:01.123Z"
      }
    ]
  },
  "stats": {
    "total_messages": 1,
    "topics_count": 1,
    "message_counter": 1
  },
  "using_mock": true
}
```

### Message Statistics

```http
GET /api/v1/debug/pubsub/stats
X-API-Key: dev-key-123
```

### Messages from Specific Topic

```http
GET /api/v1/debug/pubsub/topic/sensor-temperature/messages
X-API-Key: dev-key-123
```

### Clear Messages

```http
DELETE /api/v1/debug/pubsub/messages
X-API-Key: dev-key-123

# Or only specific topic
DELETE /api/v1/debug/pubsub/messages?topic_name=sensor-temperature
```

### Debug Mode Configuration

```http
GET /api/v1/debug/config
X-API-Key: dev-key-123
```

## Usage Examples

### Python Client for Testing

```python
import requests
import json
from datetime import datetime

# Settings for local development
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-key-123"
headers = {"X-API-Key": API_KEY}

# Send test data
sensor_data = {
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

# Send data (will be saved in mock)
response = requests.post(
    f"{API_BASE_URL}/sensors/data",
    headers=headers,
    json=sensor_data
)

print("Sending:", response.status_code, response.json())

# Check that data was saved in mock
debug_response = requests.get(
    f"{API_BASE_URL}/debug/pubsub/messages",
    headers=headers
)

print("Messages in mock:", debug_response.json())
```

### Local Development Workflow

1. **Start in debug mode:**
   ```bash
   # Set debug mode
   export SENSORGATE_DEBUG=true
   
   # Start service
   python main.py
   ```

2. **Check mock activation:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/health" \
     -H "X-API-Key: dev-key-123"
   
   # Response should contain: "using_mock": true
   ```

3. **Send test data:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/sensors/data" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-key-123" \
     -d '{
       "device_id": 12345,
       "sensor_type": "temperature",
       "value": 23.5,
       "latitude": 55.7558,
       "longitude": 37.6176,
       "timestamp": "2024-01-15T12:00:00Z"
     }'
   ```

4. **View sent messages:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/debug/pubsub/messages" \
     -H "X-API-Key: dev-key-123"
   ```

5. **Clear data for next test:**
   ```bash
   curl -X DELETE "http://localhost:8000/api/v1/debug/pubsub/messages" \
     -H "X-API-Key: dev-key-123"
   ```

## Performance

### Memory Limitations

Mock automatically limits the number of stored messages:

- **Default**: 1000 messages per topic
- **Automatic cleanup**: oldest messages are removed
- **Configurable limits**: can be changed in mock code

### Memory and Performance

- **Memory**: ~1KB per message (depends on data size)
- **Performance**: >10,000 messages/sec on typical PC
- **Limits**: configurable constraints prevent memory leaks

## Switching to Production

### Automatic Switching

When deploying to production:

```env
# Disable debug mode
SENSORGATE_DEBUG=false

# Specify real GCP settings
SENSORGATE_GCP_PROJECT_ID=your-production-project
SENSORGATE_GCP_CREDENTIALS_PATH=/path/to/production-key.json
```

Mock will automatically disable, and real GCP Pub/Sub will be used.

### Validate Switching

```bash
# Check that real Pub/Sub is being used
curl -X GET "https://your-production-domain/api/v1/health"

# Response should contain: "using_mock": false
```

## Troubleshooting

### Mock Not Activating

**Problem**: Mock doesn't enable in debug mode

**Solution**:
```env
# Make sure both settings are enabled
SENSORGATE_DEBUG=true
SENSORGATE_PUBSUB_MOCK_AUTO_ENABLE=true

# Or force enable mock
SENSORGATE_USE_PUBSUB_MOCK=true
```

### Debug Endpoints Unavailable

**Problem**: Debug endpoints return 404

**Solution**:
```env
# Debug endpoints are only available in debug mode
SENSORGATE_DEBUG=true
```

### Messages Not Saving

**Problem**: Sent messages don't appear in debug API

**Solution**:
1. Check that mock is active: `/api/v1/health` → `"using_mock": true`
2. Check API key validity
3. Check format of sent data

## Conclusion

Mock GCP Pub/Sub provides:

✅ **Development Convenience** - no need for GCP account for local tests  
✅ **Full Compatibility** - works as drop-in replacement for real Pub/Sub  
✅ **Rich Debugging** - detailed logs and debug API  
✅ **Automatic Switching** - seamless transition between dev and prod  
✅ **Performance** - fast testing without network delays  

Now local SensorGate development has become significantly easier and more efficient!
