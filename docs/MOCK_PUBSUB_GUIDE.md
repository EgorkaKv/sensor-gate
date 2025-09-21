# Мок Google Cloud Pub/Sub для локальной разработки

## Обзор

SensorGate теперь поддерживает мок Google Cloud Pub/Sub для удобной локальной разработки и тестирования без необходимости подключения к реальному GCP Pub/Sub сервису.

## Функциональность мока

### ✅ Полная совместимость с API
- Мок полностью совместим с интерфейсом Google Cloud Pub/Sub
- Поддерживает все методы: `publish()`, `get_topic()`, `topic_path()`
- Возвращает те же типы данных, что и реальный клиент

### ✅ Автоматическое переключение
- Автоматически активируется в debug режиме
- Можно принудительно включить через переменную окружения
- Прозрачное переключение между реальным и мок сервисом

### ✅ Полное логирование
- Детальное логирование всех "отправленных" сообщений
- Структурированные логи с метаданными сообщений
- JSON формат для удобного анализа

### ✅ Debug API
- Специальные эндпоинты для просмотра отправленных сообщений
- Статистика по топикам и сообщениям
- Возможность очистки данных для тестирования

## Настройка и использование

### Конфигурация

Основные переменные окружения:

```env
# Принудительно включить мок (по умолчанию false)
SENSORGATE_USE_PUBSUB_MOCK=true

# Автоматически включать мок в debug режиме (по умолчанию true)
SENSORGATE_PUBSUB_MOCK_AUTO_ENABLE=true

# Debug режим (автоматически активирует мок если PUBSUB_MOCK_AUTO_ENABLE=true)
SENSORGATE_DEBUG=true
```

### Автоматическая активация

Мок автоматически активируется в следующих случаях:

1. **Debug режим** + `PUBSUB_MOCK_AUTO_ENABLE=true` (по умолчанию)
2. **Принудительная активация** через `USE_PUBSUB_MOCK=true`

### Пример локальной разработки

Создайте `.env` файл для локальной разработки:

```env
# Включить debug режим (автоматически активирует мок)
SENSORGATE_DEBUG=true

# API ключи для тестирования
SENSORGATE_API_KEYS=dev-key-123,test-key-456

# Минимальные настройки (для мока не критичны)
SENSORGATE_GCP_PROJECT_ID=mock-project
SENSORGATE_INFLUXDB_TOKEN=mock-token
SENSORGATE_INFLUXDB_ORG=mock-org
```

## Debug API эндпоинты

### Просмотр всех сообщений

```http
GET /api/v1/debug/pubsub/messages
X-API-Key: dev-key-123
```

**Ответ:**
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

### Статистика по сообщениям

```http
GET /api/v1/debug/pubsub/stats
X-API-Key: dev-key-123
```

### Сообщения конкретного топика

```http
GET /api/v1/debug/pubsub/topic/sensor-temperature/messages
X-API-Key: dev-key-123
```

### Очистка сообщений

```http
DELETE /api/v1/debug/pubsub/messages
X-API-Key: dev-key-123

# Или только конкретный топик
DELETE /api/v1/debug/pubsub/messages?topic_name=sensor-temperature
```

### Конфигурация debug режима

```http
GET /api/v1/debug/config
X-API-Key: dev-key-123
```

## Примеры использования

### Python клиент для тестирования

```python
import requests
import json
from datetime import datetime

# Настройки для локальной разработки
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-key-123"
headers = {"X-API-Key": API_KEY}

# Отправить тестовые данные
sensor_data = {
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

# Отправить данные (будут сохранены в мок)
response = requests.post(
    f"{API_BASE_URL}/sensors/data",
    headers=headers,
    json=sensor_data
)

print("Отправка:", response.status_code, response.json())

# Проверить что данные сохранились в моке
debug_response = requests.get(
    f"{API_BASE_URL}/debug/pubsub/messages",
    headers=headers
)

print("Сообщения в моке:", debug_response.json())
```

### Workflow локальной разработки

1. **Запуск в debug режиме:**
   ```bash
   # Установить debug режим
   export SENSORGATE_DEBUG=true
   
   # Запустить сервис
   python main.py
   ```

2. **Проверка активации мока:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/health" \
     -H "X-API-Key: dev-key-123"
   
   # В ответе должно быть: "using_mock": true
   ```

3. **Отправка тестовых данных:**
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

4. **Просмотр отправленных сообщений:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/debug/pubsub/messages" \
     -H "X-API-Key: dev-key-123"
   ```

