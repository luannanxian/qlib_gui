"""
Tests for data import Celery tasks

Coverage target: 80%+

Test Coverage:
- DatabaseTask base class (session management)
- process_data_import task (success, failure, timeout, idempotency)
- validate_import_file task (validation success/failure)
- cleanup_old_imports task (cleanup old tasks and files)
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Create a real Task class for mocking
class FakeTask:
    """Fake Celery Task class"""
    def __init__(self):
        self.request = None

    def retry(self, exc=None, **kwargs):
        """Fake retry method"""
        raise exc

# Create a decorator that returns the function unchanged
def fake_task_decorator(*args, **kwargs):
    """Fake celery task decorator that returns the function unchanged"""
    def decorator(func):
        return func
    # If called without arguments, return the function directly
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

# Mock celery before importing the module
mock_celery = MagicMock()
mock_celery.Task = FakeTask

# Create fake celery_app with task decorator
mock_celery_app = MagicMock()
mock_celery_app.task = fake_task_decorator

mock_celery_signals = MagicMock()
mock_celery_utils = MagicMock()
mock_celery_utils_log = MagicMock()
mock_celery_utils_log.get_task_logger = MagicMock(return_value=MagicMock())

sys.modules['celery'] = mock_celery
sys.modules['celery.signals'] = mock_celery_signals
sys.modules['celery.utils'] = mock_celery_utils
sys.modules['celery.utils.log'] = mock_celery_utils_log

# Patch celery_app before import
with patch('app.celery_app.celery_app', mock_celery_app):
    # This doesn't work in the module scope, we need to patch it differently
    pass

# Actually, let's mock celery_app module
sys.modules['app.celery_app'] = MagicMock(celery_app=mock_celery_app)

from app.database.models.import_task import ImportStatus, ImportType

# Import the module - tasks will be decorated by our fake decorator
import app.modules.data_management.tasks.import_tasks as import_tasks_module

# Get the actual functions (not decorated)
DatabaseTask = import_tasks_module.DatabaseTask
process_data_import = import_tasks_module.process_data_import
validate_import_file = import_tasks_module.validate_import_file
cleanup_old_imports = import_tasks_module.cleanup_old_imports


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_session_maker():
    """Mock async session maker"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_maker = Mock(return_value=mock_session)
    return mock_maker, mock_session


@pytest.fixture
def mock_import_task():
    """Mock ImportTask object"""
    task = Mock()
    task.id = "test-task-id"
    task.status = ImportStatus.PENDING.value
    task.file_path = "/tmp/test_file.csv"
    task.import_type = ImportType.CSV.value
    task.total_rows = 0
    task.processed_rows = 0
    task.progress_percentage = 0.0
    return task


@pytest.fixture
def mock_import_service():
    """Mock DataImportService"""
    service = Mock()

    # Mock import_task_repo
    service.import_task_repo = Mock()
    service.import_task_repo.get = AsyncMock()
    service.import_task_repo.update = AsyncMock()
    service.import_task_repo.delete = AsyncMock()
    service.import_task_repo.find_by_filters = AsyncMock()

    # Mock process_import method
    service.process_import = AsyncMock()
    service.validate_file = AsyncMock()

    return service


@pytest.fixture
def mock_process_result():
    """Mock successful process result"""
    result = Mock()
    result.success = True
    result.rows_processed = 100
    result.rows_skipped = 5
    result.dataset_id = "dataset-123"
    result.errors = []
    return result


