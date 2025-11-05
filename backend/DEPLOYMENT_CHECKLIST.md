# Dataset API Deployment Checklist

Use this checklist to verify the dataset API migration is working correctly in your environment.

---

## Pre-Deployment Checklist

### 1. Database Setup
- [ ] MySQL database is running and accessible
- [ ] Database connection string is configured in `.env`
- [ ] Database tables are created (run migrations)
- [ ] Database user has proper permissions (SELECT, INSERT, UPDATE, DELETE)
- [ ] Indexes are created on datasets table

**Verify**:
```bash
# Check database connection
mysql -h localhost -u your_user -p -e "SHOW DATABASES;"

# Check tables exist
mysql -h localhost -u your_user -p your_database -e "SHOW TABLES LIKE 'datasets';"

# Check indexes
mysql -h localhost -u your_user -p your_database -e "SHOW INDEX FROM datasets;"
```

### 2. Dependencies
- [ ] All Python dependencies installed (`poetry install` or `pip install -r requirements.txt`)
- [ ] SQLAlchemy version >= 2.0.23
- [ ] Pydantic version >= 2.5.0
- [ ] Loguru version >= 0.7.2
- [ ] FastAPI version >= 0.104.1

**Verify**:
```bash
poetry show | grep -E "sqlalchemy|pydantic|loguru|fastapi"
# or
pip list | grep -E "sqlalchemy|pydantic|loguru|fastapi"
```

### 3. Configuration
- [ ] `.env` file exists with correct values
- [ ] `DATABASE_URL` is set and correct
- [ ] Logging configuration is set
- [ ] CORS settings configured (if needed)

**Verify**:
```bash
# Check .env file
cat backend/.env | grep -E "DATABASE_URL|LOG_LEVEL"
```

### 4. Code Changes
- [ ] `dataset.py` schemas updated (uses `extra_metadata`)
- [ ] `dataset_api.py` uses SQLAlchemy (no in-memory storage)
- [ ] Logging imports are correct
- [ ] Database session dependency is imported

**Verify**:
```bash
# Check for in-memory storage (should return nothing)
grep -n "_datasets.*dict" backend/app/modules/data_management/api/dataset_api.py

# Check for database imports
grep -n "from app.database import get_db" backend/app/modules/data_management/api/dataset_api.py
```

---

## Post-Deployment Checklist

