import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config import settings
# from app.core.logging import LoggerMixin
from app.models.history import (
    HistoryQueryParams, HistoricalDataPoint, AggregatedDataPoint,
    DeviceInfo, SensorTypeStats, AggregationType
)
from app.models.sensor import SensorType

# class InfluxDBService(LoggerMixin):
class InfluxDBService:
    """Service for interacting with InfluxDB for historical sensor data"""

    def __init__(self):
        self.client: Optional[InfluxDBClient] = None
        self.query_api: Optional[QueryApi] = None
        self.bucket = settings.influxdb_bucket
        self.org = settings.influxdb_org
        self._initialize_client()

    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            self.client = InfluxDBClient(
                url=settings.influxdb_url,
                token=settings.influxdb_token,
                org=self.org,
                timeout=settings.influxdb_timeout
            )
            self.query_api = self.client.query_api()
            print('InfluxDB client initialized successfully',
                  'url:', settings.influxdb_url,
                  'org:',self.org,
                  'bucket:',self.bucket)

        except Exception as e:
            print('Failed to initialize InfluxDB client:', e)
            raise

    def _build_base_query(self, params: HistoryQueryParams) -> str:
        """Build base Flux query from parameters"""
        query_parts = [
            f'from(bucket: "{self.bucket}")',
            f'|> range(start: {params.start_time.isoformat()}Z, stop: {params.end_time.isoformat()}Z)',
            '|> filter(fn: (r) => r["_measurement"] == "sensor_data")'
        ]

        # Add sensor type filter
        if params.sensor_type:
            query_parts.append(f'|> filter(fn: (r) => r["sensor_type"] == "{params.sensor_type.value}")')

        # Add device ID filter
        if params.device_id:
            query_parts.append(f'|> filter(fn: (r) => r["device_id"] == "{params.device_id}")')

        # Add location filters
        if params.latitude_min is not None:
            query_parts.append(f'|> filter(fn: (r) => r["latitude"] >= {params.latitude_min})')
        if params.latitude_max is not None:
            query_parts.append(f'|> filter(fn: (r) => r["latitude"] <= {params.latitude_max})')
        if params.longitude_min is not None:
            query_parts.append(f'|> filter(fn: (r) => r["longitude"] >= {params.longitude_min})')
        if params.longitude_max is not None:
            query_parts.append(f'|> filter(fn: (r) => r["longitude"] <= {params.longitude_max})')

        return '\n  '.join(query_parts)

    def _build_aggregation_query(self, base_query: str, aggregation: AggregationType) -> str:
        """Add aggregation to base query"""
        aggregation_map = {
            AggregationType.MEAN: "mean",
            AggregationType.MIN: "min",
            AggregationType.MAX: "max",
            AggregationType.COUNT: "count",
            AggregationType.SUM: "sum",
            AggregationType.FIRST: "first",
            AggregationType.LAST: "last"
        }

        agg_func = aggregation_map.get(aggregation, "mean")

        query = f"""
{base_query}
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: ["sensor_type", "device_id"])
  |> {agg_func}()
  |> yield(name: "aggregated")
"""
        return query

    async def query_historical_data(self, params: HistoryQueryParams) -> List[HistoricalDataPoint]:
        """Query historical sensor data points"""
        start_time = time.time()

        try:
            base_query = self._build_base_query(params)
            query = f"""
{base_query}
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"])
"""

            # self.logger.info("Executing InfluxDB query for historical data",
            #                start_time=params.start_time.isoformat(),
            #                end_time=params.end_time.isoformat(),
            #                sensor_type=params.sensor_type.value if params.sensor_type else None,
            #                device_id=params.device_id)

            tables = self.query_api.query(query, org=self.org)

            data_points = []
            for table in tables:
                for record in table.records:
                    try:
                        data_point = HistoricalDataPoint(
                            timestamp=record.get_time(),
                            device_id=int(record.values.get("device_id", 0)),
                            sensor_type=SensorType(record.values.get("sensor_type", "temperature")),
                            value=float(record.values.get("value", 0.0)),
                            latitude=float(record.values.get("latitude", 0.0)),
                            longitude=float(record.values.get("longitude", 0.0))
                        )
                        data_points.append(data_point)
                    except (ValueError, TypeError) as e:
                        print('Skipping invalid data point:', e, 'record:', record.values)
                        continue

            return data_points

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            print('Failed to query historical data:', e,)
            raise

    async def query_aggregated_data(self, params: HistoryQueryParams) -> List[AggregatedDataPoint]:
        """Query aggregated historical sensor data"""
        start_time = time.time()

        try:
            base_query = self._build_base_query(params)
            query = self._build_aggregation_query(base_query, params.aggregation)

            tables = self.query_api.query(query, org=self.org)

            # Also get count for each aggregation
            count_query = self._build_aggregation_query(base_query, AggregationType.COUNT)
            count_tables = self.query_api.query(count_query, org=self.org)

            # Create mapping of (sensor_type, device_id) -> count
            count_map = {}
            for table in count_tables:
                for record in table.records:
                    key = (record.values.get("sensor_type"), record.values.get("device_id"))
                    count_map[key] = int(record.get_value() or 0)

            aggregated_points = []
            for table in tables:
                for record in table.records:
                    try:
                        sensor_type = record.values.get("sensor_type")
                        device_id = record.values.get("device_id")
                        key = (sensor_type, device_id)
                        count = count_map.get(key, 0)

                        aggregated_point = AggregatedDataPoint(
                            sensor_type=SensorType(sensor_type),
                            device_id=int(device_id) if device_id else None,
                            aggregation_type=params.aggregation,
                            value=float(record.get_value() or 0.0),
                            count=count,
                            start_time=params.start_time,
                            end_time=params.end_time
                        )
                        aggregated_points.append(aggregated_point)
                    except (ValueError, TypeError) as e:
                        print("Skipping invalid aggregated point:", e, "record:", record.values)
                        continue

            return aggregated_points

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            print('Failed to query aggregated data:', e)
            raise

    async def get_device_list(self, sensor_type: Optional[SensorType] = None) -> List[DeviceInfo]:
        """Get list of all devices with their information"""
        start_time = time.time()

        try:
            # Base query for device info
            sensor_filter = f'|> filter(fn: (r) => r["sensor_type"] == "{sensor_type.value}")' if sensor_type else ""

            query = f"""
import "experimental/aggregate"

devices = from(bucket: "{self.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  {sensor_filter}
  |> group(columns: ["device_id"])
  |> aggregate.rate(every: 30d, unit: 1h)
  |> group()
  |> keep(columns: ["device_id"])
  |> distinct(column: "device_id")

devices
"""

            tables = self.query_api.query(query, org=self.org)
            device_ids = []
            for table in tables:
                for record in table.records:
                    device_id = record.values.get("device_id")
                    if device_id:
                        device_ids.append(int(device_id))

            # Get detailed info for each device
            devices = []
            for device_id in device_ids:
                device_info = await self._get_device_info(device_id, sensor_type)
                if device_info:
                    devices.append(device_info)
            return devices

        except Exception as e:
            print('Failed to get device list:', e)
            raise

    async def _get_device_info(self, device_id: int, sensor_type_filter: Optional[SensorType] = None) -> Optional[DeviceInfo]:
        """Get detailed information for a specific device"""
        try:
            sensor_filter = f'|> filter(fn: (r) => r["sensor_type"] == "{sensor_type_filter.value}")' if sensor_type_filter else ""

            query = f"""
device_data = from(bucket: "{self.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["device_id"] == "{device_id}")
  {sensor_filter}

sensor_types = device_data
  |> keep(columns: ["sensor_type"])
  |> distinct(column: "sensor_type")

stats = device_data
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: ["device_id"])
  |> aggregateWindow(every: 30d, fn: count)
  |> yield(name: "count")

first_last = device_data
  |> filter(fn: (r) => r["_field"] == "value")  
  |> group(columns: ["device_id"])
  |> first()
  |> set(key: "stat", value: "first")
  |> union(tables: [
      device_data
      |> filter(fn: (r) => r["_field"] == "value")
      |> group(columns: ["device_id"])
      |> last()
      |> set(key: "stat", value: "last")
  ])

location = device_data
  |> filter(fn: (r) => r["_field"] == "latitude" or r["_field"] == "longitude")
  |> group(columns: ["device_id"])
  |> last()
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
"""

            tables = self.query_api.query(query, org=self.org)

            sensor_types = []
            total_measurements = 0
            first_seen = None
            last_seen = None
            last_location = {"latitude": 0.0, "longitude": 0.0}

            for table in tables:
                table_name = table.records[0].table if table.records else 0

                for record in table.records:
                    if "sensor_type" in record.values:
                        sensor_type_str = record.values.get("sensor_type")
                        try:
                            sensor_types.append(SensorType(sensor_type_str))
                        except ValueError:
                            continue

                    elif record.values.get("stat") == "first":
                        first_seen = record.get_time()
                    elif record.values.get("stat") == "last":
                        last_seen = record.get_time()

                    elif record.values.get("_field") == "value" and "count" in str(table_name):
                        total_measurements += int(record.get_value() or 0)

                    elif "latitude" in record.values and "longitude" in record.values:
                        last_location = {
                            "latitude": float(record.values.get("latitude", 0.0)),
                            "longitude": float(record.values.get("longitude", 0.0))
                        }

            if not sensor_types or not first_seen or not last_seen:
                return None

            return DeviceInfo(
                device_id=device_id,
                sensor_types=list(set(sensor_types)),  # Remove duplicates
                first_seen=first_seen,
                last_seen=last_seen,
                total_measurements=total_measurements,
                last_location=last_location
            )

        except Exception as e:
            print('Failed to get info for device', device_id, ':', e)
            return None

    async def get_sensor_type_stats(self) -> List[SensorTypeStats]:
        """Get statistics for each sensor type"""
        start_time = time.time()

        try:
            query = f"""
data = from(bucket: "{self.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["_field"] == "value")

device_counts = data
  |> group(columns: ["sensor_type"])
  |> distinct(column: "device_id")
  |> count()
  |> set(key: "stat", value: "device_count")

measurement_counts = data
  |> group(columns: ["sensor_type"])
  |> count()
  |> set(key: "stat", value: "measurement_count")

value_stats = data
  |> group(columns: ["sensor_type"])
  |> aggregateWindow(every: 30d, fn: mean)
  |> set(key: "stat", value: "mean")
  |> union(tables: [
      data |> group(columns: ["sensor_type"]) |> min() |> set(key: "stat", value: "min"),
      data |> group(columns: ["sensor_type"]) |> max() |> set(key: "stat", value: "max")
  ])

time_range = data
  |> group(columns: ["sensor_type"])
  |> first()
  |> set(key: "stat", value: "first")
  |> union(tables: [
      data |> group(columns: ["sensor_type"]) |> last() |> set(key: "stat", value: "last")
  ])

union(tables: [device_counts, measurement_counts, value_stats, time_range])
"""

            tables = self.query_api.query(query, org=self.org)

            # Group results by sensor type
            stats_by_type = {}

            for table in tables:
                for record in table.records:
                    sensor_type_str = record.values.get("sensor_type")
                    if not sensor_type_str:
                        continue

                    try:
                        sensor_type = SensorType(sensor_type_str)
                    except ValueError:
                        continue

                    if sensor_type not in stats_by_type:
                        stats_by_type[sensor_type] = {
                            "device_count": 0,
                            "total_measurements": 0,
                            "first_measurement": None,
                            "last_measurement": None,
                            "value_stats": {"min": 0.0, "max": 0.0, "mean": 0.0}
                        }

                    stat_type = record.values.get("stat")
                    value = record.get_value()

                    if stat_type == "device_count":
                        stats_by_type[sensor_type]["device_count"] = int(value or 0)
                    elif stat_type == "measurement_count":
                        stats_by_type[sensor_type]["total_measurements"] = int(value or 0)
                    elif stat_type == "first":
                        stats_by_type[sensor_type]["first_measurement"] = record.get_time()
                    elif stat_type == "last":
                        stats_by_type[sensor_type]["last_measurement"] = record.get_time()
                    elif stat_type in ["min", "max", "mean"]:
                        stats_by_type[sensor_type]["value_stats"][stat_type] = float(value or 0.0)

            # Convert to response models
            sensor_stats = []
            for sensor_type, stats in stats_by_type.items():
                if stats["first_measurement"] and stats["last_measurement"]:
                    sensor_stat = SensorTypeStats(
                        sensor_type=sensor_type,
                        device_count=stats["device_count"],
                        total_measurements=stats["total_measurements"],
                        first_measurement=stats["first_measurement"],
                        last_measurement=stats["last_measurement"],
                        value_stats=stats["value_stats"]
                    )
                    sensor_stats.append(sensor_stat)
            return sensor_stats

        except Exception as e:
            print('Failed to get sensor type stats:', e)
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check InfluxDB service health"""
        try:
            # Simple ping to check connectivity
            health = self.client.health()

            return {
                "status": "healthy" if health.status == "pass" else "unhealthy",
                "url": settings.influxdb_url,
                "org": self.org,
                "bucket": self.bucket,
                "version": health.version if hasattr(health, 'version') else 'unknown'
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "url": settings.influxdb_url
            }


# Global InfluxDB service instance
influxdb_service = InfluxDBService()