@pytest.fixture
def temp_csv_file():
    """Create temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("date,open,high,low,close,volume\n")
        f.write("2024-01-01,100,105,98,102,1000000\n")
        f.write("2024-01-02,102,108,101,107,1200000\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ============================================================================
# DatabaseTask Tests
# ============================================================================


class TestDatabaseTask:
    """Test DatabaseTask base class"""

    def test_database_task_initialization(self):
        """Test DatabaseTask initializes with None session"""
        task = DatabaseTask()
        assert task._session is None

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    def test_get_session_creates_new_session(self, mock_maker):
        """Test get_session creates new session if None"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_maker.return_value = mock_session
        task = DatabaseTask()

        # ACT
        session = task.get_session()

        # ASSERT
        assert session == mock_session
        assert task._session == mock_session
        mock_maker.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    def test_get_session_reuses_existing_session(self, mock_maker):
        """Test get_session reuses existing session"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_maker.return_value = mock_session
        task = DatabaseTask()

        # ACT
        session1 = task.get_session()
        session2 = task.get_session()

        # ASSERT
        assert session1 == session2
        mock_maker.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_close_session_closes_and_resets(self):
        """Test close_session closes session and resets to None"""
        # ARRANGE
        task = DatabaseTask()
        mock_session = AsyncMock()
        task._session = mock_session

        # ACT
        await task.close_session()

        # ASSERT
        mock_session.close.assert_called_once()
        assert task._session is None

    @pytest.mark.asyncio
    async def test_close_session_when_none(self):
        """Test close_session does nothing when session is None"""
        # ARRANGE
        task = DatabaseTask()

        # ACT & ASSERT - should not raise
        await task.close_session()
        assert task._session is None


# ============================================================================
# process_data_import Tests
# ============================================================================


class TestProcessDataImport:
    """Test process_data_import task"""

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_success(
        self, mock_service_class, mock_session_maker, mock_import_task, mock_process_result
    ):
        """Test successful data import processing"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service.import_task_repo.update = AsyncMock()
        mock_service.process_import = AsyncMock(return_value=mock_process_result)
        mock_service_class.return_value = mock_service

        # Create mock task with request
        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/test.csv",
            import_type="csv",
            import_config={"delimiter": ","}
        )

        # ASSERT
        assert result["success"] is True
        assert result["task_id"] == "test-task-id"
        assert result["rows_processed"] == 100
        assert result["rows_skipped"] == 5
        assert result["dataset_id"] == "dataset-123"

        # Verify session was closed
        mock_session.close.assert_called_once()

        # Verify status was updated to PROCESSING
        assert mock_service.import_task_repo.update.call_count == 1
        update_call = mock_service.import_task_repo.update.call_args_list[0]
        assert update_call[1]["id"] == "test-task-id"
        assert update_call[1]["obj_in"]["status"] == ImportStatus.PROCESSING.value

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_task_not_found(
        self, mock_service_class, mock_session_maker
    ):
        """Test processing when task not found in database"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="nonexistent-task",
            file_path="/tmp/test.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is False
        assert result["task_id"] == "nonexistent-task"
        assert len(result["errors"]) == 1
        assert "Task not found" in result["errors"][0]["message"]

        mock_session.close.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_already_completed(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test idempotency - skip if task already completed"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        # Set task to completed status
        mock_import_task.status = ImportStatus.COMPLETED.value

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/test.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is True
        assert result["skipped"] is True
        assert "already" in result["reason"].lower()

        # Verify process_import was NOT called
        assert not hasattr(mock_service, 'process_import') or \
               mock_service.process_import.call_count == 0

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_already_cancelled(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test idempotency - skip if task already cancelled"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        # Set task to cancelled status
        mock_import_task.status = ImportStatus.CANCELLED.value

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/test.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is True
        assert result["skipped"] is True
        assert ImportStatus.CANCELLED.value in result["reason"]

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_processing_failure(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test handling of processing failure"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_result = Mock()
        mock_result.success = False
        mock_result.errors = [{"message": "Invalid data format"}]

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service.import_task_repo.update = AsyncMock()
        mock_service.process_import = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/test.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert result["errors"][0]["message"] == "Invalid data format"

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    @patch('app.modules.data_management.tasks.import_tasks.asyncio.wait_for')
    def test_process_data_import_timeout(
        self, mock_wait_for, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test handling of task timeout"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        # Simulate timeout
        mock_wait_for.side_effect = asyncio.TimeoutError()

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service.import_task_repo.update = AsyncMock()
        mock_service.process_import = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT
        result = process_data_import(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/test.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is False
        assert any("timeout" in err["message"].lower() for err in result["errors"])

        # Verify task was updated to FAILED
        update_calls = [call for call in mock_service.import_task_repo.update.call_args_list
                       if call[1].get("obj_in", {}).get("status") == ImportStatus.FAILED.value]
        assert len(update_calls) > 0

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_database_error_with_retry(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test retry on database connection errors"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service.import_task_repo.update = AsyncMock()

        # Simulate database error
        mock_service.process_import = AsyncMock(
            side_effect=Exception("Database connection lost")
        )
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"
        mock_task.retry = Mock(side_effect=Exception("Retry triggered"))

        # ACT & ASSERT
        with pytest.raises(Exception) as exc_info:
            process_data_import(
                mock_task,
                task_id="test-task-id",
                file_path="/tmp/test.csv",
                import_type="csv"
            )

        # Verify retry was called
        assert mock_task.retry.called

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_general_exception(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test handling of general exceptions"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)
        mock_service.import_task_repo.update = AsyncMock()

        # Simulate general error (not database-related)
        mock_service.process_import = AsyncMock(
            side_effect=ValueError("Invalid configuration")
        )
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT & ASSERT
        with pytest.raises(ValueError):
            process_data_import(
                mock_task,
                task_id="test-task-id",
                file_path="/tmp/test.csv",
                import_type="csv"
            )

        # Verify task was updated to FAILED
        failed_update_calls = [
            call for call in mock_service.import_task_repo.update.call_args_list
            if call[1].get("obj_in", {}).get("status") == ImportStatus.FAILED.value
        ]
        assert len(failed_update_calls) > 0

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_process_data_import_update_status_failure(
        self, mock_service_class, mock_session_maker, mock_import_task
    ):
        """Test handling when updating task status fails"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.get = AsyncMock(return_value=mock_import_task)

        # Make first update succeed, but second fail
        mock_service.import_task_repo.update = AsyncMock(
            side_effect=Exception("Database update failed")
        )
        mock_service_class.return_value = mock_service

        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = "celery-task-123"

        # ACT & ASSERT
        with pytest.raises(Exception):
            process_data_import(
                mock_task,
                task_id="test-task-id",
                file_path="/tmp/test.csv",
                import_type="csv"
            )


