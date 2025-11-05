# Logging System - Quick Start Guide

Get started with the structured logging system in 5 minutes.

## Installation

The logging system is already installed and integrated. No additional setup required!

**Dependencies** (already in `requirements.txt`):
- `loguru==0.7.2`
- `structlog==23.2.0` (optional, for reference)

## Step 1: Basic Usage

```python
from app.modules.common.logging import get_logger

# Get logger instance
logger = get_logger(__name__)

# Log messages
logger.debug("Debug information")
logger.info("Application started")
logger.warning("Something might be wrong")
logger.error("An error occurred")
logger.critical("Critical failure")
```

## Step 2: Add Context to Logs

```python
from app.modules.common.logging import get_logger

logger = get_logger(__name__)

# Log with extra fields
logger.info(
    "User created account",
    extra={
        "user_id": "user_123",
        "email": "user@example.com",
        "plan": "premium"
    }
)

# Output (JSON format):
# {
#   "timestamp": "2025-01-15T10:30:45.123456",
#   "level": "INFO",
#   "message": "User created account",
#   "extra": {
#     "user_id": "user_123",
#     "email": "user@example.com",
#     "plan": "premium"
#   }
# }
```

## Step 3: Use Decorators (Recommended)

```python
from app.modules.common.logging.decorators import log_async_execution

@log_async_execution(level="INFO", log_args=True, log_time=True)
async def fetch_dataset(dataset_id: str):
    """
    This function automatically logs:
    - Entry with arguments
    - Execution time
    - Completion or errors
    """
    dataset = await repository.get(dataset_id)
    return dataset

# Calling this function produces:
# INFO: Executing async fetch_dataset (arguments: {"dataset_id": "abc123"})
# INFO: Completed async fetch_dataset in 45.23ms
```

## Step 4: Add Correlation IDs

```python
from fastapi import Request
from app.modules.common.logging import get_logger
from app.modules.common.logging.context import set_correlation_id

logger = get_logger(__name__)

@app.get("/items/{item_id}")
async def get_item(item_id: str, request: Request):
    # Set correlation ID (already done by middleware, but you can override)
    # set_correlation_id("custom-correlation-id")

    # All logs in this request will include the correlation_id
    logger.info("Fetching item", extra={"item_id": item_id})
    # ... your code ...
    logger.info("Item retrieved")

    return {"item_id": item_id}
```

## Step 5: Audit Important Events

```python
from app.modules.common.logging.audit import AuditLogger, AuditEventType

# Log authentication
AuditLogger.log_authentication(
    event_type=AuditEventType.LOGIN_SUCCESS,
    user_id="user_123",
    username="john.doe",
    ip_address=request.client.host,
    success=True
)

# Log data access
AuditLogger.log_data_access(
    event_type=AuditEventType.DATA_DELETED,
    user_id="admin_123",
    resource_type="dataset",
    resource_id="dataset_456",
    action="delete"
)
```

## Common Patterns

### Pattern 1: API Endpoint

```python
from fastapi import APIRouter, HTTPException
from app.modules.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    logger.info("Fetching dataset", extra={"dataset_id": dataset_id})

    try:
        dataset = await dataset_service.get_by_id(dataset_id)

        if not dataset:
            logger.warning("Dataset not found", extra={"dataset_id": dataset_id})
            raise HTTPException(status_code=404, detail="Not found")

        logger.info("Dataset retrieved", extra={"dataset_id": dataset_id})
        return dataset

    except Exception as e:
        logger.exception("Error fetching dataset", extra={"dataset_id": dataset_id})
        raise
```

### Pattern 2: Service Method

```python
from app.modules.common.logging import get_logger
from app.modules.common.logging.decorators import log_async_execution

logger = get_logger(__name__)

class DatasetService:
    @log_async_execution(level="INFO", log_time=True)
    async def create_dataset(self, data: DatasetCreate):
        """Create dataset - automatically logged"""
        dataset = await self.repository.create(data)
        logger.info("Dataset created", extra={"dataset_id": str(dataset.id)})
        return dataset
```

### Pattern 3: Error Handling

```python
from app.modules.common.logging.decorators import log_error

@log_error(reraise=False, default_return=None)
async def fetch_external_data(url: str):
    """
    Fetch data from external API.
    Logs errors but doesn't crash.
    """
    response = await http_client.get(url)
    return response.json()
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Basic Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs
APP_ENV=development

# Performance (optional)
SLOW_QUERY_THRESHOLD_MS=100.0
SLOW_REQUEST_THRESHOLD_MS=1000.0
```

### Development vs Production

**Development**:
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=text  # Human-readable
LOG_REQUEST_BODY=true
```

**Production**:
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json  # Machine-readable
LOG_REQUEST_BODY=false
LOG_RESPONSE_BODY=false
```

## Viewing Logs

### Console (Development)

When running the app, logs appear in the console with colors:

```
2025-01-15 10:30:45.123 | INFO     | app.api.dataset:get_dataset:25 - Fetching dataset | dataset_id=abc123
2025-01-15 10:30:45.456 | INFO     | app.api.dataset:get_dataset:35 - Dataset retrieved | dataset_id=abc123
```

### Log Files (Production)

Logs are written to:
- `logs/app_2025-01-15.log` - All logs
- `logs/error_2025-01-15.log` - Errors only
- `logs/audit_2025-01-15.log` - Audit events
- `logs/database_2025-01-15.log` - Database queries

**Example JSON log**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "app.api.dataset",
  "message": "Dataset retrieved",
  "module": "dataset",
  "function": "get_dataset",
  "line": 35,
  "correlation_id": "abc123def456",
  "extra": {
    "dataset_id": "dataset_789"
  }
}
```

## Testing

Run the logging tests:

```bash
# Run all tests
pytest tests/modules/common/logging/

# Run specific test file
pytest tests/modules/common/logging/test_context.py

# Run with verbose output
pytest tests/modules/common/logging/ -v
```

## Next Steps

1. **Read the full documentation**: `app/modules/common/logging/README.md`
2. **See practical examples**: `app/modules/common/logging/EXAMPLES.md`
3. **Review the architecture**: `/backend/LOGGING_ARCHITECTURE.md`
4. **Set up log aggregation**: Forward logs to ELK, Splunk, or DataDog
5. **Create dashboards**: Visualize logs for monitoring

## Common Pitfalls

### ❌ Don't: Format strings manually
```python
logger.info(f"User {user_id} logged in")  # Bad
```

### ✅ Do: Use extra fields
```python
logger.info("User logged in", extra={"user_id": user_id})  # Good
```

### ❌ Don't: Log sensitive data
```python
logger.info("User credentials", extra={"password": password})  # Bad
```

### ✅ Do: Sanitize data
```python
from app.modules.common.logging.filters import sanitize_log_data

logger.info("User data", extra=sanitize_log_data(user_data))  # Good
```

### ❌ Don't: Log in tight loops
```python
for item in large_list:
    logger.debug(f"Processing {item}")  # Bad - too many logs
```

### ✅ Do: Log summaries
```python
logger.info(f"Processing {len(large_list)} items")
# ... process ...
logger.info("Processing complete")  # Good
```

## Getting Help

- **Documentation**: Check `README.md` and `EXAMPLES.md`
- **Tests**: Review test files for usage examples
- **Issues**: Create an issue in the project repository

## Summary

You now know how to:
- ✅ Get a logger and log messages
- ✅ Add context with extra fields
- ✅ Use decorators for automatic logging
- ✅ Track requests with correlation IDs
- ✅ Log audit events for security
- ✅ Configure logging for dev/prod
- ✅ View logs in console and files

**Happy logging! 🎉**
