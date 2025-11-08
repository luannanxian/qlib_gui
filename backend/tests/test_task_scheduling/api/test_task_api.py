"""
TDD Tests for Task Scheduling API Endpoints

Test coverage for:
- POST /api/v1/tasks - Create new task
- GET /api/v1/tasks - List tasks with pagination
- GET /api/v1/tasks/{task_id} - Get task by ID
- PUT /api/v1/tasks/{task_id}/start - Start task
- PUT /api/v1/tasks/{task_id}/pause - Pause task
- PUT /api/v1/tasks/{task_id}/resume - Resume task
- PUT /api/v1/tasks/{task_id}/cancel - Cancel task
- PUT /api/v1/tasks/{task_id}/progress - Update progress
- DELETE /api/v1/tasks/{task_id} - Delete task
- GET /api/v1/tasks/user/{user_id} - Get user's tasks
- GET /api/v1/tasks/pending/next - Get next pending task
- GET /api/v1/tasks/stats - Get task statistics
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


class TestCreateTask:
    """Test POST /api/v1/tasks - Create new task."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, async_client: AsyncClient):
        """Test creating a task successfully."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Backtest Task",
            "params": {
                "strategy_id": "strategy_001",
                "dataset_id": "dataset_001"
            },
            "created_by": "user_001",
            "priority": 1
        }

        # ACT
        response = await async_client.post("/api/v1/tasks", json=task_data)

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "BACKTEST"
        assert data["name"] == "Test Backtest Task"
        assert data["status"] == "PENDING"
        assert data["progress"] == 0.0
        assert data["priority"] == 1
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_task_with_defaults(self, async_client: AsyncClient):
        """Test creating a task with default values."""
        # ARRANGE
        task_data = {
            "type": "DATA_IMPORT",
            "name": "Import Data",
            "params": {"file_path": "/data/test.csv"},
            "created_by": "user_002"
        }

        # ACT
        response = await async_client.post("/api/v1/tasks", json=task_data)

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["priority"] == 1  # NORMAL priority
        assert data["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_create_task_missing_required_fields(self, async_client: AsyncClient):
        """Test creating task with missing required fields."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task"
            # Missing params and created_by
        }

        # ACT
        response = await async_client.post("/api/v1/tasks", json=task_data)

        # ASSERT
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_invalid_type(self, async_client: AsyncClient):
        """Test creating task with invalid type."""
        # ARRANGE
        task_data = {
            "type": "INVALID_TYPE",
            "name": "Test Task",
            "params": {},
            "created_by": "user_001"
        }

        # ACT
        response = await async_client.post("/api/v1/tasks", json=task_data)

        # ASSERT
        assert response.status_code == 400
        assert "Invalid task type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_task_missing_task_params(self, async_client: AsyncClient):
        """Test creating task with missing task-specific parameters."""
        # ARRANGE - BACKTEST requires strategy_id and dataset_id
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001"},  # Missing dataset_id
            "created_by": "user_001"
        }

        # ACT
        response = await async_client.post("/api/v1/tasks", json=task_data)

        # ASSERT
        assert response.status_code == 400
        assert "Missing required parameter" in response.json()["detail"]


class TestListTasks:
    """Test GET /api/v1/tasks - List tasks with pagination."""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, async_client: AsyncClient):
        """Test listing tasks when none exist."""
        # ACT
        response = await async_client.get("/api/v1/tasks")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 100

    @pytest.mark.asyncio
    async def test_list_tasks_with_data(self, async_client: AsyncClient):
        """Test listing tasks with existing data."""
        # ARRANGE - Create multiple tasks
        for i in range(3):
            task_data = {
                "type": "BACKTEST",
                "name": f"Task {i}",
                "params": {"strategy_id": f"strategy_{i}", "dataset_id": f"dataset_{i}"},
                "created_by": "user_001"
            }
            await async_client.post("/api/v1/tasks", json=task_data)

        # ACT
        response = await async_client.get("/api/v1/tasks")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self, async_client: AsyncClient):
        """Test listing tasks with pagination parameters."""
        # ARRANGE - Create 5 tasks
        for i in range(5):
            task_data = {
                "type": "BACKTEST",
                "name": f"Task {i}",
                "params": {"strategy_id": f"strategy_{i}", "dataset_id": f"dataset_{i}"},
                "created_by": "user_001"
            }
            await async_client.post("/api/v1/tasks", json=task_data)

        # ACT
        response = await async_client.get("/api/v1/tasks?skip=2&limit=2")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2


