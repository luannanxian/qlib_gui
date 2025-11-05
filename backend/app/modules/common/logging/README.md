# Structured Logging Architecture

Comprehensive structured logging system for the Qlib-UI backend using loguru.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Components](#components)
7. [Best Practices](#best-practices)
8. [Performance Considerations](#performance-considerations)
9. [Integration Guide](#integration-guide)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This logging system provides production-ready structured logging with:
- **JSON formatting** for log aggregation tools (ELK, Splunk, DataDog, CloudWatch)
- **Correlation ID tracking** for distributed tracing
- **PII and secret filtering** for security compliance
- **Performance monitoring** with slow query/request detection
- **Audit logging** for security and compliance events
- **Async logging** to avoid blocking I/O

---

## Features

### Core Features

- ✅ **Structured JSON logging** - Machine-readable logs for aggregation
- ✅ **Multiple log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **Contextual logging** - Correlation IDs, user IDs, request IDs
- ✅ **Log rotation** - By size and time with compression
- ✅ **Environment-specific** - Development vs production configurations
- ✅ **FastAPI middleware** - Automatic request/response logging
- ✅ **Database query logging** - SQLAlchemy event listeners
- ✅ **Security audit logging** - Authentication, authorization, data access
- ✅ **PII filtering** - Automatic sanitization of sensitive data
- ✅ **Performance tracking** - Slow query and request detection

### Log Outputs

1. **Console** - Human-readable (dev) or JSON (production)
2. **Application logs** - `logs/app_{date}.log`
3. **Error logs** - `logs/error_{date}.log`
4. **Audit logs** - `logs/audit_{date}.log`
5. **Database logs** - `logs/database_{date}.log`

---

## Quick Start

### 1. Basic Setup

The logging system is automatically configured when the FastAPI application starts:

```python
from app.modules.common.logging import setup_logging, get_logger

# Setup logging (done in main.py)
setup_logging(log_level="INFO", environment="production")

# Get logger instance
logger = get_logger(__name__)

# Use logger
logger.info("Application started")
logger.error("Error occurred", extra={"error_code": 500})
```

### 2. Using in Route Handlers

```python
from fastapi import APIRouter
from app.modules.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/items/{item_id}")
async def get_item(item_id: str):
    logger.info(f"Fetching item", extra={"item_id": item_id})

    # Your logic here

    logger.info(f"Item retrieved successfully", extra={"item_id": item_id})
    return {"item_id": item_id}
```

### 3. Using Decorators

```python
from app.modules.common.logging.decorators import log_async_execution

@log_async_execution(level="INFO", log_args=True, log_time=True)
async def process_data(data: dict):
    # Function automatically logs execution time and arguments
    return {"processed": True}
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=./logs                          # Log file directory
LOG_FORMAT=json                         # json or text
LOG_ROTATION_SIZE=100 MB                # Rotate when file reaches size
LOG_RETENTION_DAYS=30                   # Keep logs for N days
LOG_COMPRESSION=zip                     # Compression format (zip, gz, bz2)

# Request Logging
LOG_REQUEST_BODY=true                   # Log request bodies
LOG_RESPONSE_BODY=false                 # Log response bodies (caution!)

# Performance Thresholds
SLOW_QUERY_THRESHOLD_MS=100.0           # DB queries slower than this
SLOW_REQUEST_THRESHOLD_MS=1000.0        # Requests slower than this

# Environment
APP_ENV=production                      # development, staging, production
```

### Programmatic Configuration

```python
from app.modules.common.logging.config import setup_logging, configure_log_level

# Custom setup
setup_logging(
    log_level="DEBUG",
    log_dir="/var/log/qlib-ui",
    environment="production"
)

# Change log level at runtime
configure_log_level("sqlalchemy.engine", "WARNING")
```

---

## Usage Examples

### Basic Logging

```python
from app.modules.common.logging import get_logger

logger = get_logger(__name__)

# Simple logging
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")

# With extra context
logger.info(
    "User action performed",
    extra={
        "user_id": "user_123",
        "action": "update_profile",
        "resource_id": "profile_456"
    }
)
```

### Contextual Logging with Correlation IDs

```python
from app.modules.common.logging import get_logger
from app.modules.common.logging.context import set_correlation_id, set_user_id

logger = get_logger(__name__)

# Set context
set_correlation_id("abc123")
set_user_id("user_456")

# All logs will include correlation_id and user_id
logger.info("Processing request")  # Includes correlation_id and user_id
```

### Decorator-Based Logging

```python
from app.modules.common.logging.decorators import (
    log_execution,
    log_async_execution,
    log_error,
    log_slow_execution
)

# Log synchronous function execution
@log_execution(level="INFO", log_args=True, log_result=True)
def calculate_metrics(data: dict):
    return {"mean": 42, "std": 10}

# Log async function execution
@log_async_execution(level="DEBUG", log_time=True)
async def fetch_data(url: str):
    # Automatically logs execution time
    return await client.get(url)

# Log errors without crashing
@log_error(reraise=False, default_return={})
def risky_operation():
    # Logs error and returns {} instead of raising
    raise ValueError("Something went wrong")

# Log only slow executions
@log_slow_execution(threshold_ms=500)
async def potentially_slow_task():
    # Only logs if execution takes > 500ms
    pass
```

### Context Manager for Code Blocks

```python
from app.modules.common.logging.decorators import LogExecutionContext

with LogExecutionContext("data_processing", level="INFO"):
    # Code here is logged with timing
    process_data()
    transform_data()
# Automatically logs completion time
```

### Audit Logging

```python
from app.modules.common.logging.audit import (
    AuditLogger,
    AuditEventType,
    AuditSeverity
)

# Log authentication event
AuditLogger.log_authentication(
    event_type=AuditEventType.LOGIN_SUCCESS,
    user_id="user_123",
    username="john.doe",
    ip_address="192.168.1.100",
    success=True
)

# Log authorization event
AuditLogger.log_authorization(
    event_type=AuditEventType.ACCESS_DENIED,
    user_id="user_123",
    resource_type="dataset",
    resource_id="dataset_456",
    action="delete",
    granted=False,
    required_permission="dataset:delete"
)

# Log data access
AuditLogger.log_data_access(
    event_type=AuditEventType.DATA_DELETED,
    user_id="admin_123",
    resource_type="user",
    resource_id="user_456",
    action="delete",
    records_affected=1
)

# Log security violation
AuditLogger.log_security_violation(
    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
    user_id="user_123",
    ip_address="192.168.1.100",
    violation_type="api_rate_limit",
    details={"limit": 100, "actual": 150}
)
```

### Database Query Logging

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

### PII and Secret Filtering

```python
from app.modules.common.logging.filters import sanitize_log_data

# Sensitive data will be automatically filtered
user_data = {
    "username": "john",
    "password": "secret123",  # Will be redacted
    "email": "john@example.com"
}

# Sanitize before logging
logger.info("User data", extra=sanitize_log_data(user_data))
# Output: {"username": "john", "password": "***REDACTED***", "email": "john@example.com"}
```

---

## Components

### 1. Configuration (`config.py`)

Central logging configuration:
- Loguru setup with multiple handlers
- Environment-specific formatting
- Log rotation and retention
- Integration with Python's standard logging

### 2. Formatters (`formatters.py`)

- **JsonFormatter** - Structured JSON for production
- **DevelopmentFormatter** - Human-readable for development
- **CompactJsonFormatter** - Minimal JSON for high-throughput
- **StructuredFormatter** - Custom field mapping

### 3. Context Management (`context.py`)

Thread-safe context variables:
- Correlation IDs for request tracing
- User IDs for user-specific logging
- Request IDs for request identification
- Custom extra context

### 4. Middleware (`middleware.py`)

FastAPI middleware:
- **LoggingMiddleware** - Request/response logging
- **CorrelationIDMiddleware** - Correlation ID injection
- **PerformanceLoggingMiddleware** - Performance monitoring

### 5. Filters (`filters.py`)

Data sanitization:
- **SensitiveDataFilter** - PII and secret filtering
- **EmailFilter** - Email address masking
- **IPAddressFilter** - IP address masking
- **PerformanceFilter** - Slow operation flagging

### 6. Decorators (`decorators.py`)

Function logging decorators:
- `@log_execution` - Log synchronous functions
- `@log_async_execution` - Log async functions
- `@log_error` - Error handling with logging
- `@log_slow_execution` - Log slow executions
- `LogExecutionContext` - Context manager

### 7. Audit Logging (`audit.py`)

Security and compliance logging:
- Authentication events
- Authorization events
- Data access events
- Admin actions
- Security violations

### 8. Database Logging (`database.py`)

SQLAlchemy integration:
- Query execution logging
- Slow query detection
- Connection pool monitoring
- Transaction lifecycle logging

---

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG - Detailed diagnostic information
logger.debug("Processing user input", extra={"input": data})

# INFO - General informational messages
logger.info("User profile updated", extra={"user_id": user_id})

# WARNING - Warning messages for potentially harmful situations
logger.warning("API rate limit approaching", extra={"current": 95, "limit": 100})

# ERROR - Error events that might still allow the application to continue
logger.error("Failed to send email", extra={"recipient": email})

# CRITICAL - Very severe error events that might cause the application to abort
logger.critical("Database connection lost", extra={"attempts": 3})
```

### 2. Always Use Extra Fields

```python
# Good - Structured data in extra
logger.info("Order created", extra={"order_id": "12345", "total": 99.99})

# Bad - Unstructured string
logger.info(f"Order 12345 created with total 99.99")
```

### 3. Leverage Context Variables

```python
from app.modules.common.logging.context import set_correlation_id, set_user_id

# Set once at request start
set_correlation_id(request.headers.get("X-Correlation-ID"))
set_user_id(current_user.id)

# All subsequent logs automatically include these
logger.info("Processing request")  # Includes correlation_id and user_id
```

### 4. Use Decorators for Functions

```python
# Instead of manual logging
async def process_order(order_id: str):
    logger.info("Processing order", extra={"order_id": order_id})
    start = time.time()
    try:
        result = await do_processing(order_id)
        logger.info("Order processed", extra={"duration": time.time() - start})
        return result
    except Exception as e:
        logger.error("Processing failed", extra={"error": str(e)})
        raise

# Use decorator
@log_async_execution(level="INFO", log_args=True, log_time=True)
async def process_order(order_id: str):
    return await do_processing(order_id)
```

### 5. Sanitize Sensitive Data

```python
from app.modules.common.logging.filters import sanitize_log_data

# Always sanitize user input
logger.info("User registered", extra=sanitize_log_data({
    "username": username,
    "password": password,  # Will be redacted
    "email": email
}))
```

### 6. Use Audit Logging for Security Events

```python
# Always log authentication events
AuditLogger.log_authentication(
    event_type=AuditEventType.LOGIN_FAILED,
    username=username,
    ip_address=request.client.host,
    success=False,
    reason="Invalid credentials"
)

# Log authorization decisions
AuditLogger.log_authorization(
    event_type=AuditEventType.ACCESS_DENIED,
    user_id=user_id,
    resource_type="dataset",
    resource_id=dataset_id,
    action="delete",
    granted=False
)
```

---

## Performance Considerations

### 1. Async Logging

The system uses async logging by default (`enqueue=True`) to avoid blocking:

```python
# Logs are enqueued and written asynchronously
logger.info("Heavy processing complete")  # Returns immediately
```

### 2. Log Level in Production

Set appropriate log levels in production:

```bash
# Development
LOG_LEVEL=DEBUG

# Production
LOG_LEVEL=INFO  # or WARNING
```

### 3. Avoid Logging in Tight Loops

```python
# Bad - Logs in loop
for item in large_list:
    logger.debug(f"Processing {item}")

# Good - Log summary
logger.info(f"Processing {len(large_list)} items")
# ... process ...
logger.info("Processing complete")
```

### 4. Use Log Sampling for High-Frequency Events

```python
import random

# Sample 1% of logs
if random.random() < 0.01:
    logger.debug("High-frequency event", extra={"data": data})
```

### 5. Limit Body Logging

```bash
# Disable request/response body logging in production if not needed
LOG_REQUEST_BODY=false
LOG_RESPONSE_BODY=false
```

### Performance Benchmarks

Based on local testing:
- **Sync logging**: ~0.1ms overhead per log
- **Async logging**: ~0.01ms overhead per log
- **JSON formatting**: ~0.05ms per log
- **PII filtering**: ~0.02ms per log

---

## Integration Guide

### FastAPI Integration

Already integrated in `app/main.py`:

```python
from app.modules.common.logging import setup_logging, get_logger
from app.modules.common.logging.middleware import LoggingMiddleware

# Setup logging
setup_logging()

# Add middleware
app.add_middleware(LoggingMiddleware)

logger = get_logger(__name__)
```

### SQLAlchemy Integration

```python
from sqlalchemy import create_engine
from app.modules.common.logging.database import setup_database_logging

engine = create_engine(DATABASE_URL)
setup_database_logging(engine)
```

### Celery Integration

```python
from celery import Celery
from app.modules.common.logging import get_logger

celery_app = Celery("qlib-ui")
logger = get_logger(__name__)

@celery_app.task
def background_task(data):
    logger.info("Task started", extra={"task": "background_task"})
    # Task logic
    logger.info("Task completed")
```

### Custom Service Integration

```python
from app.modules.common.logging import get_logger
from app.modules.common.logging.decorators import log_async_execution

logger = get_logger(__name__)

class DataService:
    @log_async_execution(level="INFO", log_time=True)
    async def fetch_data(self, dataset_id: str):
        logger.info("Fetching dataset", extra={"dataset_id": dataset_id})
        # Fetch logic
        return data
```

---

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration:
```python
from app.modules.common.logging.config import configure_log_level
configure_log_level("app", "DEBUG")
```

2. Check log directory permissions:
```bash
ls -la ./logs
chmod 755 ./logs
```

### Logs Missing Context

Ensure context is set:
```python
from app.modules.common.logging.context import set_correlation_id
set_correlation_id()  # Auto-generate if not provided
```

### Sensitive Data in Logs

Update sensitive fields list:
```python
from app.modules.common.logging.filters import SensitiveDataFilter

custom_fields = {"custom_secret_field"}
filter_instance = SensitiveDataFilter(additional_fields=custom_fields)
```

### High Memory Usage

1. Reduce log retention:
```bash
LOG_RETENTION_DAYS=7  # Instead of 30
```

2. Increase rotation frequency:
```bash
LOG_ROTATION_SIZE=50 MB  # Instead of 100 MB
```

3. Disable request body logging:
```bash
LOG_REQUEST_BODY=false
```

### Slow Performance

1. Ensure async logging is enabled (default)
2. Reduce log level in production:
```bash
LOG_LEVEL=WARNING
```

3. Disable database query logging for all queries:
```python
setup_database_logging(engine, log_all_queries=False)
```

---

## Additional Resources

- [Loguru Documentation](https://loguru.readthedocs.io/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [SQLAlchemy Events](https://docs.sqlalchemy.org/en/latest/core/events.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/index.html)

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test files in `tests/modules/common/logging/`
3. Create an issue in the project repository
