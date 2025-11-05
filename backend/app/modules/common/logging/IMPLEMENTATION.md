# Qlib-UI Logging System Implementation

## Overview

Production-ready structured logging system built with loguru, providing comprehensive logging capabilities for the Qlib-UI backend application.

## Architecture

```
logging/
├── __init__.py           # Public API exports
├── config.py            # Main logging configuration
├── formatters.py        # JSON and development formatters
├── context.py           # Context variables (correlation_id, user_id)
├── filters.py           # PII and sensitive data filtering
├── middleware.py        # FastAPI logging middleware
├── decorators.py        # Function logging decorators
├── audit.py             # Security audit logging
└── database.py          # Database query logging
```

## Features

### 1. Multiple Output Formats

- **Development**: Human-readable colorized console output
- **Production**: JSON-formatted logs for log aggregation tools (ELK, Splunk, DataDog)

### 2. Multiple Log Files

- `app_{date}.log` - All application logs (JSON format)
- `error_{date}.log` - Errors and critical issues only
- `audit_{date}.log` - Security and compliance events
- `database_{date}.log` - Database queries and performance

### 3. Context Management

Thread-safe context variables using Python's `contextvars`:

- `correlation_id` - Request tracing across services
- `request_id` - Individual request identification
- `user_id` - User-specific logging
- `session_id` - Session tracking

### 4. Automatic PII Filtering

Automatically redacts sensitive data:

- Passwords, API keys, tokens
- Credit card numbers, SSNs
- Custom sensitive fields
- URL credentials

### 5. Performance Monitoring

- Slow query detection (configurable threshold)
- Slow request logging
- Execution time tracking
- Database connection pool monitoring

### 6. Audit Logging

Comprehensive security event tracking:

- Authentication events (login, logout, password changes)
- Authorization events (access granted/denied)
- Data access events (CRUD operations)
- Admin actions (user management)
- Security violations (rate limiting, suspicious activity)

## Configuration

### Environment Variables

```bash
# Logging settings
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_FORMAT=json  # or "text"
LOG_ROTATION_SIZE=100 MB
LOG_RETENTION_DAYS=30
LOG_COMPRESSION=zip

# Performance thresholds
SLOW_QUERY_THRESHOLD_MS=100.0
SLOW_REQUEST_THRESHOLD_MS=1000.0

# Body logging
LOG_REQUEST_BODY=True
LOG_RESPONSE_BODY=False
```

### Setup in main.py

```python
from app.modules.common.logging import setup_logging
from app.config import settings

# Initialize logging before creating the app
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    environment=settings.APP_ENV,
)
```

## Usage Examples

### Basic Logging

```python
from app.modules.common.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# With extra fields
logger.info(
    "User performed action",
    extra={
        "user_id": "123",
        "action": "delete",
        "resource": "dataset"
    }
)
```

### Context Management

```python
from app.modules.common.logging import (
    get_logger,
    set_correlation_id,
    set_user_id,
    clear_context
)

logger = get_logger(__name__)

# Set context for request
correlation_id = set_correlation_id()  # Auto-generated
set_user_id("user_123")

# All logs will include correlation_id and user_id
logger.info("Processing request")

# Clear context at end of request
clear_context()
```

### Decorators

```python
from app.modules.common.logging import log_execution, log_async_execution

# Synchronous function
@log_execution(level="INFO", log_args=True, log_result=True)
def process_data(data: dict, count: int = 10):
    # Function implementation
    return {"processed": True, "count": count}

# Asynchronous function
@log_async_execution(level="INFO", log_args=True, log_result=False)
async def fetch_data(url: str):
    # Async implementation
    return await client.get(url)

# Error handling decorator
@log_error(reraise=False, default_return={})
def risky_operation():
    # If error occurs, logs and returns {}
    raise ValueError("Something went wrong")
```

### Audit Logging

