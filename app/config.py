from typing import Dict, List, ClassVar, Type, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application settings
    app_name: str = "SensorGate"
    app_version: str = "0.1.0"
    host: str
    port: int
    debug: bool

    # API Security
    api_keys: List[str] = []
    public_access_enabled: bool = False  # Allow access without API keys

    # Google Cloud Pub/Sub settings
    gcp_project_id: str
    gcp_credentials_path: str = ""

    # Pub/Sub topic mapping for sensor types
    pubsub_topic_temperature: str = "sensor-temperature"
    pubsub_topic_humidity: str = "sensor-humidity"
    pubsub_topic_ndir: str = "sensor-ndir"

    # Pub/Sub client settings
    pubsub_timeout: float = 30.0
    pubsub_retry_attempts: int = 3
    pubsub_retry_delay: float = 1.0

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: ClassVar[Type[Exception]] = Exception

    # Pub/Sub Mock settings (for local development)
    use_pubsub_mock: bool = False
    pubsub_mock_auto_enable: bool = True  # Auto-enable mock in debug mode

    # InfluxDB settings
    influxdb_url: str = "https://us-east-1-1.aws.cloud2.influxdata.com"
    influxdb_token: str = ""
    influxdb_org: str = ""
    influxdb_bucket: str = "iot-sensors"
    influxdb_username: str = ""
    influxdb_password: str = ""
    influxdb_timeout: int = 30000  # milliseconds

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {valid_levels}')
        return v.upper()

    @property
    def sensor_topic_mapping(self) -> Dict[str, str]:
        """Get mapping of sensor types to Pub/Sub topics"""
        return {
            "temperature": self.pubsub_topic_temperature,
            "humidity": self.pubsub_topic_humidity,
            "ndir": self.pubsub_topic_ndir
        }

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "SENSORGATE_"
    }


# Global settings instance
settings = Settings()
