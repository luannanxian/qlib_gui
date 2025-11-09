"""
TDD Tests for QuickTestRepository

Following strict TDD methodology (Red-Green-Refactor):
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize code

Test Coverage:
- Create quick test record
- Update test status
- Update test result and metrics
- Find tests by user with pagination
- Find timeout tests
- Find tests by instance
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import QuickTest
from app.database.repositories.quick_test_repository import QuickTestRepository


@pytest.mark.asyncio
class TestQuickTestRepository:
    """Tests for QuickTestRepository"""

    async def test_create_quick_test(self, db_session: AsyncSession, sample_strategy_instance):
        """Test creating a quick test record"""
        # ARRANGE
        repo = QuickTestRepository(db_session)
        test_data = {
            "instance_id": sample_strategy_instance.id,
            "user_id": "user-001",
            "test_config": {"start_date": "2020-01-01", "end_date": "2023-12-31"},
            "logic_flow_snapshot": {"nodes": [], "edges": []},
            "status": "PENDING"
        }

        # ACT
        quick_test = await repo.create(test_data)

        # ASSERT
        assert quick_test.id is not None
        assert quick_test.status == "PENDING"
        assert quick_test.instance_id == sample_strategy_instance.id

    async def test_update_status(self, db_session: AsyncSession, sample_quick_test):
        """Test updating test status"""
        repo = QuickTestRepository(db_session)

        # ACT
        updated = await repo.update_status(sample_quick_test.id, "RUNNING")

        # ASSERT
        assert updated.status == "RUNNING"

    async def test_update_result(self, db_session: AsyncSession, sample_quick_test):
        """Test updating test result and metrics"""
        repo = QuickTestRepository(db_session)
        result_data = {
            "test_result": {"sharpe_ratio": 1.5, "total_return": 0.25},
            "execution_time": 12.5,
            "status": "COMPLETED"
        }

        # ACT
        updated = await repo.update_result(sample_quick_test.id, result_data)

        # ASSERT
        assert updated.status == "COMPLETED"
        assert updated.test_result["sharpe_ratio"] == 1.5
        assert updated.execution_time == 12.5

    async def test_find_by_user_with_pagination(self, db_session: AsyncSession, sample_strategy_instance):
        """Test finding user's tests with pagination"""
        repo = QuickTestRepository(db_session)

        # Create 15 tests for user
        for i in range(15):
            await repo.create({
                "instance_id": sample_strategy_instance.id,
                "user_id": "user-001",
                "test_config": {},
                "logic_flow_snapshot": {},
                "status": "COMPLETED"
            })

        # ACT
        page1 = await repo.find_by_user("user-001", page=1, page_size=10)
        page2 = await repo.find_by_user("user-001", page=2, page_size=10)

        # ASSERT
        assert len(page1) == 10
        assert len(page2) == 5

    async def test_find_timeout_tests(self, db_session: AsyncSession, sample_strategy_instance):
        """Test finding timeout tests (status=RUNNING, created >10min ago)"""
        repo = QuickTestRepository(db_session)

        # Create a test that started 15 minutes ago
        old_test = await repo.create({
            "instance_id": sample_strategy_instance.id,
            "user_id": "user-001",
            "test_config": {},
            "logic_flow_snapshot": {},
            "status": "RUNNING"
        })
        # Manually set created_at to 15 minutes ago
        old_test.created_at = datetime.utcnow() - timedelta(minutes=15)
        await db_session.commit()

        # Create a recent test (2 minutes ago)
        recent_test = await repo.create({
            "instance_id": sample_strategy_instance.id,
            "user_id": "user-001",
            "test_config": {},
            "logic_flow_snapshot": {},
            "status": "RUNNING"
        })

        # ACT
        timeout_tests = await repo.find_timeout_tests(timeout_minutes=10)

        # ASSERT
        assert len(timeout_tests) == 1
        assert timeout_tests[0].id == old_test.id

    async def test_find_by_instance(self, db_session: AsyncSession, sample_strategy_instance):
        """Test finding all tests for a strategy instance"""
        repo = QuickTestRepository(db_session)

        # Create tests for instance
        for i in range(3):
            await repo.create({
                "instance_id": sample_strategy_instance.id,
                "user_id": f"user-{i}",
                "test_config": {},
                "logic_flow_snapshot": {},
                "status": "COMPLETED"
            })

        # ACT
        tests = await repo.find_by_instance(sample_strategy_instance.id)

        # ASSERT
        assert len(tests) == 3
        for test in tests:
            assert test.instance_id == sample_strategy_instance.id
