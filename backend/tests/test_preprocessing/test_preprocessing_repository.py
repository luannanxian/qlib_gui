"""
Data Preprocessing Repository Tests

TDD tests for PreprocessingRuleRepository and PreprocessingTaskRepository functionality.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.preprocessing import (
    DataPreprocessingRule, DataPreprocessingTask,
    PreprocessingRuleType, PreprocessingTaskStatus,
    MissingValueMethod, OutlierDetectionMethod, TransformationType
)
from app.database.repositories.preprocessing import (
    PreprocessingRuleRepository, PreprocessingTaskRepository
)


class TestPreprocessingRuleRepository:
    """Test suite for PreprocessingRuleRepository"""

    @pytest.mark.asyncio
    async def test_create_preprocessing_rule(
        self,
        rule_repo: PreprocessingRuleRepository,
        db_session: AsyncSession
    ):
        """Test creating a preprocessing rule"""
        # Arrange
        rule_data = {
            "name": "Fill Missing Values",
            "description": "Fill missing values with mean",
            "rule_type": PreprocessingRuleType.MISSING_VALUE.value,
            "is_template": True,
            "user_id": "user_123",
            "configuration": {
                "method": MissingValueMethod.MEAN_FILL.value,
                "columns": ["price", "volume"]
            },
            "metadata": {
                "affected_columns": ["price", "volume"],
                "tags": ["cleaning"]
            }
        }

        # Act
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Assert
        assert rule.id is not None
        assert rule.name == "Fill Missing Values"
        assert rule.rule_type == PreprocessingRuleType.MISSING_VALUE.value
        assert rule.is_template is True
        assert rule.user_id == "user_123"
        assert rule.usage_count == 0
        assert rule.configuration["method"] == MissingValueMethod.MEAN_FILL.value

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_preprocessing_rule_by_id(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting a preprocessing rule by ID"""
        # Arrange
        rule_data = {
            "name": "Normalize Data",
            "rule_type": PreprocessingRuleType.TRANSFORMATION.value,
            "is_template": True,
            "configuration": {
                "type": TransformationType.NORMALIZE.value,
                "columns": ["price"]
            }
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        retrieved_rule = await rule_repo.get(rule.id)

        # Assert
        assert retrieved_rule is not None
        assert retrieved_rule.id == rule.id
        assert retrieved_rule.name == "Normalize Data"
        assert retrieved_rule.rule_type == PreprocessingRuleType.TRANSFORMATION.value

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_rules_by_user(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting rules by user ID"""
        # Arrange
        rule_data = {
            "name": "User Rule",
            "rule_type": PreprocessingRuleType.FILTERING.value,
            "is_template": True,
            "user_id": "test_user_456",
            "configuration": {"conditions": []}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        rules = await rule_repo.get_by_user("test_user_456")

        # Assert
        assert len(rules) >= 1
        assert any(r.id == rule.id for r in rules)
        assert all(r.user_id == "test_user_456" for r in rules)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_templates_by_type(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting templates by rule type"""
        # Arrange
        rule_data = {
            "name": "Outlier Detection Template",
            "rule_type": PreprocessingRuleType.OUTLIER_DETECTION.value,
            "is_template": True,
            "configuration": {
                "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
                "threshold": 3.0
            }
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        templates = await rule_repo.get_templates(
            rule_type=PreprocessingRuleType.OUTLIER_DETECTION
        )

        # Assert
        assert len(templates) >= 1
        assert any(t.id == rule.id for t in templates)
        assert all(t.is_template is True for t in templates)
        assert all(t.rule_type == PreprocessingRuleType.OUTLIER_DETECTION.value for t in templates)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_increment_usage_count(
        self,
        rule_repo: PreprocessingRuleRepository,
        db_session: AsyncSession
    ):
        """Test incrementing rule usage count"""
        # Arrange
        rule_data = {
            "name": "Usage Test Rule",
            "rule_type": PreprocessingRuleType.TRANSFORMATION.value,
            "is_template": True,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)
        initial_count = rule.usage_count

        # Act
        updated_rule = await rule_repo.increment_usage(rule.id)

        # Assert
        assert updated_rule is not None
        assert updated_rule.usage_count == initial_count + 1

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_count_user_templates(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test counting templates per user (for quota enforcement)"""
        # Arrange
        rule_data = {
            "name": "User Template Count Test",
            "rule_type": PreprocessingRuleType.MISSING_VALUE.value,
            "is_template": True,
            "user_id": "quota_user_789",
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        count = await rule_repo.count_user_templates("quota_user_789")

        # Assert
        assert count >= 1

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_update_preprocessing_rule(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test updating a preprocessing rule"""
        # Arrange
        rule_data = {
            "name": "Original Name",
            "rule_type": PreprocessingRuleType.TRANSFORMATION.value,
            "configuration": {"type": "normalize"}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        updated_rule = await rule_repo.update(
            rule.id,
            {"name": "Updated Name", "description": "New description"},
            commit=True
        )

        # Assert
        assert updated_rule is not None
        assert updated_rule.name == "Updated Name"
        assert updated_rule.description == "New description"

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_soft_delete_preprocessing_rule(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test soft deleting a preprocessing rule"""
        # Arrange
        rule_data = {
            "name": "To Delete",
            "rule_type": PreprocessingRuleType.FILTERING.value,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)
        rule_id = rule.id

        # Act
        deleted = await rule_repo.delete(rule_id, soft=True, commit=True)

        # Assert
        assert deleted is True

        # Verify rule is not returned without include_deleted
        normal_get = await rule_repo.get(rule_id, include_deleted=False)
        assert normal_get is None

        # Verify rule is returned with include_deleted
        deleted_rule = await rule_repo.get(rule_id, include_deleted=True)
        assert deleted_rule is not None
        assert deleted_rule.is_deleted is True

        # Cleanup
        await rule_repo.delete(rule_id, soft=False, commit=True)


class TestPreprocessingTaskRepository:
    """Test suite for PreprocessingTaskRepository"""

    @pytest.mark.asyncio
    async def test_create_preprocessing_task(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test creating a preprocessing task"""
        # Arrange - First create a dataset
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Missing Value Task",
            "status": PreprocessingTaskStatus.PENDING.value,
            "dataset_id": dataset.id,
            "execution_config": {
                "method": MissingValueMethod.MEAN_FILL.value,
                "columns": ["price"]
            },
            "total_operations": 1,
            "input_row_count": 1000
        }

        # Act
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Assert
        assert task.id is not None
        assert task.task_name == "Missing Value Task"
        assert task.status == PreprocessingTaskStatus.PENDING.value
        assert task.dataset_id == dataset.id
        assert task.progress_percentage == 0.0
        assert task.error_count == 0

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_tasks_by_dataset(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test getting tasks by dataset ID"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Dataset Task Test",
            "status": PreprocessingTaskStatus.PENDING.value,
            "dataset_id": dataset.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        tasks = await task_repo.get_by_dataset(dataset.id)

        # Assert
        assert len(tasks) >= 1
        assert any(t.id == task.id for t in tasks)
        assert all(t.dataset_id == dataset.id for t in tasks)

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test getting tasks by status"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Status Task Test",
            "status": PreprocessingTaskStatus.RUNNING.value,
            "dataset_id": dataset.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        running_tasks = await task_repo.get_by_status(PreprocessingTaskStatus.RUNNING)

        # Assert
        assert len(running_tasks) >= 1
        assert any(t.id == task.id for t in running_tasks)
        assert all(t.status == PreprocessingTaskStatus.RUNNING.value for t in running_tasks)

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_update_task_progress(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test updating task progress"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Progress Task",
            "status": PreprocessingTaskStatus.RUNNING.value,
            "dataset_id": dataset.id,
            "execution_config": {},
            "total_operations": 10
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        task.update_progress(completed=5, total=10)
        await db_session.commit()
        await db_session.refresh(task)

        # Assert
        assert task.completed_operations == 5
        assert task.total_operations == 10
        assert task.progress_percentage == 50.0

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_update_task_status(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test updating task status and results"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Status Update Task",
            "status": PreprocessingTaskStatus.RUNNING.value,
            "dataset_id": dataset.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        updated_task = await task_repo.update(
            task.id,
            {
                "status": PreprocessingTaskStatus.COMPLETED.value,
                "output_row_count": 900,
                "rows_affected": 100,
                "execution_results": {"operations_applied": ["mean_fill"]}
            },
            commit=True
        )

        # Assert
        assert updated_task is not None
        assert updated_task.status == PreprocessingTaskStatus.COMPLETED.value
        assert updated_task.output_row_count == 900
        assert updated_task.rows_affected == 100

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_count_tasks_by_status(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test counting tasks by status"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Count Task",
            "status": PreprocessingTaskStatus.PENDING.value,
            "dataset_id": dataset.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        count = await task_repo.count_by_status(PreprocessingTaskStatus.PENDING)

        # Assert
        assert count >= 1

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_user_templates(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting user templates"""
        # Arrange
        rule_data = {
            "name": "User Template",
            "rule_type": PreprocessingRuleType.MISSING_VALUE.value,
            "is_template": True,
            "user_id": "template_user_123",
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        templates = await rule_repo.get_user_templates("template_user_123")

        # Assert
        assert len(templates) >= 1
        assert all(t.is_template is True for t in templates)
        assert all(t.user_id == "template_user_123" for t in templates)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_by_type(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting rules by type"""
        # Arrange
        rule_data = {
            "name": "Type Test Rule",
            "rule_type": PreprocessingRuleType.TRANSFORMATION.value,
            "is_template": True,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        rules = await rule_repo.get_by_type(PreprocessingRuleType.TRANSFORMATION)

        # Assert
        assert len(rules) >= 1
        assert all(r.rule_type == PreprocessingRuleType.TRANSFORMATION.value for r in rules)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_popular_templates(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test getting popular templates"""
        # Arrange
        rule_data = {
            "name": "Popular Template",
            "rule_type": PreprocessingRuleType.OUTLIER_DETECTION.value,
            "is_template": True,
            "usage_count": 10,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        popular = await rule_repo.get_popular_templates(limit=5)

        # Assert
        assert len(popular) >= 1
        assert all(p.is_template is True for p in popular)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_search_templates(
        self,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test searching templates"""
        # Arrange
        rule_data = {
            "name": "Searchable Template",
            "description": "A template for outlier detection",
            "rule_type": PreprocessingRuleType.OUTLIER_DETECTION.value,
            "is_template": True,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        # Act
        results = await rule_repo.search_templates("outlier")

        # Assert
        assert len(results) >= 1
        assert any(r.id == rule.id for r in results)

        # Cleanup
        await rule_repo.delete(rule.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_by_rule(
        self,
        task_repo: PreprocessingTaskRepository,
        rule_repo: PreprocessingRuleRepository,
        db_session: AsyncSession
    ):
        """Test getting tasks by rule ID"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        rule_data = {
            "name": "Test Rule",
            "rule_type": PreprocessingRuleType.FILTERING.value,
            "configuration": {}
        }
        rule = await rule_repo.create(obj_in=rule_data, commit=True)

        task_data = {
            "task_name": "Rule Task",
            "status": PreprocessingTaskStatus.PENDING.value,
            "dataset_id": dataset.id,
            "rule_id": rule.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        tasks = await task_repo.get_by_rule(rule.id)

        # Assert
        assert len(tasks) >= 1
        assert all(t.rule_id == rule.id for t in tasks)

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await rule_repo.delete(rule.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_active_tasks(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test getting active tasks"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Active Task",
            "status": PreprocessingTaskStatus.RUNNING.value,
            "dataset_id": dataset.id,
            "execution_config": {}
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        active_tasks = await task_repo.get_active_tasks()

        # Assert
        assert len(active_tasks) >= 1
        assert any(t.id == task.id for t in active_tasks)

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_task_statistics(
        self,
        task_repo: PreprocessingTaskRepository,
        db_session: AsyncSession
    ):
        """Test getting task statistics"""
        # Arrange
        from app.database.models.dataset import Dataset, DatasetStatus, DataSource
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/tmp/test.csv",
            status=DatasetStatus.VALID.value
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        task_data = {
            "task_name": "Stats Task",
            "status": PreprocessingTaskStatus.COMPLETED.value,
            "dataset_id": dataset.id,
            "execution_config": {},
            "execution_time_seconds": 10.5
        }
        task = await task_repo.create(obj_in=task_data, commit=True)

        # Act
        stats = await task_repo.get_task_statistics()

        # Assert
        assert "total" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "running" in stats
        assert "average_execution_time" in stats
        assert stats["total"] >= 1

        # Cleanup
        await task_repo.delete(task.id, soft=False, commit=True)
        await db_session.delete(dataset)
        await db_session.commit()