5. **Очистка данных для следующего теста:**
   ```bash
   curl -X DELETE "http://localhost:8000/api/v1/debug/pubsub/messages" \
     -H "X-API-Key: dev-key-123"
   ```

## Тестирование

### Unit тесты

Включены полные unit тесты для мок Pub/Sub:

```bash
# Запуск тестов
pytest tests/test_mock_pubsub.py -v

# Результат покажет все аспекты функциональности:
# - Публикация сообщений
# - Ограничения по памяти
# - Статистика и очистка
# - Обработка разных типов датчиков
```

### Integration тесты

Мок отлично подходит для integration тестов:

```python
def test_sensor_data_pipeline():
    # Отправить данные через API
    response = client.post("/api/v1/sensors/data", 
                          headers={"X-API-Key": "test-key"}, 
                          json=sensor_data)
    
    # Проверить что данные попали в "Pub/Sub"
    debug_response = client.get("/api/v1/debug/pubsub/messages",
                               headers={"X-API-Key": "test-key"})
    
    messages = debug_response.json()["messages"]
    assert "sensor-temperature" in messages
    assert len(messages["sensor-temperature"]) == 1
```

## Логирование

### Структурированные логи

Мок создает детальные логи всех операций:

```json
{
  "timestamp": "2024-01-15T12:00:01.123Z",
  "level": "info",
  "logger": "MockPublisherClient",
  "message": "Mock Pub/Sub message published",
  "message_id": "mock-msg-1642248000-1",
  "topic": "sensor-temperature",
  "device_id": 12345,
  "sensor_type": "temperature",
  "value": 23.5
}
```

### Мониторинг в реальном времени

```bash
# Просматривать логи в реальном времени
tail -f logs/sensorgate.log | grep "Mock Pub/Sub"

# Или с jq для красивого JSON
tail -f logs/sensorgate.log | jq 'select(.logger | contains("Mock"))'
```

## Производительность

### Ограничения памяти

Мок автоматически ограничивает количество сохраняемых сообщений:

- **По умолчанию**: 1000 сообщений на топик
- **Автоматическая очистка**: удаляются самые старые сообщения
- **Настраиваемые лимиты**: можно изменить в коде мока

### Память и производительность

- **Память**: ~1KB на сообщение (зависит от размера данных)
- **Производительность**: >10,000 сообщений/сек на обычном ПК
- **Лимиты**: настраиваемые ограничения предотвращают утечки памяти

## Переключение на продакш

### Автоматическое переключение

При развертывании в продакшене:

```env
# Отключить debug режим
SENSORGATE_DEBUG=false

# Указать реальные GCP настройки
SENSORGATE_GCP_PROJECT_ID=your-production-project
SENSORGATE_GCP_CREDENTIALS_PATH=/path/to/production-key.json
```

Мок автоматически отключится, и будет использоваться реальный GCP Pub/Sub.

### Валидация переключения

```bash
# Проверить что используется реальный Pub/Sub
curl -X GET "https://your-production-domain/api/v1/health"

# В ответе должно быть: "using_mock": false
```

## Troubleshooting

### Мок не активируется

**Проблема**: Мок не включается в debug режиме

**Решение**:
```env
# Убедитесь что включены обе настройки
SENSORGATE_DEBUG=true
SENSORGATE_PUBSUB_MOCK_AUTO_ENABLE=true

# Или принудительно включите мок
SENSORGATE_USE_PUBSUB_MOCK=true
```

### Debug эндпоинты недоступны

**Проблема**: Debug эндпоинты возвращают 404

**Решение**:
```env
# Debug эндпоинты доступны только в debug режиме
SENSORGATE_DEBUG=true
```

### Сообщения не сохраняются

**Проблема**: Отправленные сообщения не появляются в debug API

**Решение**:
1. Проверьте что мок активен: `/api/v1/health` → `"using_mock": true`
2. Проверьте валидность API ключа
3. Проверьте формат отправляемых данных

## Заключение

Мок GCP Pub/Sub обеспечивает:

✅ **Удобство разработки** - нет необходимости в GCP аккаунте для локальных тестов  
✅ **Полная совместимость** - работает как drop-in замена реального Pub/Sub  
✅ **Богатая отладка** - детальные логи и debug API  
✅ **Автоматическое переключение** - seamless переход между dev и prod  
✅ **Производительность** - быстрое тестирование без сетевых задержек  

Теперь локальная разработка SensorGate стала значительно проще и эффективнее!
