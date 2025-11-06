# MySQL Test Database Setup Guide

This guide explains how to configure and use MySQL for TDD testing in the qlib-ui backend project.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration Options](#configuration-options)
- [Usage Scenarios](#usage-scenarios)
- [Troubleshooting](#troubleshooting)

---

## Overview

The test infrastructure supports **two database backends**:

| Database | Use Case | Speed | Isolation | Production Similarity |
|----------|----------|-------|-----------|----------------------|
| **SQLite** | Local development, fast iteration | ⚡ Very Fast | ✅ Perfect | ⚠️ Moderate |
| **MySQL** | Integration testing, CI/CD | 🐢 Slower | ✅ Good | ✅ Excellent |

**Recommendation**: Use SQLite for rapid TDD cycles, MySQL for pre-commit integration testing.

---

## Quick Start

### Option 1: SQLite (Default, No Setup Required)

```bash
# No configuration needed - works out of the box
cd /Users/zhenkunliu/project/qlib-ui/backend
pytest tests/modules/indicator/repositories/
```

### Option 2: MySQL (Docker)

```bash
# 1. Start MySQL test database
cd /Users/zhenkunliu/project/qlib-ui/backend
docker-compose -f docker-compose.test.yml up -d

# 2. Wait for MySQL to be ready (check health)
docker-compose -f docker-compose.test.yml ps

# 3. Run tests with MySQL
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4
pytest tests/modules/indicator/repositories/

# 4. Stop test database when done
docker-compose -f docker-compose.test.yml down
```

### Option 3: MySQL (Local Installation)

If you have MySQL installed locally:

```bash
# 1. Create test database and user
mysql -u root -p << EOF
CREATE DATABASE qlib_ui_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'test_user'@'localhost' IDENTIFIED BY 'test_password';
GRANT ALL PRIVILEGES ON qlib_ui_test.* TO 'test_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# 2. Update .env.test
echo "DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3306/qlib_ui_test?charset=utf8mb4" > .env.test

# 3. Run tests
pytest tests/modules/indicator/repositories/
```

---

## Configuration Options

### Environment Variables

All test database configuration is in `.env.test`:

```bash
# Database URL (switch between SQLite and MySQL)
DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4

# Connection Pool Settings (MySQL only)
TEST_DB_POOL_SIZE=5              # Number of persistent connections
TEST_DB_MAX_OVERFLOW=5           # Additional connections under load
TEST_DB_POOL_RECYCLE=1800        # Recycle connections after 30 min
TEST_DB_POOL_PRE_PING=true       # Check connection health before use

# Debugging
TEST_DB_ECHO_SQL=false           # Set to true to see all SQL queries
TEST_DB_KEEP_ALIVE=false         # Set to true to keep DB after tests
```

### Docker Compose Configuration

`docker-compose.test.yml` provides isolated MySQL instance:

```yaml
# Key settings:
ports:
  - "3307:3306"  # Different port to avoid conflict with dev DB

volumes:
  - type: tmpfs   # In-memory storage for speed
    target: /var/lib/mysql

command:
  - --innodb_flush_log_at_trx_commit=2  # Faster commits for tests
```

---

## Usage Scenarios

### Scenario 1: Fast TDD Loop (SQLite)

```bash
# Default behavior - no setup needed
pytest tests/modules/indicator/repositories/test_custom_factor_repository.py -v
```

**Pros**: ⚡ Instant startup, perfect for rapid development
**Cons**: ⚠️ Some MySQL-specific features may behave differently

### Scenario 2: Pre-Commit Validation (MySQL)

```bash
# Run full test suite with MySQL before committing
docker-compose -f docker-compose.test.yml up -d
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/ -v
docker-compose -f docker-compose.test.yml down
```

**Pros**: ✅ Catches MySQL-specific issues early
**Cons**: 🐢 Slower test execution

### Scenario 3: CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
services:
  mysql:
    image: mysql:8.0
    env:
      MYSQL_DATABASE: qlib_ui_test
      MYSQL_USER: test_user
      MYSQL_PASSWORD: test_password
    options: >-
      --health-cmd="mysqladmin ping"
      --health-interval=10s

steps:
  - name: Run tests
    env:
      DATABASE_URL_TEST: mysql+aiomysql://test_user:test_password@mysql:3306/qlib_ui_test
    run: pytest tests/
```

### Scenario 4: Debugging SQL Queries

```bash
# Enable SQL query logging
export TEST_DB_ECHO_SQL=true
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/modules/indicator/repositories/test_custom_factor_repository.py::test_count_user_factors_all -v -s
```

---

## Verification Commands

### Check MySQL Connection

```bash
# Test database connectivity
mysql -h 127.0.0.1 -P 3307 -u test_user -ptest_password -e "SHOW DATABASES;"
```

### Verify Test Database Configuration

```bash
# Run pytest with verbose configuration display
pytest tests/modules/indicator/repositories/ -v --co

# Output shows:
# Test Database: MySQL
# Database URL: mysql+aiomysql://test_user:***@localhost:3307/qlib_ui_test
# Pool Size: 5
# Echo SQL: False
```

### Run Specific Tests

```bash
# Test only repository layer
pytest tests/modules/indicator/repositories/ -v

# Test single file
pytest tests/modules/indicator/repositories/test_custom_factor_repository.py -v

# Test single function
pytest tests/modules/indicator/repositories/test_custom_factor_repository.py::test_count_user_factors_all -v
```

---

## Troubleshooting

### Issue 1: Connection Refused

**Symptom**: `sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")`

**Solutions**:
```bash
# 1. Check if MySQL container is running
docker-compose -f docker-compose.test.yml ps

# 2. Wait for MySQL to be healthy
docker-compose -f docker-compose.test.yml logs mysql-test | grep "ready for connections"

# 3. Verify port mapping
netstat -an | grep 3307
```

### Issue 2: Authentication Failed

**Symptom**: `sqlalchemy.exc.OperationalError: (1045, "Access denied for user 'test_user'@'localhost'")`

**Solutions**:
```bash
# 1. Verify credentials in .env.test match docker-compose.test.yml
cat .env.test | grep DATABASE_URL_TEST

# 2. Reset test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d

# 3. Check MySQL user grants
docker exec -it qlib-mysql-test mysql -u root -ptest_root_password -e "SHOW GRANTS FOR 'test_user'@'%';"
```

### Issue 3: Table Already Exists

**Symptom**: `sqlalchemy.exc.ProgrammingError: (1050, "Table 'datasets' already exists")`

**Solutions**:
```bash
# 1. Drop all tables (fixture should do this automatically)
pytest tests/ --tb=short  # Check fixture teardown logs

# 2. Manually reset database
docker exec -it qlib-mysql-test mysql -u test_user -ptest_password qlib_ui_test -e "DROP DATABASE qlib_ui_test; CREATE DATABASE qlib_ui_test;"

# 3. Restart MySQL container
docker-compose -f docker-compose.test.yml restart mysql-test
```

### Issue 4: Slow Test Execution

**Symptom**: Tests run significantly slower with MySQL than SQLite

**Optimizations**:
```bash
# 1. Use tmpfs volume (already configured in docker-compose.test.yml)
# Check if tmpfs is active:
docker inspect qlib-mysql-test | grep tmpfs

# 2. Reduce test isolation (use session-scoped fixtures for some tests)
# Edit conftest.py: change @pytest_asyncio.fixture(scope="function") to scope="session"

# 3. Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto  # Use all CPU cores
```

### Issue 5: Character Encoding Issues

**Symptom**: `UnicodeEncodeError` or garbled Chinese characters

**Solutions**:
```bash
# 1. Verify charset in connection URL
echo $DATABASE_URL_TEST | grep charset=utf8mb4

# 2. Check MySQL server charset
docker exec -it qlib-mysql-test mysql -u test_user -ptest_password -e "SHOW VARIABLES LIKE 'character_set%';"

# Expected output:
# character_set_server: utf8mb4
# collation_server: utf8mb4_unicode_ci

# 3. Update .env.test with explicit charset
DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4
```

---

## Performance Benchmarks

Based on 20 repository tests:

| Database | Execution Time | Startup Time | Total Time |
|----------|---------------|--------------|------------|
| SQLite   | ~2.5s         | ~0.1s        | **~2.6s**  |
| MySQL    | ~4.2s         | ~1.5s        | **~5.7s**  |

**Recommendation**: Use SQLite for TDD, MySQL for final validation.

---

## Best Practices

### 1. Default to SQLite for Development
```bash
# Keep .env.test configured for SQLite
DATABASE_URL_TEST=sqlite+aiosqlite:///:memory:
```

### 2. Run MySQL Tests Before Commits
```bash
# Pre-commit hook (.git/hooks/pre-commit)
#!/bin/bash
docker-compose -f docker-compose.test.yml up -d
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/modules/indicator/repositories/ || exit 1
docker-compose -f docker-compose.test.yml down
```

### 3. Use Conditional Markers for Database-Specific Tests
```python
import pytest

@pytest.mark.mysql
async def test_mysql_specific_feature():
    """This test only runs when using MySQL."""
    pass

@pytest.mark.sqlite
async def test_sqlite_specific_feature():
    """This test only runs when using SQLite."""
    pass
```

### 4. Clean Up Resources
```bash
# Always clean up after integration tests
docker-compose -f docker-compose.test.yml down -v  # Remove volumes too
```

---

## Additional Resources

- **SQLAlchemy Async Documentation**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **MySQL Docker Official Image**: https://hub.docker.com/_/mysql
- **aiomysql Documentation**: https://aiomysql.readthedocs.io/

---

## Support

If you encounter issues not covered in this guide:

1. Check pytest output with `-v -s` flags for detailed logs
2. Enable SQL query logging: `export TEST_DB_ECHO_SQL=true`
3. Inspect Docker logs: `docker-compose -f docker-compose.test.yml logs mysql-test`
4. Review conftest.py configuration: `/Users/zhenkunliu/project/qlib-ui/backend/tests/modules/indicator/repositories/conftest.py`