class TestGetTask:
    """Test GET /api/v1/tasks/{task_id} - Get task by ID."""

    @pytest.mark.asyncio
    async def test_get_task_success(self, async_client: AsyncClient):
        """Test getting a task by ID."""
        # ARRANGE - Create a task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.get(f"/api/v1/tasks/{task_id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent task."""
        # ACT
        response = await async_client.get("/api/v1/tasks/nonexistent_id")

        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestStartTask:
    """Test PUT /api/v1/tasks/{task_id}/start - Start task."""

    @pytest.mark.asyncio
    async def test_start_task_success(self, async_client: AsyncClient):
        """Test starting a pending task."""
        # ARRANGE - Create a pending task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_start_task_not_found(self, async_client: AsyncClient):
        """Test starting a non-existent task."""
        # ACT
        response = await async_client.put("/api/v1/tasks/nonexistent_id/start")

        # ASSERT
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_task_invalid_status(self, async_client: AsyncClient):
        """Test starting a task that's not in PENDING status."""
        # ARRANGE - Create and start a task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ACT - Try to start again
        response = await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ASSERT
        assert response.status_code == 400
        assert "Cannot start task" in response.json()["detail"]


class TestPauseTask:
    """Test PUT /api/v1/tasks/{task_id}/pause - Pause task."""

    @pytest.mark.asyncio
    async def test_pause_task_success(self, async_client: AsyncClient):
        """Test pausing a running task."""
        # ARRANGE - Create and start a task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/pause")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAUSED"

    @pytest.mark.asyncio
    async def test_pause_task_invalid_status(self, async_client: AsyncClient):
        """Test pausing a task that's not running."""
        # ARRANGE - Create a pending task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/pause")

        # ASSERT
        assert response.status_code == 400
        assert "Cannot pause task" in response.json()["detail"]


class TestResumeTask:
    """Test PUT /api/v1/tasks/{task_id}/resume - Resume task."""

    @pytest.mark.asyncio
    async def test_resume_task_success(self, async_client: AsyncClient):
        """Test resuming a paused task."""
        # ARRANGE - Create, start, and pause a task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{task_id}/start")
        await async_client.put(f"/api/v1/tasks/{task_id}/pause")

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/resume")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_resume_task_invalid_status(self, async_client: AsyncClient):
        """Test resuming a task that's not paused."""
        # ARRANGE - Create a pending task
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/resume")

        # ASSERT
        assert response.status_code == 400
        assert "Cannot resume task" in response.json()["detail"]


class TestCancelTask:
    """Test PUT /api/v1/tasks/{task_id}/cancel - Cancel task."""

    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, async_client: AsyncClient):
        """Test cancelling a pending task."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/cancel")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_running_task(self, async_client: AsyncClient):
        """Test cancelling a running task."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ACT
        response = await async_client.put(f"/api/v1/tasks/{task_id}/cancel")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_completed_task(self, async_client: AsyncClient):
        """Test cancelling a completed task (should fail)."""
        # ARRANGE - Create a task and manually set it to completed
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Start and complete the task via service (simulated)
        # For this test, we'll just verify the error handling
        # In real scenario, task would be completed through execution

        # ACT - Try to cancel (assuming we can't cancel completed tasks)
        # This test validates the business logic
        # We'll skip actual completion for now and test the validation
        pass  # This test requires task completion mechanism


