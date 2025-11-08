"""
TDD Tests for Task Model

Test coverage for:
- Task model creation
- Task status transitions
- Task priority handling
- Task metadata
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.database.models.task import Task, TaskType, TaskStatus, TaskPriority


class TestTaskModel:
    """Test Task model."""

    def test_create_task_with_required_fields(self):
        """Test creating a task with required fields only."""
        # ARRANGE & ACT
        task = Task(
            type=TaskType.BACKTEST,
            name="Test Backtest Task",
            status=TaskStatus.PENDING,
            params={"strategy_id": "test_strategy"},
            created_by="test_user"
        )

        # ASSERT
        assert task.type == TaskType.BACKTEST
        assert task.name == "Test Backtest Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL  # Default priority
        assert task.progress == 0.0
        assert task.params == {"strategy_id": "test_strategy"}
        assert task.created_by == "test_user"
        assert task.result is None
        assert task.error is None

    def test_create_task_with_all_fields(self):
        """Test creating a task with all fields."""
        # ARRANGE & ACT
        task = Task(
            type=TaskType.DATA_IMPORT,
            name="Import Stock Data",
            status=TaskStatus.RUNNING,
            priority=TaskPriority.HIGH,
            params={"source": "csv", "file_path": "/data/stocks.csv"},
            progress=45.5,
            current_step="Processing row 4500",
            eta=120,
            result={"imported_rows": 4500},
            created_by="admin"
        )

        # ASSERT
        assert task.type == TaskType.DATA_IMPORT
        assert task.name == "Import Stock Data"
        assert task.status == TaskStatus.RUNNING
        assert task.priority == TaskPriority.HIGH
        assert task.progress == 45.5
        assert task.current_step == "Processing row 4500"
        assert task.eta == 120
        assert task.result == {"imported_rows": 4500}
        assert task.created_by == "admin"

    def test_task_status_enum_values(self):
        """Test TaskStatus enum has all required values."""
        # ASSERT
        assert TaskStatus.PENDING == "PENDING"
        assert TaskStatus.RUNNING == "RUNNING"
        assert TaskStatus.PAUSED == "PAUSED"
        assert TaskStatus.COMPLETED == "COMPLETED"
        assert TaskStatus.FAILED == "FAILED"
        assert TaskStatus.CANCELLED == "CANCELLED"

    def test_task_type_enum_values(self):
        """Test TaskType enum has all required values."""
        # ASSERT
        assert TaskType.BACKTEST == "BACKTEST"
        assert TaskType.OPTIMIZATION == "OPTIMIZATION"
        assert TaskType.DATA_IMPORT == "DATA_IMPORT"
        assert TaskType.DATA_PREPROCESSING == "DATA_PREPROCESSING"
        assert TaskType.FACTOR_BACKTEST == "FACTOR_BACKTEST"
        assert TaskType.CUSTOM_CODE == "CUSTOM_CODE"

    def test_task_priority_enum_values(self):
        """Test TaskPriority enum has correct integer values."""
        # ASSERT
        assert TaskPriority.LOW == 0
        assert TaskPriority.NORMAL == 1
        assert TaskPriority.HIGH == 2
        assert TaskPriority.URGENT == 3

    def test_task_with_error_message(self):
        """Test task can store error message."""
        # ARRANGE & ACT
        task = Task(
            type=TaskType.BACKTEST,
            name="Failed Task",
            status=TaskStatus.FAILED,
            params={},
            created_by="test_user",
            error="Database connection timeout"
        )

        # ASSERT
        assert task.status == TaskStatus.FAILED
        assert task.error == "Database connection timeout"

    def test_task_progress_range(self):
        """Test task progress is within valid range."""
        # ARRANGE & ACT
        task = Task(
            type=TaskType.BACKTEST,
            name="Progress Task",
            status=TaskStatus.RUNNING,
            params={},
            created_by="test_user",
            progress=75.5
        )

        # ASSERT
        assert 0.0 <= task.progress <= 100.0
