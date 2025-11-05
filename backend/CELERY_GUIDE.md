# Celery Task Queue Guide

This document explains how to use Celery for asynchronous task processing in the qlib-ui backend.

## Overview

Celery is configured with Redis as the message broker and result backend for handling long-running tasks asynchronously, such as:
- Data import and processing
- Backtesting operations
- Strategy execution
- Report generation
- Data cleanup

## Architecture

```
FastAPI Application → Celery Task → Redis Broker → Celery Worker → Database
                                                  ↓
                                           Redis Result Backend
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Task Queues

The system uses multiple queues for different types of tasks:

- `data_import`: Data import and processing tasks
- `backtest`: Backtesting tasks
- `strategy`: Strategy execution tasks
- `default`: General purpose tasks

## Starting Celery

### 1. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using local Redis
redis-server
```

### 2. Start Celery Worker

```bash
# Using the startup script
./start_celery_worker.sh

# Or manually
celery -A app.celery_app worker --loglevel=info --queues=data_import,backtest,strategy
```

### 3. Start Celery Beat (Optional - for periodic tasks)

```bash
# Using the startup script
./start_celery_beat.sh

# Or manually
celery -A app.celery_app beat --loglevel=info
```

## Using Tasks

### 1. Data Import Task

```python
from app.modules.data_management.tasks.import_tasks import process_data_import

# Queue a data import task
task = process_data_import.delay(
    task_id="uuid-here",
    file_path="/path/to/file.csv",
    import_type="csv",
    import_config={
        "delimiter": ",",
        "encoding": "utf-8",
    }
)

# Get task ID
task_id = task.id

# Check task status
result = task.get(timeout=10)  # Wait up to 10 seconds
```

### 2. From API Endpoint

```python
from fastapi import APIRouter
from app.modules.data_management.tasks.import_tasks import process_data_import

router = APIRouter()

@router.post("/import")
async def trigger_import(task_id: str, file_path: str):
    # Queue the task
    celery_task = process_data_import.delay(
        task_id=task_id,
        file_path=file_path,
        import_type="csv",
    )

    return {
        "task_id": task_id,
        "celery_task_id": celery_task.id,
        "status": "queued"
    }
```

### 3. File Validation Task

```python
from app.modules.data_management.tasks.import_tasks import validate_import_file

# Validate before processing
validation = validate_import_file.delay(
    task_id="uuid-here",
    file_path="/path/to/file.csv",
    import_type="csv"
)

result = validation.get()
if result["success"]:
    # File is valid, proceed with import
    process_data_import.delay(...)
```

## Monitoring Tasks

### 1. Check Task Status

```python
from celery.result import AsyncResult
from app.celery_app import celery_app

# Get task status
result = AsyncResult(task_id, app=celery_app)

print(f"Status: {result.state}")
print(f"Result: {result.result}")
print(f"Info: {result.info}")
```

### 2. Using Flower (Web-based monitoring)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A app.celery_app flower --port=5555

# Access at http://localhost:5555
```

### 3. Check Worker Status

```bash
# Inspect active workers
celery -A app.celery_app inspect active

# Check registered tasks
celery -A app.celery_app inspect registered

# Check worker stats
celery -A app.celery_app inspect stats
```

## Task States

Celery tasks go through these states:

1. **PENDING**: Task is waiting to be executed
2. **STARTED**: Task has been started by a worker
3. **RETRY**: Task is being retried after failure
4. **SUCCESS**: Task completed successfully
5. **FAILURE**: Task failed and won't be retried

## Error Handling

### Automatic Retries

Tasks are configured to retry automatically on certain errors:

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
)
def my_task(self):
    try:
        # Task logic
        pass
    except DatabaseError as e:
        # Retry on database errors
        raise self.retry(exc=e, countdown=60)
```

### Manual Error Handling

```python
from celery.result import AsyncResult

result = AsyncResult(task_id)

if result.state == 'FAILURE':
    error = result.info  # Exception instance
    print(f"Task failed: {error}")
```

## Best Practices

### 1. Keep Tasks Idempotent

Tasks should produce the same result when called multiple times:

```python
@celery_app.task
def update_dataset(dataset_id: str, data: dict):
    # Use upsert operations
    dataset = get_or_create_dataset(dataset_id)
    dataset.update(data)
    dataset.save()
```

### 2. Use Task IDs Wisely

Store Celery task IDs in your database for tracking:

