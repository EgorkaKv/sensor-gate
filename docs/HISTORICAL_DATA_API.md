# Historical Data API Guide

## Overview

SensorGate теперь поддерживает получение исторических данных с датчиков из InfluxDB Cloud. Добавлены новые эндпоинты для различных сценариев запросов.

## Новые эндпоинты

### 1. Получение исторических данных
**GET** `/api/v1/sensors/history`

Базовый эндпоинт для получения исторических данных с фильтрацией.

**Параметры:**
- `start_time` (обязательный): Начальное время в ISO 8601 формате
- `end_time` (обязательный): Конечное время в ISO 8601 формате
- `sensor_type` (опционально): Тип датчика (temperature, humidity, ndir)
- `device_id` (опционально): ID конкретного устройства
- `latitude_min/max` (опционально): Фильтр по широте
- `longitude_min/max` (опционально): Фильтр по долготе

**Пример запроса:**
```http
GET /api/v1/sensors/history?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&sensor_type=temperature
```

### 2. Получение агрегированных данных
**GET** `/api/v1/sensors/history/aggregated`

Получение агрегированных данных с различными типами агрегации.

**Дополнительные параметры:**
- `aggregation`: Тип агрегации (mean, min, max, count, sum, first, last)

**Пример запроса:**
```http
GET /api/v1/sensors/history/aggregated?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&aggregation=mean&sensor_type=temperature
```

### 3. Данные по типу датчика
**GET** `/api/v1/sensors/history/by-sensor-type/{sensor_type}`

Получение данных для всех устройств определенного типа датчика.

**Пример запроса:**
```http
GET /api/v1/sensors/history/by-sensor-type/temperature?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z
```

### 4. Данные по ID устройства
**GET** `/api/v1/sensors/history/by-device/{device_id}`

Получение данных для конкретного устройства.

**Пример запроса:**
```http
GET /api/v1/sensors/history/by-device/12345?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z
```

### 5. Список всех устройств
**GET** `/api/v1/sensors/devices`

Получение списка всех устройств с метаданными.

**Параметры:**
- `sensor_type` (опционально): Фильтр по типу датчика

**Пример запроса:**
```http
GET /api/v1/sensors/devices?sensor_type=temperature
```

### 6. Статистика по типам датчиков
**GET** `/api/v1/sensors/stats`

Получение общей статистики по всем типам датчиков.

**Пример запроса:**
```http
GET /api/v1/sensors/stats
```

## Формат ответов

### Исторические данные
```json
{
  "data": [
    {
      "timestamp": "2024-01-15T12:30:00Z",
      "device_id": 12345,
      "sensor_type": "temperature",
      "value": 23.5,
      "latitude": 55.7558,
      "longitude": 37.6176
    }
  ],
  "total_count": 150,
  "query_params": {...},
  "execution_time_ms": 125.5
}
```

### Агрегированные данные
```json
{
  "data": [
    {
      "sensor_type": "temperature",
      "device_id": 12345,
      "aggregation_type": "mean",
      "value": 23.2,
      "count": 150,
      "start_time": "2024-01-15T12:00:00Z",
      "end_time": "2024-01-15T13:00:00Z"
    }
  ],
  "total_count": 150,
  "query_params": {...},
  "execution_time_ms": 89.3
}
```

### Список устройств
```json
{
  "devices": [
    {
      "device_id": 12345,
      "sensor_types": ["temperature", "humidity"],
      "first_seen": "2024-01-01T00:00:00Z",
      "last_seen": "2024-01-15T12:59:59Z",
      "total_measurements": 5240,
      "last_location": {
        "latitude": 55.7558,
        "longitude": 37.6176
      }
    }
  ],
  "total_count": 25,
  "sensor_type_filter": "temperature"
}
```

## Примеры использования

### Python клиент
```python
import requests
from datetime import datetime, timedelta

# Настройки
API_BASE_URL = "http://your-sensorgate-domain/api/v1"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

# Получить данные за последний час
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

params = {
    "start_time": start_time.isoformat() + "Z",
    "end_time": end_time.isoformat() + "Z",
    "sensor_type": "temperature"
}

response = requests.get(
    f"{API_BASE_URL}/sensors/history",
    headers=headers,
    params=params
)

if response.status_code == 200:
    data = response.json()
    print(f"Получено {data['total_count']} точек данных")
    for point in data['data']:
        print(f"Устройство {point['device_id']}: {point['value']}°C в {point['timestamp']}")
```

### cURL примеры
```bash
# Получить температурные данные за последний час
curl -X GET "http://your-domain/api/v1/sensors/history?start_time=2024-01-15T12:00:00Z&end_time=2024-01-15T13:00:00Z&sensor_type=temperature" \
  -H "X-API-Key: your-api-key"

# Получить агрегированные данные (среднее)
curl -X GET "http://your-domain/api/v1/sensors/history/aggregated?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&aggregation=mean" \
  -H "X-API-Key: your-api-key"

# Получить список устройств
curl -X GET "http://your-domain/api/v1/sensors/devices" \
  -H "X-API-Key: your-api-key"
```

## Конфигурация InfluxDB

Добавьте в ваш `.env` файл:

```env
# InfluxDB настройки
SENSORGATE_INFLUXDB_URL=https://us-east-1-1.aws.cloud2.influxdata.com
SENSORGATE_INFLUXDB_TOKEN=GdqEFmuTLknVX_WxJgeJVekhjKN555UBk2A38zFmKdvpz473K64HsYGukC_XtDQXvOF6gX2hafgI9YfqHSDGFw==
SENSORGATE_INFLUXDB_ORG=IoT-lab3
SENSORGATE_INFLUXDB_BUCKET=iot-sensors
SENSORGATE_INFLUXDB_USERNAME=root
SENSORGATE_INFLUXDB_PASSWORD=influx321pass
```

## Health Check

Обновленный health check теперь включает проверку InfluxDB:

```http
GET /api/v1/health
```

Ответ будет включать статус как Pub/Sub, так и InfluxDB соединений.

## Мониторинг

Новые метрики добавлены для исторических запросов:
- `sensorgate_sensor_data_received_total{sensor_type="history_query"}`
- `sensorgate_sensor_data_processed_total{sensor_type="history_query"}`
- `sensorgate_sensor_data_errors_total{sensor_type="history_query"}`

Аналогично для других типов запросов (aggregated_query, device_list, sensor_stats).
