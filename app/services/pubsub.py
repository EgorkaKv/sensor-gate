import json
import time
from typing import Dict, Any, Optional
from enum import Enum

from app.config import settings

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from google.api_core import exceptions as gcp_exceptions



# Conditional imports based on mock setting
if settings.use_pubsub_mock or (settings.pubsub_mock_auto_enable and settings.debug):
    # Use mock Pub/Sub
    from app.services.mock_pubsub import mock_pubsub_service as _pubsub_service_impl
    USING_MOCK = True
else:
    # Use real Pub/Sub (original implementation)
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1 import PublisherClient
    USING_MOCK = False


class CircuitBreakerState(Enum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitBreaker:
    """Circuit breaker implementation for Pub/Sub operations"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

# class PubSubService(LoggerMixin):
class PubSubService:
    """Google Cloud Pub/Sub service with circuit breaker and retry logic"""

    def __init__(self):
        self.project_id = settings.gcp_project_id
        self.topic_mapping = settings.sensor_topic_mapping
        self.client: Optional[PublisherClient] = None
        self.using_mock = USING_MOCK

        # Initialize circuit breaker (skip for mock)
        if not self.using_mock:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=settings.circuit_breaker_failure_threshold,
                recovery_timeout=settings.circuit_breaker_recovery_timeout
            )

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Pub/Sub client (real or mock)"""
        try:
            if self.using_mock:
                # Use mock service directly
                self._mock_service = _pubsub_service_impl
                print('Mock Pub/Sub client initialized successfully')
            else:
                # Initialize real Google Cloud Pub/Sub client
                import os

                # Set credentials path only if file exists (for local development)
                if (settings.gcp_credentials_path and
                    os.path.exists(settings.gcp_credentials_path)):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.gcp_credentials_path
                    print(f'Using service account file: {settings.gcp_credentials_path}')
                else:
                    # Use Application Default Credentials (Cloud Run, gcloud auth, etc.)
                    print('Using Application Default Credentials')

                self.client = pubsub_v1.PublisherClient()
                print('Real Pub/Sub client initialized successfully')

        except Exception as e:
            print(f'Error initializing Pub/Sub client: {e}')
            raise

    def get_topic_path(self, sensor_type: str) -> str:
        """Get full topic path for sensor type"""
        topic_name = self.topic_mapping.get(sensor_type)
        if not topic_name:
            raise ValueError(f"No topic mapping found for sensor type: {sensor_type}")

        if self.using_mock:
            return self._mock_service.get_topic_path(sensor_type)
        else:
            return self.client.topic_path(self.project_id, topic_name)

    def publish_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> str:
        """Publish sensor data to appropriate Pub/Sub topic"""
        if self.using_mock:
            # Use mock service
            return self._mock_service.publish_sensor_data(sensor_type, data)

        # Use real Pub/Sub service
        topic_path = self.get_topic_path(sensor_type)

        # Transform data to match Avro schema in cloud
        transformed_data = self._transform_data_for_avro_schema(data)
        message_data = json.dumps(transformed_data, default=str).encode('utf-8')

        try:
            message_id = self.circuit_breaker.call(
                self._publish_message,
                topic_path,
                message_data
            )

            return message_id

        except Exception as e:
            print('Error publishing message to Pub/Sub:', e)
            raise

    def _transform_data_for_avro_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform SensorGate data format to match cloud Avro schema"""
        # New schema expects string timestamp, not microseconds
        timestamp_value = data.get('timestamp')
        if isinstance(timestamp_value, str):
            # Keep as ISO string format as expected by schema
            timestamp_str = timestamp_value
        else:
            # Convert to ISO string if it's not already
            from datetime import datetime
            timestamp_str = datetime.utcnow().isoformat() + "Z"

        return {
            "device_id": int(data.get('device_id', 0)),
            "sensor_type": data.get('sensor_type', ''),
            "value": float(data.get('value', 0.0)),
            "latitude": float(data.get('latitude', 0.0)),
            "longitude": float(data.get('longitude', 0.0)),
            "timestamp": timestamp_str
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            gcp_exceptions.ServiceUnavailable,
            gcp_exceptions.DeadlineExceeded,
            gcp_exceptions.InternalServerError
        ))
    )
    def _publish_message(self, topic_path: str, message_data: bytes) -> str:
        """Internal method to publish message with retry logic (real Pub/Sub only)"""
        if self.using_mock:
            # This method shouldn't be called for mock, but handle gracefully
            return "mock-message-id"

        start_time = time.time()

        try:
            future = self.client.publish(topic_path, message_data)
            message_id = future.result(timeout=settings.pubsub_timeout)

            duration = time.time() - start_time
            topic_name = topic_path.split('/')[-1]


            return message_id
        except Exception as e:
            topic_name = topic_path.split('/')[-1]
            error_type = type(e).__name__
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check Pub/Sub service health"""
        if self.using_mock:
            # Use mock health check
            health_result = self._mock_service.health_check()
            health_result["using_mock"] = True
            return health_result

        # Real Pub/Sub health check
        try:
            # Try to get topic info as a health check
            sample_topic = list(self.topic_mapping.values())[0]
            topic_path = self.client.topic_path(self.project_id, sample_topic)

            # This will raise an exception if the topic doesn't exist or there are connection issues
            self.client.get_topic(request={"topic": topic_path})

            return {
                "status": "healthy",
                "using_mock": False,
                "circuit_breaker_state": self.circuit_breaker.state.name,
                "project_id": self.project_id,
                "available_topics": list(self.topic_mapping.values())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "using_mock": False,
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state.name
            }

    def get_mock_data(self) -> Optional[Dict[str, Any]]:
        """Get mock-specific data for debugging (only available in mock mode)"""
        if self.using_mock:
            return self._mock_service.get_mock_data()
        return None

    def clear_mock_data(self, topic_name: Optional[str] = None) -> bool:
        """Clear mock data (only available in mock mode)"""
        if self.using_mock:
            self._mock_service.clear_mock_data(topic_name)
            return True
        return False


# Global PubSub service instance
pubsub_service = PubSubService()
