# Настройка общего доступа к API

## Обзор

SensorGate теперь поддерживает настройку общего доступа, которая позволяет вызывать API эндпоинты без необходимости предоставления API-ключей.

## Конфигурация

### Переменная окружения

Для включения общего доступа используйте переменную окружения:

```env
SENSORGATE_PUBLIC_ACCESS_ENABLED=true
```

### Варианты настройки

1. **Общий доступ отключен (по умолчанию):**
   ```env
   SENSORGATE_PUBLIC_ACCESS_ENABLED=false
   SENSORGATE_API_KEYS=your-api-key-1,your-api-key-2
   ```
   - Требуется API-ключ для всех запросов
   - Стандартное поведение для продакшена

2. **Общий доступ включен:**
   ```env
   SENSORGATE_PUBLIC_ACCESS_ENABLED=true
   ```
   - API-ключи не требуются
   - Подходит для внутренних сетей или тестирования

## Приоритет аутентификации

Система аутентификации работает по следующему приоритету:

1. **Общий доступ включен** → разрешить все запросы
2. **API-ключи не настроены** → разрешить все запросы (режим разработки)
3. **API-ключи настроены** → требовать валидный API-ключ

## Примеры использования

### С общим доступом (API-ключ не нужен)

```bash
# Отправить данные датчика
curl -X POST "http://localhost:8000/api/v1/sensors/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 12345,
    "sensor_type": "temperature", 
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "2025-09-21T12:00:00Z"
  }'

# Получить исторические данные
curl -X GET "http://localhost:8000/api/v1/sensors/history?start_time=2025-09-21T10:00:00Z&end_time=2025-09-21T12:00:00Z"
```

### Python клиент

```python
import requests
from datetime import datetime

# Настройки
API_BASE_URL = "http://localhost:8000/api/v1"

# С общим доступом заголовки аутентификации не нужны
headers = {"Content-Type": "application/json"}

# Отправить данные
sensor_data = {
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

response = requests.post(
    f"{API_BASE_URL}/sensors/data",
    headers=headers,
    json=sensor_data
)

print("Ответ:", response.status_code, response.json())
```

## Проверка статуса аутентификации

### Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

В ответе будет поле:
```json
{
  "config": {
    "public_access_enabled": true,
    ...
  }
}
```

### Корневой эндпоинт

```bash
curl -X GET "http://localhost:8000/"
```

Ответ:
```json
{
  "service": "SensorGate",
  "authentication": {
    "public_access_enabled": true,
    "api_key_required": false
  },
  ...
}
```

## Логирование

При включенном общем доступе в логах будут появляться записи:

```json
{
  "level": "debug",
  "logger": "AuthService",
  "message": "Public access enabled - allowing request without API key",
  "timestamp": "2025-09-21T12:00:00Z"
}
```

## Сценарии использования

### 1. Локальная разработка

```env
SENSORGATE_DEBUG=true
SENSORGATE_PUBLIC_ACCESS_ENABLED=true
```

### 2. Внутренняя корпоративная сеть

```env
SENSORGATE_PUBLIC_ACCESS_ENABLED=true
SENSORGATE_DEBUG=false
```

### 3. Продакшн с аутентификацией

```env
SENSORGATE_PUBLIC_ACCESS_ENABLED=false
SENSORGATE_API_KEYS=prod-key-123,backup-key-456
```

## Безопасность

### ⚠️ Важные замечания

1. **Не используйте общий доступ в продакшене** без дополнительных мер безопасности
2. **Настройте firewall** для ограничения доступа к API
3. **Используйте HTTPS** для защиты данных в транзите
4. **Мониторьте запросы** для обнаружения аномальной активности

### Рекомендуемые настройки безопасности

```yaml
# Для внутренней сети
firewall:
  - allow from: 192.168.1.0/24
  - deny from: all

# Для публичного доступа
rate_limiting:
  requests_per_minute: 100
  burst: 20
```

## Troubleshooting

### Проблема: Запросы все еще требуют API-ключ

**Решение:**
1. Проверьте переменную окружения:
   ```bash
   echo $SENSORGATE_PUBLIC_ACCESS_ENABLED
   ```
2. Убедитесь что сервис перезапущен после изменения настроек
3. Проверьте статус через health check

### Проблема: Не работает в debug режиме

**Решение:**
Общий доступ работает независимо от debug режима. Проверьте:
```env
SENSORGATE_PUBLIC_ACCESS_ENABLED=true  # Должно быть true
```

## Заключение

Функция общего доступа обеспечивает:

✅ **Упрощение разработки** - нет необходимости настраивать API-ключи  
✅ **Гибкость конфигурации** - легкое переключение между режимами  
✅ **Обратная совместимость** - существующие клиенты продолжают работать  
✅ **Прозрачное логирование** - все запросы логируются одинаково  

Используйте эту функцию осознанно, учитывая требования безопасности вашего окружения.