```python
from app.modules.common.logging import AuditLogger, AuditEventType, AuditSeverity

# Authentication event
AuditLogger.log_authentication(
    event_type=AuditEventType.LOGIN_SUCCESS,
    user_id="user_123",
    username="john_doe",
    ip_address="192.168.1.100",
    success=True
)

# Authorization event
AuditLogger.log_authorization(
    event_type=AuditEventType.ACCESS_GRANTED,
    user_id="user_123",
    resource_type="dataset",
    resource_id="dataset_456",
    action="delete",
    granted=True
)

# Data access event
AuditLogger.log_data_access(
    event_type=AuditEventType.DATA_DELETED,
    user_id="user_123",
    resource_type="model",
    resource_id="model_789",
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

### PII Filtering

```python
from app.modules.common.logging import sanitize_log_data, get_logger

logger = get_logger(__name__)

# Data with sensitive fields
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secret123",
    "api_key": "sk-1234567890abcdef",
    "normal_field": "safe data"
}

# Sanitize before logging
sanitized = sanitize_log_data(user_data)
logger.info("User data", extra={"data": sanitized})

# Output: password and api_key will be "***REDACTED***"
```

### Database Logging

```python
from sqlalchemy import create_engine
from app.modules.common.logging.database import setup_database_logging

# Create engine
engine = create_engine("postgresql://...")

# Setup database logging
setup_database_logging(
    engine,
    slow_query_threshold_ms=100.0,
    log_all_queries=False,  # Only log slow queries
    enable_transaction_logging=True,
    enable_pool_monitoring=True
)
```

### FastAPI Middleware

```python
from fastapi import FastAPI
from app.modules.common.logging.middleware import (
    LoggingMiddleware,
    CorrelationIDMiddleware
)

app = FastAPI()

# Add logging middleware (should be first)
app.add_middleware(
    LoggingMiddleware,
    log_request_body=True,
    log_response_body=False,
    skip_healthcheck=True
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)
```

## Log Output Examples

### Development Mode (Console)

```
2025-11-05 09:40:16.006 | INFO     | app.api.users:create_user:45 - Creating new user | correlation_id=abc123 | user_id=admin_1
2025-11-05 09:40:16.156 | WARNING  | app.database.queries:execute:78 - Slow query detected | ⏱ 150.23ms
```

### Production Mode (JSON)

```json
{
  "timestamp": "2025-11-05T01:40:16.006000",
  "level": "INFO",
  "logger": "app.api.users",
  "message": "Creating new user",
  "module": "users",
  "function": "create_user",
  "line": 45,
  "correlation_id": "abc123",
  "user_id": "admin_1",
  "file": {
    "name": "users.py",
    "path": "/app/api/users.py"
  }
}
```

### Audit Log (JSON)

```json
{
  "timestamp": "2025-11-05T01:40:16.110000",
  "level": "INFO",
  "message": "Audit event: auth.login.success",
  "audit": true,
  "event_type": "auth.login.success",
  "severity": "low",
  "user_id": "user_123",
  "correlation_id": "abc123",
  "result": "success",
  "ip_address": "192.168.1.100",
  "details": {
    "username": "john_doe",
    "method": "password"
  }
}
```

## Best Practices

### 1. Always Use Context in API Endpoints

```python
from fastapi import Request
from app.modules.common.logging import get_logger, set_user_id

logger = get_logger(__name__)

@router.post("/datasets")
async def create_dataset(request: Request, data: DatasetCreate):
    # Correlation ID is set by middleware
    # Set user_id from auth
    set_user_id(request.state.user.id)

    logger.info("Creating dataset", extra={"dataset_name": data.name})
    # ... implementation
```

### 2. Use Decorators for Service Methods

```python
from app.modules.common.logging import log_async_execution

class DatasetService:
    @log_async_execution(level="INFO", log_args=True, log_time=True)
    async def create_dataset(self, data: DatasetCreate):
        # Automatic logging of entry, exit, and timing
        return await self.repository.create(data)
```

### 3. Log Audit Events for Security-Critical Actions

```python
from app.modules.common.logging import AuditLogger, AuditEventType