### 1. API Server Start
- [ ] Server starts without errors
- [ ] No import errors in logs
- [ ] Database connection successful
- [ ] API documentation accessible (http://localhost:8000/docs)

**Verify**:
```bash
# Start server (check for errors)
uvicorn app.main:app --reload

# Check server is running
curl http://localhost:8000/docs
```

### 2. Basic Functionality Tests

#### Test 1: List Datasets (Empty)
- [ ] Returns 200 status code
- [ ] Returns `{"total": 0, "items": []}`

```bash
curl -X GET "http://localhost:8000/api/datasets" -H "accept: application/json"
```

**Expected**:
```json
{"total": 0, "items": []}
```

#### Test 2: Create Dataset
- [ ] Returns 201 status code
- [ ] Dataset has ID, timestamps
- [ ] Status is "pending"
- [ ] Returns metadata correctly

```bash
curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Dataset",
    "source": "local",
    "file_path": "/data/test.csv",
    "extra_metadata": {"test": true}
  }'
```

**Expected**:
- `status_code`: 201
- `status`: "pending"
- `metadata.test`: true

#### Test 3: Get Dataset by ID
- [ ] Returns 200 status code
- [ ] Dataset details match created dataset

```bash
# Replace {id} with actual ID from Test 2
curl -X GET "http://localhost:8000/api/datasets/{id}"
```

#### Test 4: Update Dataset
- [ ] Returns 200 status code
- [ ] Updates are persisted
- [ ] `updated_at` timestamp changes

```bash
curl -X PUT "http://localhost:8000/api/datasets/{id}" \
  -H "Content-Type: application/json" \
  -d '{"status": "valid", "row_count": 100}'
```

#### Test 5: List Datasets (With Data)
- [ ] Returns 200 status code
- [ ] `total` is >= 1
- [ ] Created dataset is in items

```bash
curl -X GET "http://localhost:8000/api/datasets"
```

#### Test 6: Delete Dataset
- [ ] Returns 204 status code
- [ ] Dataset no longer appears in list

```bash
curl -X DELETE "http://localhost:8000/api/datasets/{id}"
```

### 3. Advanced Functionality Tests

#### Test 7: Duplicate Name Prevention
- [ ] Creating dataset with existing name returns 409

```bash
# Create first dataset
curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "Duplicate Test", "source": "local", "file_path": "/data/dup.csv"}'

# Try to create duplicate (should fail with 409)
curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "Duplicate Test", "source": "local", "file_path": "/data/dup2.csv"}'
```

**Expected**: Status 409, error message about duplicate name

#### Test 8: Pagination
- [ ] Pagination parameters work correctly
- [ ] `total` count is accurate

```bash
# Create multiple datasets first (at least 3)

# Test pagination
curl -X GET "http://localhost:8000/api/datasets?skip=0&limit=2"
curl -X GET "http://localhost:8000/api/datasets?skip=2&limit=2"
```

**Expected**: First call returns 2 items, second call returns remaining items

#### Test 9: Filtering
- [ ] Filter by source works
- [ ] Filter by status works
- [ ] Search by name works

```bash
# Filter by source
curl -X GET "http://localhost:8000/api/datasets?source=local"

# Filter by status
curl -X GET "http://localhost:8000/api/datasets?status=valid"

# Search by name
curl -X GET "http://localhost:8000/api/datasets?search=test"
```

#### Test 10: Soft Delete
- [ ] Soft delete removes from list
- [ ] Dataset still in database with `is_deleted=1`

```bash
# Create and soft delete
DATASET_ID=$(curl -s -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "Soft Delete Test", "source": "local", "file_path": "/data/soft.csv"}' \
  | jq -r '.id')

curl -X DELETE "http://localhost:8000/api/datasets/$DATASET_ID"

# Check database
mysql -h localhost -u your_user -p your_database -e \
  "SELECT id, name, is_deleted FROM datasets WHERE id='$DATASET_ID';"
```

**Expected**: `is_deleted` = 1

### 4. Database Verification

#### Check Data Persistence
- [ ] Created datasets are in database
- [ ] Updates are persisted
- [ ] Soft deletes set `is_deleted=1`
- [ ] Timestamps are correct

```bash
# Check database contents
mysql -h localhost -u your_user -p your_database -e "SELECT * FROM datasets LIMIT 5;"
```

#### Check Constraints
- [ ] `row_count` cannot be negative
- [ ] `name` is required
- [ ] `source` is required

```bash
# Try to create dataset with negative row_count (should fail in database)
# This should be prevented by application validation
```

### 5. Logging Verification

#### Check Log Files
- [ ] Log files are being created in `/backend/logs/`
- [ ] Logs contain structured JSON
- [ ] Correlation IDs are present
- [ ] All CRUD operations are logged

```bash
# Check latest log file
tail -f backend/logs/qlib-ui_*.log

# Test with correlation ID
curl -X GET "http://localhost:8000/api/datasets" \
  -H "X-Correlation-ID: test-correlation-123"

# Check log for correlation ID
grep "test-correlation-123" backend/logs/qlib-ui_*.log
```

#### Log Levels
- [ ] INFO: Normal operations
- [ ] WARNING: Validation failures, duplicates
- [ ] ERROR: Database errors, exceptions

**Verify**:
```bash
# Check log levels
grep -E "INFO|WARNING|ERROR" backend/logs/qlib-ui_*.log | tail -20
```

### 6. Error Handling Verification

#### Test Error Scenarios
- [ ] 404 for non-existent dataset
- [ ] 409 for duplicate name
- [ ] 400 for validation errors
- [ ] 422 for invalid JSON schema
- [ ] 500 for database errors (simulate by stopping database)

```bash
# Test 404
curl -X GET "http://localhost:8000/api/datasets/00000000-0000-0000-0000-000000000000"

# Test 422 (invalid data)
curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'  # Missing required fields

# Test 500 (stop database and make request)
```

### 7. Performance Verification

#### Response Times
- [ ] List datasets < 500ms
- [ ] Get single dataset < 200ms
- [ ] Create dataset < 500ms
- [ ] Update dataset < 500ms

**Verify**:
```bash
# Measure response time
time curl -X GET "http://localhost:8000/api/datasets"
```

#### Database Connection Pool
- [ ] Multiple concurrent requests work
- [ ] No connection leaks

```bash
# Make concurrent requests
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/datasets" &
done
wait
```

### 8. Integration Tests

#### Run Test Suite
- [ ] All tests pass
- [ ] No warnings or errors
- [ ] Coverage is adequate

```bash
# Run tests
pytest tests/test_dataset_api_migration.py -v

# Run with coverage
pytest tests/test_dataset_api_migration.py --cov=app.modules.data_management.api -v
```

**Expected**: All tests pass, coverage > 80%

---

## Rollback Criteria

If any of these conditions are met, consider rollback:

- [ ] Database connection fails consistently
- [ ] More than 10% of requests result in 500 errors
- [ ] Data corruption detected in database
- [ ] Critical functionality broken (cannot create/list datasets)
- [ ] Performance degradation > 3x slower than in-memory version
- [ ] Logging causing disk space issues

---

## Production Deployment Checklist

### Before Deploying to Production

- [ ] All above tests pass in staging environment
- [ ] Database backup created
- [ ] Rollback plan documented and tested
- [ ] Monitoring/alerting configured
- [ ] Load testing completed
- [ ] Security review completed
- [ ] API documentation updated
- [ ] Team trained on new logging/debugging

### Deployment Steps

1. [ ] Create database backup
2. [ ] Run database migrations
3. [ ] Deploy new code
4. [ ] Verify health check endpoint
5. [ ] Test basic CRUD operations
6. [ ] Monitor logs for errors
7. [ ] Monitor database connection pool
8. [ ] Monitor API response times

### Post-Deployment Monitoring (First 24 Hours)

- [ ] No 500 errors in logs
- [ ] Database connections stable
- [ ] API response times acceptable
- [ ] No data integrity issues
- [ ] Logging working correctly
- [ ] No disk space issues from logs

---

## Troubleshooting Guide

### Issue: API won't start
**Check**:
- Database connection string
- Python dependencies installed
- Import errors in logs

### Issue: 500 errors on all requests
**Check**:
- Database is running
- Database credentials correct
- Database user permissions
- Firewall rules

### Issue: Datasets not persisting
**Check**:
- Database tables exist
- Transactions committing
- No rollback errors in logs

### Issue: Logging not working
**Check**:
- Log directory permissions
- Disk space available
- Loguru configuration
- Log file rotation settings

### Issue: Slow performance
**Check**:
- Database indexes created
- Connection pool size
- Network latency to database
- Slow query logs

---

## Sign-Off

### Development Environment
- [ ] All checklist items verified
- [ ] Signature: _________________ Date: _______

### Staging Environment
- [ ] All checklist items verified
- [ ] Signature: _________________ Date: _______

### Production Environment
- [ ] All checklist items verified
- [ ] Signature: _________________ Date: _______

---

## Notes

Use this section to document any issues found, workarounds, or special considerations:

```
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
```
