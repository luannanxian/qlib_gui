# Database Layer Quick Start Guide

## 🚀 Quick Setup

### 1. Install Dependencies (if not already done)

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create all tables
python -m app.database.init_db init

# Or reset database (drop and recreate)
python -m app.database.init_db reset
```

### 3. Verify Installation

```bash
# Run verification script
PYTHONPATH=/Users/zhenkunliu/project/qlib-ui/backend python scripts/verify_database.py

# Run tests
pytest tests/test_database/ -v
```

## 📖 Quick Examples

### Example 1: Create a Dataset

```python
import asyncio
from app.database import db_manager
from app.database.repositories import DatasetRepository

async def create_dataset():
    # Initialize database
    db_manager.init()
    
    async with db_manager.session() as session:
        repo = DatasetRepository(session)
        
        dataset = await repo.create({
            "name": "Stock Prices 2024",
            "source": "local",
            "file_path": "/data/stocks.csv",
            "status": "valid",
            "row_count": 10000,
            "columns": ["date", "open", "high", "low", "close", "volume"],
            "metadata": {"description": "Historical stock data"}
        })
        
        print(f"Created dataset: {dataset.id}")
    
    await db_manager.close()

asyncio.run(create_dataset())
```

### Example 2: Create a Chart

```python
async def create_chart(dataset_id):
    db_manager.init()
    
    async with db_manager.session() as session:
        repo = ChartRepository(session)
        
        chart = await repo.create({
            "name": "Price Candlestick",
            "chart_type": "kline",
            "dataset_id": dataset_id,
            "config": {
                "x_axis": "date",
                "y_axis": ["open", "high", "low", "close"],
                "colors": {"up": "green", "down": "red"}
            }
        })
        
        print(f"Created chart: {chart.id}")
    
    await db_manager.close()
```

### Example 3: User Preferences

```python
async def manage_user_prefs():
    db_manager.init()
    
    async with db_manager.session() as session:
        repo = UserPreferencesRepository(session)
        
        # Get or create
        prefs, created = await repo.get_or_create(
            "user-123",
            defaults={"mode": "expert", "theme": "dark"}
        )
        
        # Update mode
        await repo.update_mode("user-123", "expert")
        
        # Add completed guide
        await repo.add_completed_guide("user-123", "intro-tour")
        
        # Update custom settings
        await repo.update_settings("user-123", {
            "chart_type": "kline",
            "auto_refresh": True
        })
    
    await db_manager.close()
```

### Example 4: FastAPI Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.database.repositories import DatasetRepository

router = APIRouter()

@router.get("/datasets")
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    datasets = await repo.get_multi(skip=skip, limit=limit)
    total = await repo.count()
    
    return {
        "items": datasets,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/datasets")
async def create_dataset(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    return await repo.create(data)

@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset
```

## 📚 Documentation

- **Complete Guide**: See `/app/database/README.md`
- **Usage Examples**: See `/app/database/USAGE_EXAMPLES.md`
- **Implementation Details**: See `/backend/IMPLEMENTATION_SUMMARY.md`
- **Checklist**: See `/backend/DATABASE_IMPLEMENTATION_CHECKLIST.md`

## 🧪 Running Tests

```bash
# All tests
pytest tests/test_database/ -v

# Specific test file
pytest tests/test_database/test_repositories.py -v

# With coverage
pytest --cov=app.database tests/test_database/

# Single test
pytest tests/test_database/test_repositories.py::TestDatasetRepository::test_create_dataset -v
```

## 🗂️ File Structure

```
app/database/
├── models/               # Data models
│   ├── dataset.py       # Dataset model
│   ├── chart.py         # Chart model
│   └── user_preferences.py
├── repositories/         # Data access layer
│   ├── base.py          # Generic CRUD
│   ├── dataset.py       # Dataset queries
│   ├── chart.py         # Chart queries
│   └── user_preferences.py
├── base.py              # Base models
├── session.py           # Session management
└── init_db.py          # Database initialization
```

## 🔧 Configuration

Edit `app/config.py`:

```python
DATABASE_URL = "mysql+aiomysql://user:pass@host:port/db?charset=utf8mb4"
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_RECYCLE = 3600
DATABASE_POOL_PRE_PING = True
```

## 🎯 Key Concepts

### Soft Delete
```python
# Soft delete (default)
await repo.delete(id, soft=True)

# Hard delete
await repo.delete(id, soft=False)

# Restore
await repo.restore(id)
```

### Pagination
```python
# Get page 1 (items 0-19)
items = await repo.get_multi(skip=0, limit=20)

# Get page 2 (items 20-39)
items = await repo.get_multi(skip=20, limit=20)
```

### Filtering
```python
# Single filter
datasets = await repo.get_by_source("local")

# Multiple filters
datasets = await repo.get_with_filters(
    source="local",
    status="valid",
    search_term="2024"
)
```

## 🚨 Common Issues

### Issue: "No module named 'app'"
**Solution**: Set PYTHONPATH
```bash
export PYTHONPATH=/Users/zhenkunliu/project/qlib-ui/backend
# Or run from backend directory
cd /Users/zhenkunliu/project/qlib-ui/backend
```

### Issue: "Cannot import DeclarativeBase"
**Solution**: Install SQLAlchemy 2.0+
```bash
pip install "sqlalchemy>=2.0"
```

### Issue: "Connection timeout"
**Solution**: Check MySQL server
```bash
mysql -h 192.168.3.46 -u remote -p
```

## ✅ Verification Checklist

- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Tests passing
- [ ] Can create records
- [ ] Can query records
- [ ] FastAPI integration working

## 🎉 You're Ready!

The database layer is fully implemented and ready to use. Start building your API endpoints!