async def delete_dataset(dataset_id: str, user_id: str):
    # Perform deletion
    await repository.delete(dataset_id)

    # Log audit event
    AuditLogger.log_data_access(
        event_type=AuditEventType.DATA_DELETED,
        user_id=user_id,
        resource_type="dataset",
        resource_id=dataset_id,
        action="delete"
    )
```

### 4. Sanitize User Input Before Logging

```python
from app.modules.common.logging import sanitize_log_data, get_logger

logger = get_logger(__name__)

def process_user_data(user_input: dict):
    # Sanitize before logging
    safe_data = sanitize_log_data(user_input)
    logger.info("Processing user data", extra={"input": safe_data})
```

### 5. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information (not in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error events that still allow the application to continue
- **CRITICAL**: Severe errors that may cause application shutdown

### 6. Include Relevant Context

```python
logger.info(
    "Dataset processing completed",
    extra={
        "dataset_id": dataset.id,
        "records_processed": count,
        "execution_time_ms": duration_ms,
        "success": True
    }
)
```

## Performance Considerations

1. **Async Logging**: All file handlers use `enqueue=True` for non-blocking I/O
2. **Log Rotation**: Automatic rotation prevents disk space issues
3. **Compression**: Old logs are compressed to save space
4. **Selective Logging**: Only log slow queries and errors in production
5. **PII Filtering**: Minimal performance overhead with regex patterns

## Monitoring and Analysis

### ELK Stack Integration

```json
{
  "timestamp": "2025-11-05T01:40:16.006000",
  "level": "INFO",
  "logger": "app.api.users",
  "message": "Creating new user",
  "correlation_id": "abc123",
  "user_id": "admin_1"
}
```

### Query Examples

```
# Find all logs for a specific request
correlation_id: "abc123"

# Find slow queries
slow_query: true AND query_time_ms: >100

# Find failed logins
event_type: "auth.login.failed"

# Find errors by user
level: "ERROR" AND user_id: "user_123"
```

## Testing

Run the comprehensive test suite:

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend
python test_logging_setup.py
```

The test covers:

- Basic logging
- Context management
- PII filtering
- Decorators (sync and async)
- Audit logging
- Error logging
- Performance logging

## Troubleshooting

### Issue: Logs not appearing

**Solution**: Check log level configuration
```python
# Ensure log level is appropriate
LOG_LEVEL=DEBUG  # Shows all logs
LOG_LEVEL=INFO   # Shows info and above
```

### Issue: PII not being filtered

**Solution**: Use sanitize_log_data explicitly
```python
from app.modules.common.logging import sanitize_log_data
safe_data = sanitize_log_data(sensitive_data)
logger.info("Data", extra={"data": safe_data})
```

### Issue: Missing correlation_id in logs

**Solution**: Ensure middleware is added
```python
# In main.py
app.add_middleware(CorrelationIDMiddleware)
```

### Issue: JSON format not working

**Solution**: Check environment setting
```python
# Use production environment for JSON
setup_logging(environment="production")
```

## Security Considerations

1. **Never log sensitive data** - passwords, tokens, API keys are automatically filtered
2. **Limit request/response body logging** in production
3. **Restrict log access** to authorized personnel only
4. **Enable log encryption** for compliance requirements
5. **Monitor audit logs** for security events
6. **Rotate and archive logs** regularly

## Compliance

The logging system supports compliance requirements for:

- **GDPR**: PII filtering and data access logging
- **SOC 2**: Audit trail and security event logging
- **HIPAA**: Access logging and data modification tracking
- **PCI DSS**: Security event monitoring and log retention

## Future Enhancements

- [ ] Log shipping to external services (AWS CloudWatch, DataDog)
- [ ] Real-time log analysis and alerting
- [ ] Log aggregation across multiple instances
- [ ] Custom metric extraction from logs
- [ ] Integration with distributed tracing (OpenTelemetry)

## Support

For questions or issues with the logging system:

1. Check this documentation
2. Review the code examples
3. Run the test suite
4. Contact the development team

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
**Maintainer**: Qlib-UI Development Team
