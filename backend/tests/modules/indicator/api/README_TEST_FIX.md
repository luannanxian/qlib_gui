# Test Infrastructure Fix

## Problem

The original test infrastructure using `TestClient` from FastAPI had async SQLAlchemy table creation timing issues:

```python
# Original problematic approach
with TestClient(app) as client:
    response = client.get("/api/indicators")
```

**Error**: `sqlite3.OperationalError: no such table: indicator_components`

### Root Cause

The `TestClient` synchronous context manager doesn't properly handle async database initialization lifecycle, causing tables to not be created before tests run.

## Solution

Use `httpx.AsyncClient` instead of `TestClient` with proper async fixtures:

### New Test Infrastructure Files

1. **`conftest_async.py`** - Async-first test fixtures
   - `event_loop` - Session-scoped event loop
   - `test_db_engine` - Function-scoped database engine with table creation
   - `test_db_session` - Function-scoped database session
   - `async_client` - Function-scoped HTTP client with DB override

2. **`test_indicator_api_async.py`** - Example async tests

### Usage

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_indicators(async_client: AsyncClient):
    response = await async_client.get("/api/indicators")
    assert response.status_code == 200
```

### Key Differences

| Aspect | Old (TestClient) | New (AsyncClient) |
|--------|------------------|-------------------|
| **Client Type** | Synchronous | Asynchronous |
| **Test Decorator** | None | `@pytest.mark.asyncio` |
| **Request Method** | `client.get()` | `await async_client.get()` |
| **Table Creation** | Unreliable timing | Guaranteed before tests |
| **Isolation** | Flaky | Full per-test isolation |

### Benefits

✅ **Reliable**: Tables are guaranteed to exist before tests run
✅ **Async-Native**: Properly handles async SQLAlchemy operations
✅ **Isolated**: Each test gets fresh database session
✅ **Fast**: In-memory SQLite with proper cleanup
✅ **Type-Safe**: Full async/await support

### Migration Guide

**Before:**
```python
def test_list_indicators(client):
    response = client.get("/api/indicators")
```

**After:**
```python
@pytest.mark.asyncio
async def test_list_indicators(async_client: AsyncClient):
    response = await async_client.get("/api/indicators")
```

### Running Tests

```bash
# Run all async tests
pytest tests/modules/indicator/api/test_indicator_api_async.py -v

# Run specific test
pytest tests/modules/indicator/api/test_indicator_api_async.py::test_list_indicators_empty -v

# Run with coverage
pytest tests/modules/indicator/api/test_indicator_api_async.py --cov=app.modules.indicator
```

## Future Improvements

1. **Fixture Factories**: Create helpers for common test data
2. **Database Seeding**: Add fixtures to populate test data
3. **Parallel Testing**: Enable with `pytest-xdist`
4. **Performance**: Consider shared DB for read-only tests

## Status

✅ **FIXED** - Test infrastructure now works reliably with async SQLAlchemy
