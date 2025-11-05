# Database Layer Usage Examples

This document provides comprehensive examples for using the Qlib-UI database layer.

## Table of Contents

1. [Setup and Initialization](#setup-and-initialization)
2. [Session Management](#session-management)
3. [Dataset Operations](#dataset-operations)
4. [Chart Operations](#chart-operations)
5. [User Preferences Operations](#user-preferences-operations)
6. [Advanced Usage](#advanced-usage)

## Setup and Initialization

### Initialize Database

```python
import asyncio
from app.database.session import db_manager

async def initialize():
    # Initialize the database engine
    db_manager.init()

    # Create all tables (first time setup)
    await db_manager.create_all()

    # Close when done
    await db_manager.close()

# Run initialization
asyncio.run(initialize())
```

### Using CLI Tool

```bash
# Initialize database (create tables)
python -m app.database.init_db init

# Reset database (drop and recreate)
python -m app.database.init_db reset

# Drop all tables (WARNING: deletes all data)
python -m app.database.init_db drop
```

## Session Management

### Using Context Manager

```python
from app.database.session import db_manager

async def example():
    db_manager.init()

    async with db_manager.session() as session:
        # Your database operations here
        result = await session.execute(select(Dataset))
        datasets = result.scalars().all()
```

### Using FastAPI Dependency

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("/datasets")
async def list_datasets(db: AsyncSession = Depends(get_db)):
    # db session is automatically managed
    result = await db.execute(select(Dataset))
    return result.scalars().all()
```

## Dataset Operations

### Create Dataset

```python
from app.database.repositories import DatasetRepository
from app.database import get_db

async def create_dataset_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        dataset = await repo.create({
            "name": "Stock Data 2024",
            "source": "local",
            "file_path": "/data/stocks_2024.csv",
            "status": "valid",
            "row_count": 10000,
            "columns": ["date", "open", "high", "low", "close", "volume"],
            "metadata": {
                "description": "Historical stock data for 2024",
                "symbols": ["AAPL", "GOOGL", "MSFT"]
            }
        }, user_id="user-123")

        print(f"Created dataset: {dataset.id}")
```

### Get Dataset

```python
async def get_dataset_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        # Get by ID
        dataset = await repo.get("dataset-id-123")

        # Get by name
        dataset = await repo.get_by_name("Stock Data 2024")

        # Get by source
        datasets = await repo.get_by_source("local", limit=10)

        # Get by status
        valid_datasets = await repo.get_by_status("valid", limit=20)
```

### Search Datasets

```python
async def search_datasets_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        # Search by name (partial match)
        results = await repo.search_by_name("stock", limit=10)

        # Advanced filtering
        results = await repo.get_with_filters(
            source="local",
            status="valid",
            search_term="2024",
            skip=0,
            limit=20
        )
```

### Update Dataset

```python
async def update_dataset_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        updated = await repo.update(
            "dataset-id-123",
            {
                "status": "invalid",
                "row_count": 15000,
                "metadata": {"note": "Updated with new data"}
            },
            user_id="user-123"
        )
```

### Delete Dataset

```python
async def delete_dataset_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        # Soft delete (default)
        success = await repo.delete("dataset-id-123", soft=True)

        # Hard delete (permanent)
        success = await repo.delete("dataset-id-123", soft=False)

        # Restore soft-deleted dataset
        restored = await repo.restore("dataset-id-123")
```

### Dataset Statistics

```python
async def dataset_statistics_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        stats = await repo.get_statistics()
        # Returns:
        # {
        #     "total": 100,
        #     "by_source": {"local": 50, "qlib": 30, "thirdparty": 20},
        #     "by_status": {"valid": 80, "invalid": 10, "pending": 10}
        # }
```

## Chart Operations

### Create Chart

```python
from app.database.repositories import ChartRepository

async def create_chart_example():
    async with db_manager.session() as session:
        repo = ChartRepository(session)

        chart = await repo.create({
            "name": "Price Candlestick Chart",
            "chart_type": "kline",
            "dataset_id": "dataset-id-123",
            "config": {
                "x_axis": "date",
                "y_axis": ["open", "high", "low", "close"],
                "colors": {
                    "up": "#26a69a",
                    "down": "#ef5350"
                },
                "volume": True,
                "indicators": ["MA5", "MA10", "MA20"]
            },
            "description": "Candlestick chart with volume and moving averages"
        }, user_id="user-123")
```

### Get Charts

```python
async def get_charts_example():
    async with db_manager.session() as session:
        repo = ChartRepository(session)

        # Get by dataset
        charts = await repo.get_by_dataset("dataset-id-123")

        # Get by type
        kline_charts = await repo.get_by_type("kline", limit=10)

        # Get by dataset and type
        charts = await repo.get_by_dataset_and_type(
            "dataset-id-123",
            "kline"
        )
```

### Duplicate Chart

```python
async def duplicate_chart_example():
    async with db_manager.session() as session:
        repo = ChartRepository(session)

        duplicate = await repo.duplicate_chart(
            "chart-id-123",
            new_name="Copy of Price Chart",
            user_id="user-123"
        )
```

### Chart Statistics

```python
async def chart_statistics_example():
    async with db_manager.session() as session:
        repo = ChartRepository(session)

        stats = await repo.get_statistics()
        # Returns:
        # {
        #     "total": 50,
        #     "by_type": {
        #         "kline": 20,
        #         "line": 15,
        #         "bar": 10,
        #         "scatter": 3,
        #         "heatmap": 2
        #     }
        # }
```

## User Preferences Operations

### Get or Create Preferences

```python
from app.database.repositories import UserPreferencesRepository

async def get_or_create_prefs_example():
    async with db_manager.session() as session:
        repo = UserPreferencesRepository(session)

        # Get existing or create with defaults
        prefs, created = await repo.get_or_create(
            "user-123",
            defaults={
                "mode": "expert",
                "language": "zh",
                "theme": "dark"
            }
        )

        if created:
            print("Created new preferences")
        else:
            print("Retrieved existing preferences")
```

### Update User Preferences

```python
async def update_prefs_example():
    async with db_manager.session() as session:
        repo = UserPreferencesRepository(session)

        # Update mode
        await repo.update_mode("user-123", "expert")

        # Update language
        await repo.update_language("user-123", "zh")

        # Update theme
        await repo.update_theme("user-123", "dark")

        # Toggle tooltips
        await repo.toggle_tooltips("user-123")
```

### Manage Completed Guides

```python
async def manage_guides_example():
    async with db_manager.session() as session:
        repo = UserPreferencesRepository(session)

        # Add completed guide
        await repo.add_completed_guide("user-123", "intro-tour")
        await repo.add_completed_guide("user-123", "advanced-features")

        # Check if guide is completed
        completed = await repo.has_completed_guide("user-123", "intro-tour")

        # Remove completed guide
        await repo.remove_completed_guide("user-123", "intro-tour")
```

### Custom Settings

```python
async def custom_settings_example():
    async with db_manager.session() as session:
        repo = UserPreferencesRepository(session)

        # Update settings (merge with existing)
        await repo.update_settings(
            "user-123",
            {
                "chart_default_type": "kline",
                "auto_refresh": True,
                "refresh_interval": 30
            },
            merge=True
        )

        # Get specific setting
        chart_type = await repo.get_setting(
            "user-123",
            "chart_default_type",
            default="line"
        )
```

## Advanced Usage

### Transactions

```python
async def transaction_example():
    async with db_manager.session() as session:
        dataset_repo = DatasetRepository(session)
        chart_repo = ChartRepository(session)

        try:
            # Create dataset
            dataset = await dataset_repo.create({
                "name": "New Dataset",
                "source": "local",
                "file_path": "/data/new.csv",
                "status": "valid",
                "row_count": 1000,
                "columns": [],
                "metadata": {}
            }, commit=False)

            # Create chart for the dataset
            chart = await chart_repo.create({
                "name": "New Chart",
                "chart_type": "line",
                "dataset_id": dataset.id,
                "config": {}
            }, commit=False)

            # Commit both operations together
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise
```

### Bulk Operations

```python
async def bulk_operations_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        # Bulk create
        datasets = await repo.bulk_create([
            {
                "name": f"Dataset {i}",
                "source": "local",
                "file_path": f"/data/{i}.csv",
                "status": "valid",
                "row_count": 1000 * i,
                "columns": [],
                "metadata": {}
            }
            for i in range(10)
        ])

        print(f"Created {len(datasets)} datasets")
```

### Pagination

```python
async def pagination_example():
    async with db_manager.session() as session:
        repo = DatasetRepository(session)

        page_size = 20
        page = 1

        # Get page 1
        datasets = await repo.get_multi(
            skip=(page - 1) * page_size,
            limit=page_size,
            order_by="-created_at"  # Sort by created_at descending
        )

        # Get total count
        total = await repo.count()
        total_pages = (total + page_size - 1) // page_size
```

### FastAPI Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.database.repositories import DatasetRepository

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset

@router.post("/")
async def create_dataset(
    dataset_data: dict,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    dataset = await repo.create(dataset_data)
    return dataset

@router.get("/")
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    source: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)

    if source or status:
        datasets = await repo.get_with_filters(
            source=source,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        datasets = await repo.get_multi(skip=skip, limit=limit)

    total = await repo.count()

    return {
        "items": datasets,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

## Best Practices

1. **Always use async/await**: All database operations are async
2. **Use dependency injection**: Prefer `Depends(get_db)` in FastAPI routes
3. **Handle errors**: Wrap operations in try/except blocks
4. **Use soft deletes**: Default to `soft=True` for delete operations
5. **Commit transactions**: Remember to commit or use `commit=True`
6. **Close sessions**: Use context managers or dependency injection for automatic cleanup
7. **Use pagination**: Limit query results for better performance
8. **Add indexes**: Models already have appropriate indexes for common queries
9. **Use enums**: Use model enums instead of strings for type safety
10. **Audit trail**: Pass `user_id` for create/update operations

## Troubleshooting

### Connection Issues

```python
# Check database connection
from app.database.session import db_manager

async def check_connection():
    db_manager.init()
    try:
        async with db_manager.session() as session:
            await session.execute(select(1))
            print("Database connection OK")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await db_manager.close()
```

### Migration Issues

If you need to modify the schema, consider using Alembic for migrations instead of `create_all()`.

### Performance Issues

- Use `selectin` loading for relationships (already configured)
- Add appropriate indexes (already configured for common queries)
- Use pagination for large result sets
- Consider connection pooling settings in config