```python
import_task = ImportTask(
    id=uuid4(),
    celery_task_id=None,  # Set when task is queued
    status=ImportStatus.PENDING
)

# Queue task
celery_task = process_data_import.delay(...)

# Update with Celery task ID
import_task.celery_task_id = celery_task.id
import_task.save()
```

### 3. Handle Long-Running Tasks

Use soft and hard time limits:

```python
@celery_app.task(
    time_limit=3600,      # Hard limit: 1 hour
    soft_time_limit=3300, # Soft limit: 55 minutes
)
def long_running_task():
    try:
        # Task logic
        pass
    except SoftTimeLimitExceeded:
        # Cleanup before hard limit
        cleanup()
        raise
```

### 4. Implement Progress Tracking

Update task progress in the database:

```python
@celery_app.task(bind=True)
def process_large_file(self, task_id: str):
    total = 1000
    for i in range(total):
        # Process item
        process_item(i)

        # Update progress
        update_task_progress(
            task_id=task_id,
            current=i + 1,
            total=total
        )

        # Update Celery state
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total}
        )
```

### 5. Clean Up Resources

Always close database connections and file handles:

```python
@celery_app.task
def process_file(file_path: str):
    session = None
    file_handle = None

    try:
        session = get_db_session()
        file_handle = open(file_path, 'r')

        # Process file
        process_data(file_handle, session)

    finally:
        if file_handle:
            file_handle.close()
        if session:
            session.close()
```

## Periodic Tasks

Configure periodic tasks in Celery Beat:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-imports': {
        'task': 'app.modules.data_management.tasks.cleanup_old_imports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (30,)  # Delete tasks older than 30 days
    },
}
```

## Production Deployment

### 1. Use Multiple Workers

```bash
# Start multiple workers for different queues
celery -A app.celery_app worker -Q data_import -c 4 --hostname=import@%h &
celery -A app.celery_app worker -Q backtest -c 2 --hostname=backtest@%h &
celery -A app.celery_app worker -Q strategy -c 2 --hostname=strategy@%h &
```

### 2. Use Supervisor for Process Management

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A app.celery_app worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A app.celery_app beat --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/beat.err.log
stdout_logfile=/var/log/celery/beat.out.log
```

### 3. Use systemd Services

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/celery -A app.celery_app worker --detach
ExecStop=/path/to/venv/bin/celery -A app.celery_app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Worker Not Picking Up Tasks

```bash
# Check if worker is running
celery -A app.celery_app inspect active

# Check if tasks are registered
celery -A app.celery_app inspect registered

# Check queue length
redis-cli LLEN celery

# Purge all tasks (DANGER!)
celery -A app.celery_app purge
```

### Memory Leaks

```bash
# Restart workers after N tasks
celery -A app.celery_app worker --max-tasks-per-child=1000
```

### Dead Tasks

```bash
# Revoke a task
celery -A app.celery_app control revoke <task-id> --terminate

# Revoke all tasks in queue
celery -A app.celery_app purge
```

### Redis Connection Issues

```bash
# Check Redis connection
redis-cli ping

# Check Redis memory
redis-cli info memory

# Monitor Redis commands
redis-cli monitor
```

## Testing Tasks

### Unit Testing Tasks

```python
import pytest
from app.modules.data_management.tasks.import_tasks import process_data_import

@pytest.mark.asyncio
async def test_process_data_import():
    # Run task synchronously for testing
    result = process_data_import(
        task_id="test-task",
        file_path="/path/to/test.csv",
        import_type="csv"
    )

    assert result["success"] is True
    assert result["rows_processed"] > 0
```

### Integration Testing

```python
import pytest
from celery.result import AsyncResult

@pytest.mark.asyncio
async def test_async_import():
    # Queue task
    task = process_data_import.delay(
        task_id="test-task",
        file_path="/path/to/test.csv",
        import_type="csv"
    )

    # Wait for completion
    result = task.get(timeout=30)

    assert result["success"] is True
```

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## Current Task Implementations

### Data Management Tasks

1. **process_data_import**: Main task for processing CSV/Excel imports
2. **validate_import_file**: Validate file before import
3. **cleanup_old_imports**: Periodic cleanup of old import tasks

### Backtest Tasks (TODO)

Tasks for backtesting will be implemented when the backtest module is ready.

### Strategy Tasks (TODO)

Tasks for strategy execution will be implemented when the strategy module is ready.
