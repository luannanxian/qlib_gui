"""
TDD Tests for Import Task API Endpoints

Comprehensive test suite covering:
- POST /api/imports/upload (file upload and task creation)
- POST /api/imports/{task_id}/process (process import task)
- GET /api/imports (list tasks with filtering)
- GET /api/imports/{task_id} (get specific task)
- DELETE /api/imports/{task_id} (soft/hard delete)
- GET /api/imports/active/count (count active tasks)

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Test HTTP status codes and response structure
- Test request validation
- Test error handling
- Test file upload handling
"""

import io
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.import_task import ImportTask, ImportStatus, ImportType
from app.database.repositories.import_task import ImportTaskRepository
from app.modules.data_management.services.import_service import DataImportService


class TestUploadFileEndpoint:
    """Test POST /api/imports/upload endpoint."""

    def test_upload_csv_file_success(
        self,
        client: TestClient,
        tmp_path
    ):
        """Test uploading a CSV file successfully."""
        # ARRANGE
        csv_content = b"date,open,high,low,close,volume\n2024-01-01,100,110,95,105,1000"
        csv_file = io.BytesIO(csv_content)
        csv_file.name = "test_data.csv"

        with patch('app.config.settings.UPLOAD_DIR', str(tmp_path)):
            # ACT
            response = client.post(
                "/api/imports/upload",
                files={"file": ("test_data.csv", csv_file, "text/csv")},
                data={"task_name": "Test CSV Import", "user_id": "user123"}
            )

        # ASSERT
        print(f"\n===== DEBUG =====")
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        print(f"=================\n")
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "Test CSV Import"
        assert data["import_type"] == ImportType.CSV.value
        assert data["original_filename"] == "test_data.csv"
        assert data["status"] == ImportStatus.PENDING.value
        assert data["user_id"] == "user123"
        assert "id" in data
        assert "file_path" in data
        assert data["file_size"] > 0

    def test_upload_excel_file_success(
        self,
        client: TestClient,
        tmp_path
    ):
        """Test uploading an Excel file successfully."""
        # ARRANGE
        excel_content = b"PK\x03\x04"  # Minimal Excel file signature
        excel_file = io.BytesIO(excel_content)

        with patch('app.config.settings.UPLOAD_DIR', str(tmp_path)):
            # ACT
            response = client.post(
                "/api/imports/upload",
                files={"file": ("stocks.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"task_name": "Excel Import"}
            )

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["import_type"] == ImportType.EXCEL.value
        assert data["original_filename"] == "stocks.xlsx"

    def test_upload_without_filename(
        self,
        client: TestClient
    ):
        """Test uploading file without filename."""
        # ARRANGE
        file_content = io.BytesIO(b"test")

        # ACT
        response = client.post(
            "/api/imports/upload",
            files={"file": (None, file_content, "text/csv")}
        )

        # ASSERT
        # FastAPI returns 422 for validation errors
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            assert "Filename is required" in response.json()["detail"]

    def test_upload_unsupported_file_type(
        self,
        client: TestClient
    ):
        """Test uploading unsupported file type."""
        # ARRANGE
        txt_file = io.BytesIO(b"test data")

        # ACT
        response = client.post(
            "/api/imports/upload",
            files={"file": ("data.txt", txt_file, "text/plain")}
        )

        # ASSERT
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_file_exceeds_size_limit(
        self,
        client: TestClient,
        tmp_path
    ):
        """Test uploading file that exceeds size limit."""
        # ARRANGE
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        large_file = io.BytesIO(large_content)

        with patch('app.config.settings.UPLOAD_DIR', str(tmp_path)), \
             patch('app.config.settings.MAX_UPLOAD_SIZE_MB', 100):
            # ACT
            response = client.post(
                "/api/imports/upload",
                files={"file": ("large.csv", large_file, "text/csv")}
            )

        # ASSERT
        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]

    def test_upload_file_with_auto_generated_task_name(
        self,
        client: TestClient,
        tmp_path
    ):
        """Test uploading file without custom task name (auto-generated)."""
        # ARRANGE
        csv_file = io.BytesIO(b"col1,col2\n1,2")

        with patch('app.config.settings.UPLOAD_DIR', str(tmp_path)):
            # ACT
            response = client.post(
                "/api/imports/upload",
                files={"file": ("mydata.csv", csv_file, "text/csv")}
            )

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert "Import mydata.csv" in data["task_name"]


class TestProcessImportTask:
    """Test POST /api/imports/{task_id}/process endpoint."""

    @pytest.mark.asyncio
    async def test_process_pending_task_success(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test processing a pending import task successfully."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Process Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "test.csv",
                "file_path": "/tmp/test.csv",
                "file_size": 1024
            },
            commit=True
        )

        with patch.object(DataImportService, 'process_import', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"success": True, "rows_processed": 100}

            # ACT
            response = client.post(f"/api/imports/{task.id}/process")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task.id)

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)

    def test_process_nonexistent_task(
        self,
        client: TestClient
    ):
        """Test processing non-existent task."""
        # ARRANGE
        fake_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        response = client.post(f"/api/imports/{fake_id}/process")

        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_process_already_completed_task(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test processing already completed task (should fail)."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Already Completed",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.COMPLETED.value,
                "original_filename": "completed.csv",
                "file_path": "/tmp/completed.csv",
                "file_size": 2048
            },
            commit=True
        )

        # ACT
        response = client.post(f"/api/imports/{task.id}/process")

        # ASSERT
        assert response.status_code == 400
        assert "cannot reprocess" in response.json()["detail"]

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_process_failed_task_cannot_retry(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test processing failed task (should fail)."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Failed Task",
                "import_type": ImportType.EXCEL.value,
                "status": ImportStatus.FAILED.value,
                "original_filename": "failed.xlsx",
                "file_path": "/tmp/failed.xlsx",
                "file_size": 4096
            },
            commit=True
        )

        # ACT
        response = client.post(f"/api/imports/{task.id}/process")

        # ASSERT
        assert response.status_code == 400

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)


