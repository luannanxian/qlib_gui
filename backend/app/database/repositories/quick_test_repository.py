"""
QuickTest Repository

Repository for managing quick test operations with specialized
query methods for test execution and result tracking.
"""

from typing import List, Optional
from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import QuickTest
from app.database.repositories.base import BaseRepository


class QuickTestRepository(BaseRepository[QuickTest]):
    """
    Repository for QuickTest operations.

    Provides specialized methods for:
    - Test status management (PENDING -> RUNNING -> COMPLETED/FAILED)
    - Result storage and metrics tracking
    - User test history with pagination
    - Timeout detection for stuck tests
    - Instance-based test queries
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with QuickTest model"""
        super().__init__(QuickTest, session)

    async def update_status(
        self,
        test_id: str,
        status: str,
        commit: bool = True
    ) -> Optional[QuickTest]:
        """
        Update test status.

        Args:
            test_id: Test ID
            status: New status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
            commit: Whether to commit the transaction

        Returns:
            Updated test or None if not found
        """
        update_data = {"status": status}

        # Set started_at when status changes to RUNNING
        if status == "RUNNING":
            update_data["started_at"] = datetime.utcnow()

        # Set completed_at when status changes to terminal state
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            update_data["completed_at"] = datetime.utcnow()

        updated = await self.update(test_id, update_data, commit=commit)

        if updated:
            logger.debug(f"Updated QuickTest {test_id} status to {status}")

        return updated

    async def update_result(
        self,
        test_id: str,
        result_data: dict,
        commit: bool = True
    ) -> Optional[QuickTest]:
        """
        Update test result and metrics.

        Args:
            test_id: Test ID
            result_data: Dictionary containing:
                - test_result: Test results (dict)
                - execution_time: Execution time in seconds (float)
                - status: New status (optional)
                - error_message: Error message if failed (optional)
                - metrics_summary: Summary metrics (optional)
            commit: Whether to commit the transaction

        Returns:
            Updated test or None if not found
        """
        updated = await self.update(test_id, result_data, commit=commit)

        if updated:
            logger.debug(
                f"Updated QuickTest {test_id} result "
                f"(status={result_data.get('status')}, "
                f"execution_time={result_data.get('execution_time')})"
            )

        return updated

    async def find_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None
    ) -> List[QuickTest]:
        """
        Find tests by user with pagination.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of records per page
            status: Optional status filter

        Returns:
            List of user's tests
        """
        stmt = select(QuickTest).where(
            QuickTest.user_id == user_id,
            QuickTest.is_deleted == False
        )

        # Apply status filter
        if status:
            stmt = stmt.where(QuickTest.status == status)

        # Order by creation time (most recent first)
        stmt = stmt.order_by(QuickTest.created_at.desc())

        # Apply pagination (convert 1-indexed to 0-indexed)
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)

        result = await self.session.execute(stmt)
        tests = list(result.scalars().all())

        logger.debug(
            f"Found {len(tests)} tests for user {user_id} "
            f"(page={page}, page_size={page_size})"
        )
        return tests

    async def find_timeout_tests(
        self,
        timeout_minutes: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> List[QuickTest]:
        """
        Find timeout tests (status=RUNNING, created >timeout_minutes ago).

        Args:
            timeout_minutes: Timeout threshold in minutes
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of timeout tests
        """
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        stmt = select(QuickTest).where(
            QuickTest.status == "RUNNING",
            QuickTest.created_at < timeout_threshold,
            QuickTest.is_deleted == False
        )

        stmt = stmt.order_by(QuickTest.created_at.asc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        tests = list(result.scalars().all())

        logger.warning(
            f"Found {len(tests)} timeout tests "
            f"(threshold={timeout_minutes} minutes)"
        )
        return tests

    async def find_by_instance(
        self,
        instance_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[QuickTest]:
        """
        Find all tests for a strategy instance.

        Args:
            instance_id: Strategy instance ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of tests for the instance
        """
        stmt = select(QuickTest).where(
            QuickTest.instance_id == instance_id,
            QuickTest.is_deleted == False
        )

        # Apply status filter
        if status:
            stmt = stmt.where(QuickTest.status == status)

        # Order by creation time (most recent first)
        stmt = stmt.order_by(QuickTest.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        tests = list(result.scalars().all())

        logger.debug(
            f"Found {len(tests)} tests for instance {instance_id}"
        )
        return tests

    async def count_by_user_and_status(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> int:
        """
        Count tests by user and optional status.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Number of matching tests
        """
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status

        return await self.count(**filters)

    async def get_recent_tests(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[QuickTest]:
        """
        Get user's most recent tests.

        Args:
            user_id: User ID
            limit: Maximum number of tests to return

        Returns:
            List of recent tests
        """
        return await self.find_by_user(user_id, page=1, page_size=limit)

    async def get_running_tests(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[QuickTest]:
        """
        Get currently running tests.

        Args:
            user_id: Optional user filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of running tests
        """
        stmt = select(QuickTest).where(
            QuickTest.status == "RUNNING",
            QuickTest.is_deleted == False
        )

        if user_id:
            stmt = stmt.where(QuickTest.user_id == user_id)

        stmt = stmt.order_by(QuickTest.started_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        tests = list(result.scalars().all())

        logger.debug(
            f"Found {len(tests)} running tests"
            + (f" for user {user_id}" if user_id else "")
        )
        return tests