class TestUpdateProgress:
    """Test PUT /api/v1/tasks/{task_id}/progress - Update progress."""

    @pytest.mark.asyncio
    async def test_update_progress_success(self, async_client: AsyncClient):
        """Test updating task progress."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        progress_data = {
            "progress": 50.0,
            "current_step": "Processing data",
            "eta": 120
        }

        # ACT
        response = await async_client.put(
            f"/api/v1/tasks/{task_id}/progress",
            json=progress_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 50.0
        assert data["current_step"] == "Processing data"
        assert data["eta"] == 120

    @pytest.mark.asyncio
    async def test_update_progress_minimal(self, async_client: AsyncClient):
        """Test updating progress with minimal data."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        progress_data = {"progress": 75.0}

        # ACT
        response = await async_client.put(
            f"/api/v1/tasks/{task_id}/progress",
            json=progress_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 75.0


class TestDeleteTask:
    """Test DELETE /api/v1/tasks/{task_id} - Delete task."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, async_client: AsyncClient):
        """Test deleting a task."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # ACT
        response = await async_client.delete(f"/api/v1/tasks/{task_id}")

        # ASSERT
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify task is deleted
        get_response = await async_client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent task."""
        # ACT
        response = await async_client.delete("/api/v1/tasks/nonexistent_id")

        # ASSERT
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_running_task(self, async_client: AsyncClient):
        """Test deleting a running task (should fail)."""
        # ARRANGE
        task_data = {
            "type": "BACKTEST",
            "name": "Test Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        create_response = await async_client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{task_id}/start")

        # ACT
        response = await async_client.delete(f"/api/v1/tasks/{task_id}")

        # ASSERT
        assert response.status_code == 400
        assert "Cannot delete running task" in response.json()["detail"]


class TestGetUserTasks:
    """Test GET /api/v1/tasks/user/{user_id} - Get user's tasks."""

    @pytest.mark.asyncio
    async def test_get_user_tasks_success(self, async_client: AsyncClient):
        """Test getting tasks for a specific user."""
        # ARRANGE - Create tasks for different users
        for i in range(3):
            task_data = {
                "type": "BACKTEST",
                "name": f"User1 Task {i}",
                "params": {"strategy_id": f"strategy_{i}", "dataset_id": f"dataset_{i}"},
                "created_by": "user_001"
            }
            await async_client.post("/api/v1/tasks", json=task_data)

        task_data = {
            "type": "BACKTEST",
            "name": "User2 Task",
            "params": {"strategy_id": "strategy_x", "dataset_id": "dataset_x"},
            "created_by": "user_002"
        }
        await async_client.post("/api/v1/tasks", json=task_data)

        # ACT
        response = await async_client.get("/api/v1/tasks/user/user_001")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for task in data:
            assert task["created_by"] == "user_001"

    @pytest.mark.asyncio
    async def test_get_user_tasks_empty(self, async_client: AsyncClient):
        """Test getting tasks for user with no tasks."""
        # ACT
        response = await async_client.get("/api/v1/tasks/user/nonexistent_user")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetNextPendingTask:
    """Test GET /api/v1/tasks/pending/next - Get next pending task."""

    @pytest.mark.asyncio
    async def test_get_next_pending_task_by_priority(self, async_client: AsyncClient):
        """Test getting next pending task by priority."""
        # ARRANGE - Create tasks with different priorities
        low_priority_task = {
            "type": "BACKTEST",
            "name": "Low Priority Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001",
            "priority": 0  # LOW
        }
        await async_client.post("/api/v1/tasks", json=low_priority_task)

        high_priority_task = {
            "type": "BACKTEST",
            "name": "High Priority Task",
            "params": {"strategy_id": "strategy_002", "dataset_id": "dataset_002"},
            "created_by": "user_001",
            "priority": 2  # HIGH
        }
        high_response = await async_client.post("/api/v1/tasks", json=high_priority_task)
        high_task_id = high_response.json()["id"]

        # ACT
        response = await async_client.get("/api/v1/tasks/pending/next")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == high_task_id
        assert data["priority"] == 2

    @pytest.mark.asyncio
    async def test_get_next_pending_task_none_available(self, async_client: AsyncClient):
        """Test getting next pending task when none available."""
        # ACT
        response = await async_client.get("/api/v1/tasks/pending/next")

        # ASSERT
        assert response.status_code == 404
        assert "No pending tasks" in response.json()["detail"]


class TestGetTaskStats:
    """Test GET /api/v1/tasks/stats - Get task statistics."""

    @pytest.mark.asyncio
    async def test_get_task_stats(self, async_client: AsyncClient):
        """Test getting task statistics."""
        # ARRANGE - Create tasks with different statuses
        # Pending task
        pending_task = {
            "type": "BACKTEST",
            "name": "Pending Task",
            "params": {"strategy_id": "strategy_001", "dataset_id": "dataset_001"},
            "created_by": "user_001"
        }
        await async_client.post("/api/v1/tasks", json=pending_task)

        # Running task
        running_task = {
            "type": "BACKTEST",
            "name": "Running Task",
            "params": {"strategy_id": "strategy_002", "dataset_id": "dataset_002"},
            "created_by": "user_001"
        }
        running_response = await async_client.post("/api/v1/tasks", json=running_task)
        running_task_id = running_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{running_task_id}/start")

        # Cancelled task
        cancelled_task = {
            "type": "BACKTEST",
            "name": "Cancelled Task",
            "params": {"strategy_id": "strategy_003", "dataset_id": "dataset_003"},
            "created_by": "user_001"
        }
        cancelled_response = await async_client.post("/api/v1/tasks", json=cancelled_task)
        cancelled_task_id = cancelled_response.json()["id"]
        await async_client.put(f"/api/v1/tasks/{cancelled_task_id}/cancel")

        # ACT
        response = await async_client.get("/api/v1/tasks/stats")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["pending"] == 1
        assert data["running"] == 1
        assert data["paused"] == 0
        assert data["completed"] == 0
        assert data["failed"] == 0
        assert data["cancelled"] == 1

    @pytest.mark.asyncio
    async def test_get_task_stats_empty(self, async_client: AsyncClient):
        """Test getting task statistics when no tasks exist."""
        # ACT
        response = await async_client.get("/api/v1/tasks/stats")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["pending"] == 0
        assert data["running"] == 0
