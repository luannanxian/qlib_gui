# Logging System - Practical Examples

This document provides practical, real-world examples of using the logging system in the Qlib-UI backend.

## Table of Contents

1. [API Endpoint Logging](#api-endpoint-logging)
2. [Service Layer Logging](#service-layer-logging)
3. [Database Operations](#database-operations)
4. [Error Handling](#error-handling)
5. [Security Events](#security-events)
6. [Performance Monitoring](#performance-monitoring)
7. [Background Tasks](#background-tasks)
8. [Testing with Logs](#testing-with-logs)

---

## API Endpoint Logging

### Example 1: Basic REST API Endpoint

```python
from fastapi import APIRouter, HTTPException, Request
from app.modules.common.logging import get_logger
from app.modules.common.logging.context import get_correlation_id

router = APIRouter()
logger = get_logger(__name__)

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, request: Request):
    """Get dataset by ID with logging"""

    logger.info(
        "Fetching dataset",
        extra={
            "dataset_id": dataset_id,
            "correlation_id": get_correlation_id(),
            "client_ip": request.client.host
        }
    )

    try:
        dataset = await dataset_service.get_by_id(dataset_id)

        if not dataset:
            logger.warning(
                "Dataset not found",
                extra={"dataset_id": dataset_id}
            )
            raise HTTPException(status_code=404, detail="Dataset not found")

        logger.info(
            "Dataset retrieved successfully",
            extra={
                "dataset_id": dataset_id,
                "dataset_name": dataset.name
            }
        )

        return dataset

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to retrieve dataset",
            extra={
                "dataset_id": dataset_id,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Example 2: POST Endpoint with Audit Logging

```python
from fastapi import APIRouter, Depends
from app.modules.common.logging import get_logger
from app.modules.common.logging.audit import AuditLogger, AuditEventType
from app.modules.common.schemas import DatasetCreate

router = APIRouter()
logger = get_logger(__name__)

@router.post("/datasets")
async def create_dataset(
    dataset: DatasetCreate,
    current_user = Depends(get_current_user)
):
    """Create new dataset with audit logging"""

    logger.info(
        "Creating dataset",
        extra={
            "user_id": current_user.id,
            "dataset_name": dataset.name
        }
    )

    try:
        # Create dataset
        new_dataset = await dataset_service.create(dataset, current_user.id)

        # Log audit event
        AuditLogger.log_data_access(
            event_type=AuditEventType.DATA_CREATED,
            user_id=current_user.id,
            resource_type="dataset",
            resource_id=str(new_dataset.id),
            action="create",
            details={
                "dataset_name": dataset.name,
                "dataset_type": dataset.type
            }
        )

        logger.info(
            "Dataset created successfully",
            extra={
                "dataset_id": str(new_dataset.id),
                "user_id": current_user.id
            }
        )

        return new_dataset

    except Exception as e:
        logger.error(
            "Failed to create dataset",
            extra={
                "user_id": current_user.id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise
```

### Example 3: Bulk Operation

```python
from app.modules.common.logging.decorators import LogExecutionContext

@router.post("/datasets/bulk-import")
async def bulk_import_datasets(
    datasets: list[DatasetCreate],
    current_user = Depends(get_current_user)
):
    """Bulk import datasets with context logging"""

    with LogExecutionContext(
        "bulk_dataset_import",
        level="INFO",
        user_id=current_user.id,
        count=len(datasets)
    ):
        results = []
        failed = []

        for idx, dataset_data in enumerate(datasets):
            try:
                dataset = await dataset_service.create(dataset_data, current_user.id)
                results.append(dataset)

                # Log every 10 datasets
                if (idx + 1) % 10 == 0:
                    logger.info(
                        f"Imported {idx + 1}/{len(datasets)} datasets",
                        extra={"progress": (idx + 1) / len(datasets) * 100}
                    )

            except Exception as e:
                logger.warning(
                    "Failed to import dataset",
                    extra={
                        "index": idx,
                        "dataset_name": dataset_data.name,
                        "error": str(e)
                    }
                )
                failed.append({"index": idx, "error": str(e)})

        logger.info(
            "Bulk import completed",
            extra={
                "total": len(datasets),
                "successful": len(results),
                "failed": len(failed)
            }
        )

        return {
            "successful": len(results),
            "failed": len(failed),
            "failed_items": failed
        }
```

---

## Service Layer Logging

### Example 4: Service with Decorators

```python
from app.modules.common.logging import get_logger
from app.modules.common.logging.decorators import log_async_execution, log_error

logger = get_logger(__name__)

class DatasetService:
    """Dataset service with comprehensive logging"""

    @log_async_execution(level="INFO", log_args=True, log_time=True)
    async def create_dataset(self, data: DatasetCreate, user_id: str):
        """Create new dataset - automatically logged"""

        # Validate
        await self._validate_dataset(data)

        # Create in database
        dataset = await self.repository.create(data, user_id)

        logger.info(
            "Dataset created in database",
            extra={
                "dataset_id": str(dataset.id),
                "user_id": user_id
            }
        )

        # Initialize storage
        await self._initialize_storage(dataset.id)

        return dataset

    @log_async_execution(level="DEBUG", log_time=True)
    async def _validate_dataset(self, data: DatasetCreate):
        """Validate dataset data"""
        # Validation logic
        pass

    @log_error(reraise=True)
    async def _initialize_storage(self, dataset_id: str):
        """Initialize storage - errors automatically logged"""
        # Storage initialization
        pass

    async def get_by_id(self, dataset_id: str):
        """Get dataset by ID"""

        logger.debug(
            "Retrieving dataset from repository",
            extra={"dataset_id": dataset_id}
        )

        dataset = await self.repository.get(dataset_id)

        if dataset:
            logger.debug(
                "Dataset found",
                extra={
                    "dataset_id": dataset_id,
                    "name": dataset.name
                }
            )
        else:
            logger.warning(
                "Dataset not found",
                extra={"dataset_id": dataset_id}
            )

        return dataset

    async def delete_dataset(self, dataset_id: str, user_id: str):
        """Delete dataset with audit logging"""

        logger.info(
            "Deleting dataset",
            extra={
                "dataset_id": dataset_id,
                "user_id": user_id
            }
        )

        # Get dataset info before deletion
        dataset = await self.get_by_id(dataset_id)

        if not dataset:
            raise ValueError("Dataset not found")

        # Delete from database
        await self.repository.delete(dataset_id)

        # Delete from storage
        await self._cleanup_storage(dataset_id)

        # Audit log
        AuditLogger.log_data_access(
            event_type=AuditEventType.DATA_DELETED,
            user_id=user_id,
            resource_type="dataset",
            resource_id=dataset_id,
            action="delete",
            details={"dataset_name": dataset.name}
        )

        logger.info(
            "Dataset deleted successfully",
            extra={
                "dataset_id": dataset_id,
                "user_id": user_id
            }
        )
```

---

## Database Operations

### Example 5: Repository with Query Logging

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.common.logging import get_logger
from app.modules.common.logging.decorators import log_async_execution

logger = get_logger(__name__)

class DatasetRepository:
    """Dataset repository with query logging"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @log_async_execution(level="DEBUG", log_time=True)
    async def create(self, data: DatasetCreate, user_id: str):
        """Create dataset in database"""

        dataset = Dataset(
            name=data.name,
            description=data.description,
            created_by=user_id
        )

        self.session.add(dataset)
        await self.session.commit()
        await self.session.refresh(dataset)

        return dataset

    async def find_by_user(self, user_id: str, limit: int = 100):
        """Find datasets by user with pagination"""

        logger.debug(
            "Querying datasets by user",
            extra={
                "user_id": user_id,
                "limit": limit
            }
        )

        from sqlalchemy import select

        stmt = (
            select(Dataset)
            .where(Dataset.created_by == user_id)
            .limit(limit)
            .order_by(Dataset.created_at.desc())
        )

        result = await self.session.execute(stmt)
        datasets = result.scalars().all()

        logger.debug(
            "Datasets query completed",
            extra={
                "user_id": user_id,
                "count": len(datasets)
            }
        )

        return datasets
```

### Example 6: Transaction with Logging

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.common.logging.decorators import LogExecutionContext

async def update_dataset_with_history(
    session: AsyncSession,
    dataset_id: str,
    updates: dict,
    user_id: str
):
    """Update dataset and create history record"""

    with LogExecutionContext(
        "update_dataset_transaction",
        dataset_id=dataset_id,
        user_id=user_id
    ):
        async with session.begin():
            # Update dataset
            dataset = await session.get(Dataset, dataset_id)

            if not dataset:
                raise ValueError("Dataset not found")

            # Store old values for history
            old_values = {
                "name": dataset.name,
                "description": dataset.description
            }

            # Apply updates
            for key, value in updates.items():
                setattr(dataset, key, value)

            # Create history record
            history = DatasetHistory(
                dataset_id=dataset_id,
                changed_by=user_id,
                old_values=old_values,
                new_values=updates
            )
            session.add(history)

            logger.info(
                "Dataset updated with history",
                extra={
                    "dataset_id": dataset_id,
                    "changes": list(updates.keys())
                }
            )
```

---

## Error Handling

### Example 7: Graceful Error Handling

```python
from app.modules.common.logging.decorators import log_error

class ExternalAPIService:
    """Service that calls external APIs"""

    @log_error(reraise=False, default_return=None)
    async def fetch_market_data(self, symbol: str):
        """
        Fetch market data from external API.
        Logs errors but doesn't crash - returns None on failure.
        """

        response = await http_client.get(f"/api/market/{symbol}")
        return response.json()

    async def get_enriched_data(self, symbol: str):
        """Get data with fallback"""

        # Try external API
        market_data = await self.fetch_market_data(symbol)

        if market_data is None:
            logger.warning(
                "External API unavailable, using cached data",
                extra={"symbol": symbol}
            )
            # Fallback to cache
            market_data = await cache.get(f"market:{symbol}")

        return market_data
```

### Example 8: Error with Context

```python
async def process_dataset_upload(file_path: str, user_id: str):
    """Process uploaded dataset file"""

    try:
        # Read file
        logger.info(
            "Reading uploaded file",
            extra={"file_path": file_path}
        )
        data = await read_file(file_path)

        # Validate
        logger.debug("Validating data structure")
        validate_data_structure(data)

        # Process
        logger.info(
            "Processing dataset",
            extra={"rows": len(data)}
        )
        result = await process_data(data)

        return result

    except FileNotFoundError:
        logger.error(
            "Uploaded file not found",
            extra={
                "file_path": file_path,
                "user_id": user_id
            }
        )
        raise

    except ValidationError as e:
        logger.error(
            "Data validation failed",
            extra={
                "file_path": file_path,
                "validation_errors": e.errors(),
                "user_id": user_id
            }
        )
        raise

    except Exception as e:
        logger.exception(
            "Unexpected error processing dataset",
            extra={
                "file_path": file_path,
                "user_id": user_id,
                "error_type": type(e).__name__
            }
        )
        raise
```

---

## Security Events

### Example 9: Authentication Logging

```python
from fastapi import HTTPException
from app.modules.common.logging.audit import AuditLogger, AuditEventType

async def login_user(username: str, password: str, request: Request):
    """Login user with audit logging"""

    ip_address = request.client.host

    try:
        # Verify credentials
        user = await user_service.authenticate(username, password)

        if not user:
            # Failed login
            AuditLogger.log_authentication(
                event_type=AuditEventType.LOGIN_FAILED,
                username=username,
                ip_address=ip_address,
                success=False,
                reason="Invalid credentials"
            )

            logger.warning(
                "Login failed - invalid credentials",
                extra={
                    "username": username,
                    "ip_address": ip_address
                }
            )

            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Successful login
        token = create_access_token(user.id)

        AuditLogger.log_authentication(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=str(user.id),
            username=username,
            ip_address=ip_address,
            success=True
        )

        logger.info(
            "User logged in successfully",
            extra={
                "user_id": str(user.id),
                "username": username,
                "ip_address": ip_address
            }
        )

        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Login error",
            extra={
                "username": username,
                "ip_address": ip_address
            }
        )
        raise
```

### Example 10: Authorization Check

```python
from app.modules.common.logging.audit import AuditLogger, AuditEventType

async def check_dataset_access(
    user_id: str,
    dataset_id: str,
    required_permission: str
):
    """Check if user has access to dataset"""

    has_access = await permission_service.check_permission(
        user_id=user_id,
        resource_type="dataset",
        resource_id=dataset_id,
        permission=required_permission
    )

    if not has_access:
        # Log denied access
        AuditLogger.log_authorization(
            event_type=AuditEventType.ACCESS_DENIED,
            user_id=user_id,
            resource_type="dataset",
            resource_id=dataset_id,
            action=required_permission,
            granted=False,
            required_permission=required_permission
        )

        logger.warning(
            "Access denied",
            extra={
                "user_id": user_id,
                "dataset_id": dataset_id,
                "required_permission": required_permission
            }
        )

        raise PermissionError("Access denied")

    # Log granted access
    AuditLogger.log_authorization(
        event_type=AuditEventType.ACCESS_GRANTED,
        user_id=user_id,
        resource_type="dataset",
        resource_id=dataset_id,
        action=required_permission,
        granted=True
    )

    return True
```

---

## Performance Monitoring

### Example 11: Slow Operation Detection

```python
from app.modules.common.logging.decorators import log_slow_execution

@log_slow_execution(threshold_ms=500, level="WARNING")
async def generate_report(dataset_id: str):
    """
    Generate report - logs automatically if takes > 500ms
    """

    # Heavy computation
    data = await fetch_dataset_data(dataset_id)
    report = await compute_analytics(data)

    return report
```

### Example 12: Performance Metrics

```python
import time

async def process_batch_with_metrics(items: list):
    """Process batch with detailed performance metrics"""

    start_time = time.perf_counter()
    processed = 0
    errors = 0

    logger.info(
        "Starting batch processing",
        extra={"batch_size": len(items)}
    )

    for item in items:
        item_start = time.perf_counter()

        try:
            await process_item(item)
            processed += 1

            item_duration = (time.perf_counter() - item_start) * 1000

            # Log slow items
            if item_duration > 100:
                logger.warning(
                    "Slow item processing",
                    extra={
                        "item_id": item.id,
                        "duration_ms": round(item_duration, 2)
                    }
                )

        except Exception as e:
            errors += 1
            logger.error(
                "Item processing failed",
                extra={"item_id": item.id, "error": str(e)}
            )

    total_duration = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Batch processing completed",
        extra={
            "total_items": len(items),
            "processed": processed,
            "errors": errors,
            "total_duration_ms": round(total_duration, 2),
            "avg_duration_ms": round(total_duration / len(items), 2)
        }
    )

    return {"processed": processed, "errors": errors}
```

---

## Background Tasks

### Example 13: Celery Task

```python
from celery import shared_task
from app.modules.common.logging import get_logger
from app.modules.common.logging.context import set_correlation_id

logger = get_logger(__name__)

@shared_task(bind=True)
def process_dataset_task(self, dataset_id: str, correlation_id: str = None):
    """Background task with logging"""

    # Set correlation ID for tracing
    if correlation_id:
        set_correlation_id(correlation_id)

    logger.info(
        "Task started",
        extra={
            "task_id": self.request.id,
            "dataset_id": dataset_id
        }
    )

    try:
        # Process dataset
        result = process_dataset(dataset_id)

        logger.info(
            "Task completed successfully",
            extra={
                "task_id": self.request.id,
                "dataset_id": dataset_id,
                "result": result
            }
        )

        return result

    except Exception as e:
        logger.exception(
            "Task failed",
            extra={
                "task_id": self.request.id,
                "dataset_id": dataset_id
            }
        )
        raise
```

---

## Testing with Logs

### Example 14: Testing Log Output

```python
import pytest
from loguru import logger
import json

@pytest.fixture
def log_capture():
    """Fixture to capture log output"""
    logs = []

    def sink(message):
        record = message.record
        logs.append({
            "level": record["level"].name,
            "message": record["message"],
            "extra": record["extra"]
        })

    # Add test sink
    handler_id = logger.add(sink, format="{message}")

    yield logs

    # Remove test sink
    logger.remove(handler_id)


async def test_dataset_creation_logs(log_capture):
    """Test that dataset creation produces correct logs"""

    # Perform operation
    await create_dataset(DatasetCreate(name="Test Dataset"))

    # Verify logs
    assert len(log_capture) >= 2

    # Check first log
    assert log_capture[0]["level"] == "INFO"
    assert "Creating dataset" in log_capture[0]["message"]

    # Check last log
    assert log_capture[-1]["level"] == "INFO"
    assert "created successfully" in log_capture[-1]["message"]
    assert "dataset_id" in log_capture[-1]["extra"]
```

---

## Summary

These examples demonstrate:
- ✅ API endpoint logging patterns
- ✅ Service layer integration
- ✅ Database operation logging
- ✅ Error handling strategies
- ✅ Security event auditing
- ✅ Performance monitoring
- ✅ Background task logging
- ✅ Testing with logs

For more details, see [README.md](./README.md).
