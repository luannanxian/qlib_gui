# Task Scheduling API Tests

Complete test suite for the Task Scheduling API endpoints with **87 comprehensive tests**.

## Quick Start

### 1. Set Environment Variables

```bash
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export SECRET_KEY="wQqU5pxUUsAQGTQsqwUQakjtHqk6Hm2hIFGyfg8PRa9IEH0WXQe7JXZQnBRQljpUal0PhrhMzgBNW2vtymY_og"
```

### 2. Run All Tests

```bash
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py -v
```

### 3. Run with Coverage Report

```bash
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py \
  --cov=backend/app/modules/task_scheduling/api/task_api \
  --cov-report=term-missing \
  --cov-report=html
```

## Test Organization

### By Endpoint

Run tests for a specific endpoint:

```bash
# Test task creation
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestCreateTask -v

# Test task listing
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestListTasks -v

# Test task retrieval
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestGetTask -v

# Test task lifecycle
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestTaskLifecycle -v
```

### By Status Transition

```bash
# Test start task
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestStartTask -v

# Test pause task
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestPauseTask -v

# Test resume task
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestResumeTask -v

# Test cancel task
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py::TestCancelTask -v
```

## Test Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 87 |
| Passing | 87 (100%) |
| Failed | 0 |
| Line Coverage | 50% |
| Endpoints Covered | 12/12 |
| Execution Time | ~6 seconds |

## Endpoints Tested

- ✓ POST /api/v1/tasks - Create new task
- ✓ GET /api/v1/tasks - List tasks with pagination
- ✓ GET /api/v1/tasks/{id} - Get task by ID
- ✓ PUT /api/v1/tasks/{id}/start - Start task
- ✓ PUT /api/v1/tasks/{id}/pause - Pause task
- ✓ PUT /api/v1/tasks/{id}/resume - Resume task
- ✓ PUT /api/v1/tasks/{id}/cancel - Cancel task
- ✓ PUT /api/v1/tasks/{id}/progress - Update task progress
- ✓ DELETE /api/v1/tasks/{id} - Delete task
- ✓ GET /api/v1/tasks/user/{user_id} - Get user's tasks
- ✓ GET /api/v1/tasks/pending/next - Get next pending task
- ✓ GET /api/v1/tasks/stats - Get task statistics

## Test Coverage Details

### Task Creation (21 tests)
- Valid creation with all field types
- Default value assignment
- Required field validation
- Invalid task type detection
- Task-specific parameter validation
- Priority boundary testing
- Name length validation

### Task Listing (10 tests)
- Empty list handling
- Pagination with skip/limit
- Boundary value testing
- Invalid parameter handling

### Task Retrieval (6 tests)
- Successful retrieval by ID
- 404 error for non-existent tasks
- ID format validation
- Special character handling

### Status Transitions (22 tests)
- Start, pause, resume, cancel operations
- Status transition validation
- Error handling for invalid transitions

### Progress Update (11 tests)
- Progress boundary testing (0-100)
- Field validation
- Error handling

### Task Deletion (7 tests)
- Successful deletion
- Status-based deletion rules
- Error handling

### User & Priority Queries (8 tests)
- User-specific task retrieval
- Priority-based task selection
- Empty result handling

### Statistics (3 tests)
- Task counts by status
- Empty database handling
- All status types

### Lifecycle (3 tests)
- Complete task lifecycle
- Sequential operations

## Development Notes

### Test File Location
```
backend/tests/test_task_scheduling/api/test_task_api.py
```

### Fixtures (in conftest.py)
- `test_engine`: In-memory SQLite database
- `db_session`: Async database session
- `async_client`: HTTP client for API testing

### Test Pattern
All tests follow the **Arrange-Act-Assert (AAA) pattern**:
```python
async def test_example(self, async_client: AsyncClient):
    # ARRANGE - Setup test data
    task_data = {...}
    
    # ACT - Execute API call
    response = await async_client.post("/api/v1/tasks", json=task_data)
    
    # ASSERT - Verify results
    assert response.status_code == 201
    assert response.json()["name"] == "Test Task"
```

## Continuous Integration

Add to your CI pipeline:

```bash
# Run tests with coverage
DATABASE_URL="sqlite+aiosqlite:///:memory:" \
SECRET_KEY="<generated-secret-key>" \
python -m pytest backend/tests/test_task_scheduling/api/test_task_api.py \
  --cov=backend/app/modules/task_scheduling/api/task_api \
  --cov-report=xml \
  --junit-xml=test-results.xml \
  -v
```

## Troubleshooting

### Import Errors
Ensure the backend directory is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

### Database Errors
Tests use in-memory SQLite. If you see database-related errors:
1. Check environment variables are set
2. Clear pytest cache: `pytest --cache-clear`
3. Run individual tests for isolation

### Async Issues
If async tests fail:
1. Ensure pytest-asyncio is installed: `pip install pytest-asyncio`
2. All test methods must be `async def`
3. All client calls must use `await`

## Documentation

For detailed test analysis, see [TEST_SUMMARY.md](TEST_SUMMARY.md)

## Contributing

When adding new tests:
1. Follow AAA pattern
2. Use descriptive docstrings
3. Group related tests in classes
4. Use appropriate status code assertions
5. Test both happy paths and error cases
6. Validate boundary conditions
