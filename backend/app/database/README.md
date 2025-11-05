# Qlib-UI Database Layer

Complete async SQLAlchemy-based database layer for the Qlib-UI backend application.

## Overview

This module provides a complete database abstraction layer with:

- **Async Support**: Full async/await support using SQLAlchemy 2.0+ and aiomysql
- **MySQL Compatible**: Optimized for MySQL with proper type handling
- **Repository Pattern**: Clean separation of data access logic
- **Soft Deletes**: Built-in soft delete support for all models
- **Audit Trail**: Automatic tracking of created_by and updated_by
- **Type Safety**: Comprehensive type hints throughout
- **FastAPI Integration**: Ready-to-use dependency injection

## Architecture

```
app/database/
├── __init__.py                  # Main exports
├── base.py                      # Base models and mixins
├── session.py                   # Session management
├── init_db.py                   # Database initialization script
├── models/                      # Data models
│   ├── __init__.py
│   ├── dataset.py              # Dataset model
│   ├── chart.py                # Chart configuration model
│   └── user_preferences.py     # User preferences model
└── repositories/                # Repository pattern
    ├── __init__.py
    ├── base.py                 # Generic base repository
    ├── dataset.py              # Dataset repository
    ├── chart.py                # Chart repository
    └── user_preferences.py     # User preferences repository
```

## Features

### Base Models

All models inherit from `BaseDBModel` which provides:

- **UUID Primary Key**: String-based UUID for compatibility
- **Timestamps**: `created_at`, `updated_at` with timezone support
- **Soft Delete**: `is_deleted`, `deleted_at` for soft deletion
- **Audit Trail**: `created_by`, `updated_by` for tracking changes

### Models

#### Dataset
Manages uploaded and imported data sources.

**Fields**:
- `name`: Dataset name
- `source`: Data source (local, qlib, thirdparty)
- `file_path`: File path or URI
- `status`: Validation status (valid, invalid, pending)
- `row_count`: Number of rows
- `columns`: JSON array of column names
- `metadata`: Additional metadata as JSON

**Relationships**:
- One-to-Many with ChartConfig

#### ChartConfig
Stores visualization configurations.

**Fields**:
- `name`: Chart name
- `chart_type`: Chart type (kline, line, bar, scatter, heatmap)
- `dataset_id`: Foreign key to Dataset
- `config`: JSON configuration object
- `description`: Optional description

**Relationships**:
- Many-to-One with Dataset

#### UserPreferences
Stores user-specific settings.

**Fields**:
- `user_id`: Unique user identifier
- `mode`: User mode (beginner, expert)
- `language`: Language code (en, zh, etc.)
- `theme`: Theme preference (light, dark)
- `show_tooltips`: Boolean tooltip preference
- `completed_guides`: JSON array of guide IDs
- `settings`: JSON object for custom settings

### Repositories

Each model has a corresponding repository with CRUD operations:

#### Base Repository Methods
- `create()`: Create new record
- `get()`: Get by ID
- `get_multi()`: Get multiple with pagination
- `update()`: Update by ID
- `delete()`: Delete (soft or hard)
- `count()`: Count records
- `exists()`: Check existence
- `bulk_create()`: Create multiple records
- `restore()`: Restore soft-deleted record

#### Dataset Repository
Additional methods:
- `get_by_name()`: Get by exact name
- `get_by_source()`: Filter by source
- `get_by_status()`: Filter by status
- `search_by_name()`: Search with partial match
- `get_with_filters()`: Combined filtering
- `get_statistics()`: Get statistics by source and status

#### Chart Repository
Additional methods:
- `get_by_dataset()`: Get charts for a dataset
- `get_by_type()`: Filter by chart type
- `get_by_dataset_and_type()`: Combined filter
- `count_by_dataset()`: Count charts per dataset
- `search_by_name()`: Search by name
- `duplicate_chart()`: Duplicate existing chart
- `get_statistics()`: Get statistics by type