class TestListImportTasks:
    """Test GET /api/imports endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_tasks(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test listing all import tasks."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "List Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "list.csv",
                "file_path": "/tmp/list.csv",
                "file_size": 512
            },
            commit=True
        )

        # ACT
        response = client.get("/api/imports")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 1
        assert any(item["id"] == str(task.id) for item in data["items"])

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test listing tasks with pagination parameters."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        tasks = []
        for i in range(5):
            task = await repo.create(
                obj_in={
                    "task_name": f"Pagination Test {i}",
                    "import_type": ImportType.CSV.value,
                    "status": ImportStatus.PENDING.value,
                    "original_filename": f"page{i}.csv",
                    "file_path": f"/tmp/page{i}.csv",
                    "file_size": 1024
                },
                commit=True
            )
            tasks.append(task)

        # ACT
        response = client.get("/api/imports?skip=2&limit=2")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2

        # Cleanup
        for task in tasks:
            await repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_status(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test listing tasks filtered by status."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        pending_task = await repo.create(
            obj_in={
                "task_name": "Pending Filter Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "pending.csv",
                "file_path": "/tmp/pending.csv",
                "file_size": 1024
            },
            commit=True
        )

        # ACT
        response = client.get(f"/api/imports?task_status={ImportStatus.PENDING.value}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == ImportStatus.PENDING.value for item in data["items"])
        assert any(item["id"] == str(pending_task.id) for item in data["items"])

        # Cleanup
        await repo.delete(pending_task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_user_id(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test listing tasks filtered by user_id."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        user_task = await repo.create(
            obj_in={
                "task_name": "User Filter Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "user.csv",
                "file_path": "/tmp/user.csv",
                "file_size": 2048,
                "user_id": "test_user_456"
            },
            commit=True
        )

        # ACT
        response = client.get("/api/imports?user_id=test_user_456")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert all(item["user_id"] == "test_user_456" for item in data["items"])
        assert any(item["id"] == str(user_task.id) for item in data["items"])

        # Cleanup
        await repo.delete(user_task.id, soft=False, commit=True)


class TestGetImportTask:
    """Test GET /api/imports/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_success(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test getting a specific import task."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Get Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.COMPLETED.value,
                "original_filename": "get.csv",
                "file_path": "/tmp/get.csv",
                "file_size": 1536
            },
            commit=True
        )

        # ACT
        response = client.get(f"/api/imports/{task.id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task.id)
        assert data["task_name"] == "Get Test"
        assert data["status"] == ImportStatus.COMPLETED.value

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)

    def test_get_nonexistent_task(
        self,
        client: TestClient
    ):
        """Test getting non-existent task."""
        # ARRANGE
        fake_id = "00000000-0000-0000-0000-000000000001"

        # ACT
        response = client.get(f"/api/imports/{fake_id}")

        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDeleteImportTask:
    """Test DELETE /api/imports/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_soft_delete_task_success(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test soft deleting an import task."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Soft Delete Test",
                "import_type": ImportType.EXCEL.value,
                "status": ImportStatus.COMPLETED.value,
                "original_filename": "delete.xlsx",
                "file_path": "/tmp/delete.xlsx",
                "file_size": 3072
            },
            commit=True
        )
        task_id = task.id

        # ACT
        response = client.delete(f"/api/imports/{task_id}")

        # ASSERT
        assert response.status_code == 204

        # Verify task is soft deleted
        deleted_task = await repo.get(task_id, include_deleted=True)
        assert deleted_task is not None
        assert deleted_task.is_deleted is True

        # Cleanup
        await repo.delete(task_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_hard_delete_task_success(
        self,
        client: TestClient,
        db_session: AsyncSession,
        tmp_path
    ):
        """Test hard deleting an import task."""
        # ARRANGE
        file_path = tmp_path / "hard_delete.csv"
        file_path.write_text("test data")

        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Hard Delete Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.COMPLETED.value,
                "original_filename": "hard_delete.csv",
                "file_path": str(file_path),
                "file_size": 9
            },
            commit=True
        )
        task_id = task.id

        # ACT
        response = client.delete(f"/api/imports/{task_id}?hard_delete=true")

        # ASSERT
        assert response.status_code == 204

        # Verify task is hard deleted (not found even with include_deleted)
        hard_deleted_task = await repo.get(task_id, include_deleted=True)
        assert hard_deleted_task is None

        # Verify file is deleted
        assert not file_path.exists()

    def test_delete_nonexistent_task(
        self,
        client: TestClient
    ):
        """Test deleting non-existent task."""
        # ARRANGE
        fake_id = "00000000-0000-0000-0000-000000000002"

        # ACT
        response = client.delete(f"/api/imports/{fake_id}")

        # ASSERT
        assert response.status_code == 404


class TestGetActiveTaskCount:
    """Test GET /api/imports/active/count endpoint."""

    @pytest.mark.asyncio
    async def test_get_active_count(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test getting count of active tasks."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        processing_task = await repo.create(
            obj_in={
                "task_name": "Active Count Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PROCESSING.value,
                "original_filename": "active.csv",
                "file_path": "/tmp/active.csv",
                "file_size": 2048
            },
            commit=True
        )

        # ACT
        response = client.get("/api/imports/active/count")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "active_count" in data
        assert data["active_count"] >= 1

        # Cleanup
        await repo.delete(processing_task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_active_count_excludes_completed(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test active count excludes completed tasks."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        completed_task = await repo.create(
            obj_in={
                "task_name": "Completed Task",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.COMPLETED.value,
                "original_filename": "completed.csv",
                "file_path": "/tmp/completed.csv",
                "file_size": 1024
            },
            commit=True
        )

        # ACT - get count before adding active task
        response_before = client.get("/api/imports/active/count")
        count_before = response_before.json()["active_count"]

        # Add active task
        pending_task = await repo.create(
            obj_in={
                "task_name": "Pending Task",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "pending.csv",
                "file_path": "/tmp/pending.csv",
                "file_size": 512
            },
            commit=True
        )

        response_after = client.get("/api/imports/active/count")
        count_after = response_after.json()["active_count"]

        # ASSERT
        assert count_after > count_before

        # Cleanup
        await repo.delete(completed_task.id, soft=False, commit=True)
        await repo.delete(pending_task.id, soft=False, commit=True)


class TestImportAPIErrorHandling:
    """Test error handling for Import API endpoints."""

    def test_upload_service_error(
        self,
        client: TestClient,
        tmp_path
    ):
        """Test upload endpoint handles service errors gracefully."""
        # ARRANGE
        csv_file = io.BytesIO(b"col1,col2\n1,2")

        with patch('app.config.settings.UPLOAD_DIR', str(tmp_path)), \
             patch.object(DataImportService, 'create_import_task', new_callable=AsyncMock, side_effect=Exception("Service error")):
            # ACT
            response = client.post(
                "/api/imports/upload",
                files={"file": ("error.csv", csv_file, "text/csv")}
            )

        # ASSERT
        assert response.status_code == 500
        assert "Error uploading file" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_process_task_service_error(
        self,
        client: TestClient,
        db_session: AsyncSession
    ):
        """Test process endpoint handles service errors."""
        # ARRANGE
        repo = ImportTaskRepository(db_session)
        task = await repo.create(
            obj_in={
                "task_name": "Service Error Test",
                "import_type": ImportType.CSV.value,
                "status": ImportStatus.PENDING.value,
                "original_filename": "error.csv",
                "file_path": "/tmp/error.csv",
                "file_size": 1024
            },
            commit=True
        )

        with patch.object(DataImportService, 'process_import', new_callable=AsyncMock, side_effect=Exception("Processing error")):
            # ACT
            response = client.post(f"/api/imports/{task.id}/process")

        # ASSERT
        assert response.status_code == 500

        # Cleanup
        await repo.delete(task.id, soft=False, commit=True)


@pytest.mark.asyncio
class TestImportAPIInputValidation:
    """Test input validation for Import API."""

    def test_upload_with_invalid_pagination(
        self,
        client: TestClient
    ):
        """Test list endpoint with invalid pagination parameters."""
        # ACT
        response = client.get("/api/imports?skip=-1&limit=0")

        # ASSERT
        assert response.status_code == 422

    def test_upload_with_invalid_task_id_format(
        self,
        client: TestClient
    ):
        """Test endpoints with invalid UUID format."""
        # ACT
        response = client.get("/api/imports/invalid-uuid")

        # ASSERT
        assert response.status_code in [404, 422]
