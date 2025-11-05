# Qlib-UI Logging - Quick Reference Guide

## Setup (One-time in main.py)

```python
from app.modules.common.logging import setup_logging
from app.config import settings

setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    environment=settings.APP_ENV
)
```

## Basic Usage

```python
from app.modules.common.logging import get_logger

logger = get_logger(__name__)

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# With extra data
logger.info("User action", extra={"user_id": "123", "action": "delete"})
```

## Context Management

```python
from app.modules.common.logging import set_correlation_id, set_user_id, clear_context

# Set context (automatically included in all logs)
correlation_id = set_correlation_id()  # Auto-generated
set_user_id("user_123")

# Your code here...

# Clear context (end of request)
clear_context()
```

## Decorators

```python
from app.modules.common.logging import log_execution, log_async_execution

# Sync function
@log_execution(level="INFO", log_args=True, log_result=True)
def process_data(data: dict):
    return {"result": "success"}

# Async function
@log_async_execution(level="INFO", log_args=True, log_result=False)
async def fetch_data(url: str):
    return await client.get(url)
```

## Audit Logging

```python
from app.modules.common.logging import AuditLogger, AuditEventType, AuditSeverity

# Login event
AuditLogger.log_authentication(
    event_type=AuditEventType.LOGIN_SUCCESS,
    user_id="user_123",
    username="john_doe",
    ip_address="192.168.1.100"
)

# Data access
AuditLogger.log_data_access(
    event_type=AuditEventType.DATA_DELETED,
    user_id="user_123",
    resource_type="dataset",
    resource_id="dataset_456",
    records_affected=100
)

# Security violation
AuditLogger.log_security_violation(
    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
    user_id="user_123",
    ip_address="192.168.1.100",
    violation_type="api_rate_limit",
    details={"limit": 100, "actual": 150}
)
```

## PII Filtering

```python
from app.modules.common.logging import sanitize_log_data

# Sanitize sensitive data
user_data = {
    "username": "john",
    "password": "secret123",  # Will be redacted
    "api_key": "sk-1234567890"  # Will be redacted
}

safe_data = sanitize_log_data(user_data)
logger.info("User data", extra={"data": safe_data})
```

## FastAPI Integration

```python
from fastapi import Request
from app.modules.common.logging import get_logger, set_user_id

logger = get_logger(__name__)

@router.post("/datasets")
async def create_dataset(request: Request, data: DatasetCreate):
    # Correlation ID is already set by middleware
    # Set user from auth
    set_user_id(request.state.user.id)

    logger.info("Creating dataset", extra={"name": data.name})
    # ... your code ...
```

## Database Logging

```python
from app.modules.common.logging.database import setup_database_logging

# Setup once when creating the engine
engine = create_async_engine(settings.DATABASE_URL)
setup_database_logging(
    engine,
    slow_query_threshold_ms=100.0
)
```

## Common Event Types

### Authentication
- `AuditEventType.LOGIN_SUCCESS`
- `AuditEventType.LOGIN_FAILED`
- `AuditEventType.LOGOUT`
- `AuditEventType.PASSWORD_CHANGED`

### Authorization
- `AuditEventType.ACCESS_GRANTED`
- `AuditEventType.ACCESS_DENIED`
- `AuditEventType.PERMISSION_CHANGED`

### Data Access
- `AuditEventType.DATA_READ`
- `AuditEventType.DATA_CREATED`
- `AuditEventType.DATA_UPDATED`
- `AuditEventType.DATA_DELETED`
- `AuditEventType.DATA_EXPORTED`

### Admin Actions
- `AuditEventType.USER_CREATED`
- `AuditEventType.USER_UPDATED`
- `AuditEventType.USER_DELETED`
- `AuditEventType.USER_DEACTIVATED`

### Security
- `AuditEventType.RATE_LIMIT_EXCEEDED`
- `AuditEventType.SUSPICIOUS_ACTIVITY`
- `AuditEventType.SQL_INJECTION_ATTEMPT`

## Log Levels

| Level | When to Use |
|-------|-------------|
| DEBUG | Detailed diagnostic information |
| INFO | General informational messages |
| WARNING | Potentially harmful situations |
| ERROR | Error events that still allow the app to continue |
| CRITICAL | Severe errors that may cause shutdown |

## Sensitive Fields (Auto-Redacted)

- `password`, `passwd`, `pwd`
- `secret`, `api_key`, `apikey`
- `token`, `access_token`, `refresh_token`
- `authorization`, `auth`
- `credit_card`, `card_number`, `cvv`
- `ssn`, `social_security`
- `private_key`, `session_id`, `cookie`

## Log Files

| File | Contains |
|------|----------|
| `app_{date}.log` | All application logs |
| `error_{date}.log` | Errors and critical only |
| `audit_{date}.log` | Security/audit events |
| `database_{date}.log` | Database queries |

## Environment Variables

```bash
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_FORMAT=json
LOG_ROTATION_SIZE=100 MB
LOG_RETENTION_DAYS=30
SLOW_QUERY_THRESHOLD_MS=100.0
SLOW_REQUEST_THRESHOLD_MS=1000.0
```

## Testing

```bash
# Run test suite
python test_logging_setup.py
```

## Tips

1. **Always use context in API endpoints**: Correlation ID + User ID
2. **Use decorators for service methods**: Automatic logging
3. **Log audit events for security-critical actions**: Create, update, delete
4. **Sanitize user input before logging**: Use `sanitize_log_data()`
5. **Use appropriate log levels**: DEBUG for dev, INFO for prod
6. **Include relevant context**: Add extra fields to logs

## Quick Examples

### API Endpoint Pattern

```python
@router.post("/items")
async def create_item(request: Request, item: ItemCreate):
    logger = get_logger(__name__)
    set_user_id(request.state.user.id)

    logger.info("Creating item", extra={"item_name": item.name})

    # Create item
    new_item = await service.create(item)

    # Audit log
    AuditLogger.log_data_access(
        event_type=AuditEventType.DATA_CREATED,
        resource_type="item",
        resource_id=new_item.id
    )

    return new_item
```

### Service Method Pattern

```python
class ItemService:
    @log_async_execution(level="INFO", log_time=True)
    async def create(self, item: ItemCreate):
        # Automatic logging
        return await self.repository.create(item)
```

### Error Handling Pattern

```python
try:
    result = await service.process(data)
except ValueError as e:
    logger.error(
        "Validation failed",
        extra={"error": str(e), "data": sanitize_log_data(data)}
    )
    raise
except Exception as e:
    logger.exception("Unexpected error", extra={"data_id": data.id})
    raise
```

## Need More Help?

- **Full Documentation**: `/app/modules/common/logging/IMPLEMENTATION.md`
- **Examples**: `/app/modules/common/logging/EXAMPLES.md`
- **Architecture**: `/app/modules/common/logging/README.md`
- **Summary**: `/backend/LOGGING_SUMMARY.md`

---

**Quick Reference Version**: 1.0.0
**Last Updated**: 2025-11-05