#### UserPreferences Repository
Additional methods:
- `get_by_user_id()`: Get by user ID
- `get_or_create()`: Get existing or create new
- `update_mode()`: Update user mode
- `update_language()`: Update language
- `update_theme()`: Update theme
- `toggle_tooltips()`: Toggle tooltip preference
- `add_completed_guide()`: Mark guide as completed
- `remove_completed_guide()`: Unmark guide
- `has_completed_guide()`: Check completion
- `update_settings()`: Update custom settings
- `get_setting()`: Get specific setting

## Quick Start

### 1. Initialize Database

```bash
# Create all tables
python -m app.database.init_db init

# Reset database (drop and recreate)
python -m app.database.init_db reset
```

### 2. Basic Usage

```python
from app.database import db_manager, get_db
from app.database.repositories import DatasetRepository

# Initialize database
db_manager.init()

# Use in async context
async def example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        # Create
        dataset = await repo.create({
            "name": "My Dataset",
            "source": "local",
            "file_path": "/path/to/data.csv",
            "status": "valid",
            "row_count": 1000,
            "columns": ["col1", "col2"],
            "metadata": {}
        })

        # Read
        dataset = await repo.get(dataset.id)

        # Update
        await repo.update(dataset.id, {"status": "invalid"})

        # Delete
        await repo.delete(dataset.id)
```

### 3. FastAPI Integration

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.database.repositories import DatasetRepository

router = APIRouter()

@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    return await repo.get(dataset_id)
```

## Configuration

Database settings are configured in `app/config.py`:

```python
# MySQL Connection
DATABASE_URL = "mysql+aiomysql://user:pass@host:port/dbname"
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_RECYCLE = 3600
DATABASE_POOL_PRE_PING = True
```

## Testing

Run tests with pytest:

```bash
# Run all database tests
pytest tests/test_database/

# Run specific test file
pytest tests/test_database/test_repositories.py

# Run with coverage
pytest --cov=app.database tests/test_database/
```

## Best Practices

1. **Always use async/await** for all database operations
2. **Use dependency injection** in FastAPI routes
3. **Handle errors** with try/except blocks
4. **Use soft deletes** by default
5. **Pass user_id** for audit trail
6. **Use pagination** for large result sets
7. **Use transactions** for multiple operations
8. **Close sessions** properly with context managers

## Migration Strategy

For production deployments, use Alembic for database migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Performance Considerations

- **Connection Pooling**: Configured with pre-ping for reliability
- **Eager Loading**: Uses `selectin` for relationships
- **Indexes**: Optimized indexes on frequently queried columns
- **Pagination**: Always paginate large result sets
- **Query Optimization**: Use filters and specific queries

## Security

- **SQL Injection**: Protected by SQLAlchemy parameterization
- **Soft Deletes**: Data is never truly lost by default
- **Audit Trail**: All changes are tracked
- **Input Validation**: Use Pydantic schemas before database operations

## Troubleshooting

### Connection Issues

```python
# Test connection
python -c "
import asyncio
from app.database.session import db_manager
from sqlalchemy import select

async def test():
    db_manager.init()
    async with db_manager.session() as session:
        await session.execute(select(1))
        print('Connection OK')
    await db_manager.close()

asyncio.run(test())
"
```

### Common Errors

**Error**: `RuntimeError: Database engine not initialized`
**Solution**: Call `db_manager.init()` before using sessions

**Error**: `Connection timeout`
**Solution**: Check MySQL server is running and accessible

**Error**: `Charset issues`
**Solution**: Ensure `charset=utf8mb4` in DATABASE_URL

## Documentation

- [Usage Examples](./USAGE_EXAMPLES.md) - Comprehensive usage examples
- [API Reference](./API_REFERENCE.md) - Detailed API documentation (TODO)

## License

Part of the Qlib-UI project.