# ============================================================================
# validate_import_file Tests
# ============================================================================


class TestValidateImportFile:
    """Test validate_import_file task"""

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_validate_import_file_success(
        self, mock_service_class, mock_session_maker, temp_csv_file
    ):
        """Test successful file validation"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.errors = []
        mock_validation.warnings = ["Missing optional field: description"]
        mock_validation.metadata = {
            "columns": ["date", "open", "high", "low", "close", "volume"],
            "row_count": 2
        }

        mock_service = Mock()
        mock_service.validate_file = AsyncMock(return_value=mock_validation)
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.update = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_task = Mock()

        # ACT
        result = validate_import_file(
            mock_task,
            task_id="test-task-id",
            file_path=temp_csv_file,
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is True
        assert result["task_id"] == "test-task-id"
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 1
        assert result["metadata"]["row_count"] == 2

        # Verify service was called correctly
        mock_service.validate_file.assert_called_once_with(
            temp_csv_file, ImportType.CSV
        )

        # Verify task was updated
        mock_service.import_task_repo.update.assert_called_once()
        update_call = mock_service.import_task_repo.update.call_args
        assert update_call[1]["id"] == "test-task-id"
        assert update_call[1]["obj_in"]["parsing_metadata"] == mock_validation.metadata

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_validate_import_file_validation_errors(
        self, mock_service_class, mock_session_maker
    ):
        """Test file validation with errors"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_validation = Mock()
        mock_validation.is_valid = False
        mock_validation.errors = [
            "Missing required column: date",
            "Invalid data type in column: volume"
        ]
        mock_validation.warnings = []
        mock_validation.metadata = {"columns": ["open", "close"]}

        mock_service = Mock()
        mock_service.validate_file = AsyncMock(return_value=mock_validation)
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.update = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_task = Mock()

        # ACT
        result = validate_import_file(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/invalid.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is False
        assert len(result["errors"]) == 2
        assert "Missing required column" in result["errors"][0]

        # Verify validation errors were stored
        update_call = mock_service.import_task_repo.update.call_args
        assert update_call[1]["obj_in"]["validation_errors"] == mock_validation.errors

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_validate_import_file_exception(
        self, mock_service_class, mock_session_maker
    ):
        """Test handling of validation exception"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_service = Mock()
        mock_service.validate_file = AsyncMock(
            side_effect=Exception("File not found")
        )
        mock_service_class.return_value = mock_service

        mock_task = Mock()

        # ACT
        result = validate_import_file(
            mock_task,
            task_id="test-task-id",
            file_path="/tmp/nonexistent.csv",
            import_type="csv"
        )

        # ASSERT
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "File not found" in result["errors"][0]
        assert result["metadata"] == {}

        mock_session.close.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.modules.data_management.tasks.import_tasks.DataImportService')
    def test_validate_import_file_different_types(
        self, mock_service_class, mock_session_maker
    ):
        """Test validation with different import types"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.errors = []
        mock_validation.warnings = []
        mock_validation.metadata = {}

        mock_service = Mock()
        mock_service.validate_file = AsyncMock(return_value=mock_validation)
        mock_service.import_task_repo = Mock()
        mock_service.import_task_repo.update = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_task = Mock()

        # Test different import types
        for import_type in ["csv", "excel", "json"]:
            # ACT
            result = validate_import_file(
                mock_task,
                task_id="test-task-id",
                file_path=f"/tmp/test.{import_type}",
                import_type=import_type
            )

            # ASSERT
            assert result["success"] is True

            # Verify correct enum was used
            call_args = mock_service.validate_file.call_args
            assert call_args[0][1] == ImportType(import_type)


# ============================================================================
# cleanup_old_imports Tests
# ============================================================================


class TestCleanupOldImports:
    """Test cleanup_old_imports task"""

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_old_imports_success(
        self, mock_remove, mock_exists, mock_repo_class, mock_session_maker
    ):
        """Test successful cleanup of old imports"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value = mock_session

        # Create mock old tasks
        old_task1 = Mock()
        old_task1.id = "task-1"
        old_task1.file_path = "/tmp/old_file1.csv"

        old_task2 = Mock()
        old_task2.id = "task-2"
        old_task2.file_path = "/tmp/old_file2.csv"

        old_task3 = Mock()
        old_task3.id = "task-3"
        old_task3.file_path = None  # Task without file

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(
            return_value=[old_task1, old_task2, old_task3]
        )
        mock_repo.delete = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock file existence
        mock_exists.return_value = True

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=30)

        # ASSERT
        assert result["success"] is True
        assert result["tasks_deleted"] == 3
        assert result["files_deleted"] == 2  # Only 2 tasks had files

        # Verify repository was called correctly
        mock_repo.find_by_filters.assert_called_once()
        filters = mock_repo.find_by_filters.call_args[1]["filters"]
        assert ImportStatus.FAILED.value in filters["status"]
        assert ImportStatus.CANCELLED.value in filters["status"]

        # Verify files were deleted
        assert mock_remove.call_count == 2
        mock_remove.assert_any_call("/tmp/old_file1.csv")
        mock_remove.assert_any_call("/tmp/old_file2.csv")

        # Verify tasks were soft-deleted
        assert mock_repo.delete.call_count == 3

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    def test_cleanup_old_imports_no_tasks(
        self, mock_repo_class, mock_session_maker
    ):
        """Test cleanup when no old tasks exist"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(return_value=[])
        mock_repo_class.return_value = mock_repo

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=30)

        # ASSERT
        assert result["success"] is True
        assert result["tasks_deleted"] == 0
        assert result["files_deleted"] == 0

        mock_session.commit.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_old_imports_file_deletion_error(
        self, mock_remove, mock_exists, mock_repo_class, mock_session_maker
    ):
        """Test cleanup continues when file deletion fails"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value = mock_session

        old_task = Mock()
        old_task.id = "task-1"
        old_task.file_path = "/tmp/locked_file.csv"

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(return_value=[old_task])
        mock_repo.delete = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_exists.return_value = True
        # Simulate file deletion error
        mock_remove.side_effect = OSError("Permission denied")

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=30)

        # ASSERT
        assert result["success"] is True
        assert result["tasks_deleted"] == 1
        assert result["files_deleted"] == 0  # File deletion failed

        # Verify task was still deleted despite file error
        mock_repo.delete.assert_called_once_with("task-1", commit=False)

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    @patch('os.path.exists')
    def test_cleanup_old_imports_file_not_exists(
        self, mock_exists, mock_repo_class, mock_session_maker
    ):
        """Test cleanup when file doesn't exist"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value = mock_session

        old_task = Mock()
        old_task.id = "task-1"
        old_task.file_path = "/tmp/missing_file.csv"

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(return_value=[old_task])
        mock_repo.delete = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # File doesn't exist
        mock_exists.return_value = False

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=30)

        # ASSERT
        assert result["success"] is True
        assert result["tasks_deleted"] == 1
        assert result["files_deleted"] == 0

        # Task should still be deleted
        mock_repo.delete.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    def test_cleanup_old_imports_exception(
        self, mock_repo_class, mock_session_maker
    ):
        """Test handling of exceptions during cleanup"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(
            side_effect=Exception("Database error")
        )
        mock_repo_class.return_value = mock_repo

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=30)

        # ASSERT
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]

        mock_session.close.assert_called_once()

    @patch('app.modules.data_management.tasks.import_tasks.async_session_maker')
    @patch('app.database.repositories.import_task.ImportTaskRepository')
    def test_cleanup_old_imports_custom_days(
        self, mock_repo_class, mock_session_maker
    ):
        """Test cleanup with custom days parameter"""
        # ARRANGE
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value = mock_session

        mock_repo = Mock()
        mock_repo.find_by_filters = AsyncMock(return_value=[])
        mock_repo_class.return_value = mock_repo

        mock_task = Mock()

        # ACT
        result = cleanup_old_imports(mock_task, days=60)

        # ASSERT
        assert result["success"] is True

        # Verify the cutoff date calculation used 60 days
        call_args = mock_repo.find_by_filters.call_args
        filters = call_args[1]["filters"]
        cutoff_date = filters["created_before"]

        # Verify it's approximately 60 days ago (within 1 hour tolerance)
        expected_cutoff = datetime.utcnow() - timedelta(days=60)
        time_diff = abs((cutoff_date - expected_cutoff).total_seconds())
        assert time_diff < 3600  # Less than 1 hour difference
