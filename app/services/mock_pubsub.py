import json
import time
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from collections import defaultdict

from app.config import settings
# from app.core.logging import LoggerMixin


class MockPubSubMessage:
    """Mock Pub/Sub message for testing"""

    def __init__(self, message_id: str, topic: str, data: bytes, timestamp: datetime):
        self.message_id = message_id
        self.topic = topic
        self.data = data
        self.timestamp = timestamp
        self.attributes = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        try:
            data_str = self.data.decode('utf-8')
            data_json = json.loads(data_str)
        except (UnicodeDecodeError, json.JSONDecodeError):
            data_json = {"raw_data": self.data.hex()}

        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "data": data_json,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes
        }

# class MockPublisherClient(LoggerMixin):
def topic_path(project_id: str, topic_name: str) -> str:
    """Generate topic path (same as real client)"""
    return f"projects/{project_id}/topics/{topic_name}"


class MockPublisherClient:
    """Mock Google Cloud Pub/Sub Publisher Client for local development"""

    def __init__(self):
        self.project_id = settings.gcp_project_id or "mock-project"
        self.published_messages: Dict[str, List[MockPubSubMessage]] = defaultdict(list)
        self.message_counter = 0
        self.max_messages_per_topic = 1000  # Prevent memory overflow

        print("Mock Pub/Sub Publisher Client initialized", self.project_id, 'max_messages_per_topic:', self.max_messages_per_topic)

    def publish(self, topic_path: str, data: bytes, **kwargs) -> 'MockFuture':
        """Mock publish method"""
        # Extract topic name from path
        topic_name = topic_path.split('/')[-1]

        # Generate unique message ID
        self.message_counter += 1
        message_id = f"mock-msg-{int(time.time())}-{self.message_counter}"

        # Create mock message
        message = MockPubSubMessage(
            message_id=message_id,
            topic=topic_name,
            data=data,
            timestamp=datetime.now(UTC)
        )

        # Store message (with size limit per topic)
        if len(self.published_messages[topic_name]) >= self.max_messages_per_topic:
            # Remove oldest message
            self.published_messages[topic_name].pop(0)

        self.published_messages[topic_name].append(message)

        # Log the published message
        try:
            data_dict = json.loads(data.decode('utf-8'))
            # self.logger.info(
            #     "Mock Pub/Sub message published",
            #     message_id=message_id,
            #     topic=topic_name,
            #     device_id=data_dict.get('device_id'),
            #     sensor_type=data_dict.get('sensor_type'),
            #     value=data_dict.get('value')
            # )
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
            # self.logger.info(
            #     "Mock Pub/Sub message published (binary data)",
            #     message_id=message_id,
            #     topic=topic_name,
            #     data_size=len(data)
            # )

        # Return mock future
        return MockFuture(message_id)

    def get_topic(self, request: Dict[str, str]) -> 'MockTopic':
        """Mock get_topic method for health checks"""
        topic_path = request.get("topic", "")
        topic_name = topic_path.split('/')[-1] if topic_path else "unknown"

        return MockTopic(topic_path, topic_name)

    def get_published_messages(self, topic_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all published messages for debugging"""
        if topic_name:
            messages = self.published_messages.get(topic_name, [])
            return {topic_name: [msg.to_dict() for msg in messages]}

        result = {}
        for topic, messages in self.published_messages.items():
            result[topic] = [msg.to_dict() for msg in messages]

        return result

    def get_message_count(self, topic_name: Optional[str] = None) -> Dict[str, int]:
        """Get message count per topic"""
        if topic_name:
            return {topic_name: len(self.published_messages.get(topic_name, []))}

        return {topic: len(messages) for topic, messages in self.published_messages.items()}

    def clear_messages(self, topic_name: Optional[str] = None) -> None:
        """Clear stored messages for testing"""
        if topic_name:
            self.published_messages[topic_name].clear()
            print('Cleared mock messages for topic:', topic_name)
        else:
            self.published_messages.clear()
            print('Cleared all mock messages')

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about mock Pub/Sub usage"""
        total_messages = sum(len(messages) for messages in self.published_messages.values())

        return {
            "total_messages": total_messages,
            "topics_count": len(self.published_messages),
            "topics": list(self.published_messages.keys()),
            "messages_per_topic": self.get_message_count(),
            "message_counter": self.message_counter,
            "max_messages_per_topic": self.max_messages_per_topic
        }


class MockFuture:
    """Mock future object returned by publish"""

    def __init__(self, message_id: str):
        self.message_id = message_id

    def result(self, timeout: Optional[float] = None) -> str:
        """Return message ID immediately (mock successful publish)"""
        return self.message_id


class MockTopic:
    """Mock topic object for health checks"""

    def __init__(self, topic_path: str, name: str):
        self.name = topic_path
        self.display_name = name

# class MockPubSubService(LoggerMixin):
class MockPubSubService:
    """Mock version of PubSubService for local development"""

    def __init__(self):
        self.project_id = settings.gcp_project_id or "mock-project"
        self.topic_mapping = settings.sensor_topic_mapping
        self.client = MockPublisherClient()

        # Mock circuit breaker (always closed)
        self.circuit_breaker = MockCircuitBreaker()

        print('Mock Pub/Sub Service initialized', self.project_id, self.topic_mapping)

    def get_topic_path(self, sensor_type: str) -> str:
        """Get full topic path for sensor type"""
        topic_name = self.topic_mapping.get(sensor_type)
        if not topic_name:
            raise ValueError(f"No topic mapping found for sensor type: {sensor_type}")

        return topic_path(self.project_id, topic_name)

    def publish_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> str:
        """Publish sensor data to mock Pub/Sub"""
        topic_path = self.get_topic_path(sensor_type)
        message_data = json.dumps(data, default=str).encode('utf-8')

        # Use circuit breaker (mock always succeeds)
        message_id = self.circuit_breaker.call(
            self._publish_message,
            topic_path,
            message_data
        )

        return message_id

    def _publish_message(self, topic_path: str, message_data: bytes) -> str:
        """Internal method to publish message"""
        future = self.client.publish(topic_path, message_data)
        return future.result(timeout=settings.pubsub_timeout)

    def health_check(self) -> Dict[str, Any]:
        """Mock health check (always healthy)"""
        stats = self.client.get_stats()

        return {
            "status": "healthy",
            "type": "mock",
            "circuit_breaker_state": "CLOSED",
            "project_id": self.project_id,
            "available_topics": list(self.topic_mapping.values()),
            "mock_stats": stats
        }

    def get_mock_data(self) -> Dict[str, Any]:
        """Get mock-specific data for debugging"""
        return {
            "published_messages": self.client.get_published_messages(),
            "stats": self.client.get_stats()
        }

    def clear_mock_data(self, topic_name: Optional[str] = None) -> None:
        """Clear mock data"""
        self.client.clear_messages(topic_name)


class MockCircuitBreaker:
    """Mock circuit breaker that always succeeds"""

    def __init__(self):
        self.state_name = "CLOSED"

    def call(self, func, *args, **kwargs):
        """Execute function (always succeeds in mock)"""
        return func(*args, **kwargs)

    @property
    def state(self):
        """Mock state object"""
        return type('MockState', (), {'name': self.state_name})()


# Global mock instances
mock_pubsub_client = MockPublisherClient()
mock_pubsub_service = MockPubSubService()
