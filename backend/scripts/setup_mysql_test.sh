#!/bin/bash
# Quick Start Script for MySQL Test Environment
#
# This script helps you quickly set up and verify MySQL test environment.
# Usage: ./scripts/setup_mysql_test.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="/Users/zhenkunliu/project/qlib-ui/backend"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}MySQL Test Environment Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Check Docker
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker daemon is not running${NC}"
    echo "Please start Docker Desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker is available${NC}"
echo ""

# Step 2: Check docker-compose
echo -e "${YELLOW}[2/5] Checking Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: docker-compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose is available${NC}"
echo ""

# Step 3: Start MySQL test database
echo -e "${YELLOW}[3/5] Starting MySQL test database...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for MySQL to be healthy
echo -e "${BLUE}Waiting for MySQL to be ready (max 60s)...${NC}"
WAIT_TIME=0
MAX_WAIT=60
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}✅ MySQL is ready${NC}"
        break
    fi
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
    echo -n "."
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ Error: MySQL failed to start within ${MAX_WAIT}s${NC}"
    echo "Check logs: docker-compose -f docker-compose.test.yml logs mysql-test"
    exit 1
fi
echo ""

# Step 4: Verify database connectivity
echo -e "${YELLOW}[4/5] Verifying database connectivity...${NC}"
if docker exec qlib-mysql-test mysql -u test_user -ptest_password -e "SHOW DATABASES;" | grep -q "qlib_ui_test"; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
    echo -e "${GREEN}✅ Test database 'qlib_ui_test' exists${NC}"
else
    echo -e "${RED}❌ Error: Cannot connect to database${NC}"
    exit 1
fi
echo ""

# Step 5: Set up environment variables
echo -e "${YELLOW}[5/5] Configuring environment...${NC}"
if [ ! -f ".env.test" ]; then
    echo -e "${YELLOW}⚠️  .env.test not found, using default configuration${NC}"
fi

# Export test database URL
export DATABASE_URL_TEST="mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4"
echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${GREEN}MySQL test database is running and ready.${NC}"
echo ""
echo -e "${YELLOW}To run tests with MySQL:${NC}"
echo ""
echo "  export DATABASE_URL_TEST=\"mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4\""
echo "  pytest tests/modules/indicator/repositories/"
echo ""
echo -e "${YELLOW}To stop the test database:${NC}"
echo ""
echo "  docker-compose -f docker-compose.test.yml down"
echo ""
echo -e "${YELLOW}To remove database volumes (clean slate):${NC}"
echo ""
echo "  docker-compose -f docker-compose.test.yml down -v"
echo ""
echo -e "${YELLOW}To view MySQL logs:${NC}"
echo ""
echo "  docker-compose -f docker-compose.test.yml logs -f mysql-test"
echo ""

# Optional: Run a quick test
read -p "Do you want to run a quick verification test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Running verification test...${NC}"
    export DATABASE_URL_TEST="mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4"

    if pytest tests/modules/indicator/repositories/test_fixture_debug.py -v; then
        echo -e "${GREEN}✅ Verification test passed!${NC}"
    else
        echo -e "${RED}❌ Verification test failed${NC}"
        echo "Check the output above for details"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}All systems ready for TDD with MySQL! 🚀${NC}"
