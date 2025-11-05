"""
Tests for Database Repositories

This module contains integration tests for repository classes.
"""

import pytest
from typing import Dict, Any

from app.database.models import Dataset, ChartConfig, UserPreferences
from app.database.repositories import (
    DatasetRepository,
    ChartRepository,
    UserPreferencesRepository,
)


class TestDatasetRepository:
    """Tests for DatasetRepository"""

    @pytest.mark.asyncio
    async def test_create_dataset(self, dataset_repo: DatasetRepository):
        """Test creating a dataset"""
        dataset_data = {
            "name": "New Dataset",
            "source": "local",
            "file_path": "/path/to/data.csv",
            "status": "valid",
            "row_count": 500,
            "columns": ["col1", "col2"],
            "metadata": {"test": "data"}
        }

        dataset = await dataset_repo.create(dataset_data)

        assert dataset.id is not None
        assert dataset.name == "New Dataset"
        assert dataset.source == "local"
        assert dataset.row_count == 500
        assert dataset.created_at is not None

    @pytest.mark.asyncio
    async def test_get_dataset(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test getting a dataset by ID"""
        dataset = await dataset_repo.get(sample_dataset.id)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self, dataset_repo: DatasetRepository):
        """Test getting a non-existent dataset"""
        dataset = await dataset_repo.get("non-existent-id")
        assert dataset is None

    @pytest.mark.asyncio
    async def test_get_by_name(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test getting a dataset by name"""
        dataset = await dataset_repo.get_by_name(sample_dataset.name)

        assert dataset is not None
        assert dataset.name == sample_dataset.name

    @pytest.mark.asyncio
    async def test_get_by_source(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test getting datasets by source"""
        datasets = await dataset_repo.get_by_source("local")

        assert len(datasets) > 0
        assert all(d.source == "local" for d in datasets)

    @pytest.mark.asyncio
    async def test_get_by_status(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test getting datasets by status"""
        datasets = await dataset_repo.get_by_status("valid")

        assert len(datasets) > 0
        assert all(d.status == "valid" for d in datasets)

    @pytest.mark.asyncio
    async def test_search_by_name(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test searching datasets by name"""
        results = await dataset_repo.search_by_name("Test")

        assert len(results) > 0
        assert any("Test" in d.name for d in results)

    @pytest.mark.asyncio
    async def test_update_dataset(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test updating a dataset"""
        updated = await dataset_repo.update(
            sample_dataset.id,
            {"status": "invalid", "row_count": 2000}
        )

        assert updated is not None
        assert updated.status == "invalid"
        assert updated.row_count == 2000

    @pytest.mark.asyncio
    async def test_delete_dataset_soft(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test soft deleting a dataset"""
        success = await dataset_repo.delete(sample_dataset.id, soft=True)
        assert success is True

        # Should not be found with default query
        dataset = await dataset_repo.get(sample_dataset.id)
        assert dataset is None

        # Should be found when including deleted
        dataset = await dataset_repo.get(sample_dataset.id, include_deleted=True)
        assert dataset is not None
        assert dataset.is_deleted is True

    @pytest.mark.asyncio
    async def test_count_datasets(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test counting datasets"""
        count = await dataset_repo.count()
        assert count > 0

    @pytest.mark.asyncio
    async def test_get_statistics(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test getting dataset statistics"""
        stats = await dataset_repo.get_statistics()

        assert "total" in stats
        assert "by_source" in stats
        assert "by_status" in stats
        assert stats["total"] > 0


class TestChartRepository:
    """Tests for ChartRepository"""

    @pytest.mark.asyncio
    async def test_create_chart(self, chart_repo: ChartRepository, sample_dataset: Dataset):
        """Test creating a chart"""
        chart_data = {
            "name": "New Chart",
            "chart_type": "line",
            "dataset_id": sample_dataset.id,
            "config": {"x": "date", "y": "value"},
            "description": "Test chart"
        }

        chart = await chart_repo.create(chart_data)

        assert chart.id is not None
        assert chart.name == "New Chart"
        assert chart.chart_type == "line"
        assert chart.dataset_id == sample_dataset.id

    @pytest.mark.asyncio
    async def test_get_by_dataset(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test getting charts by dataset"""
        charts = await chart_repo.get_by_dataset(sample_chart.dataset_id)

        assert len(charts) > 0
        assert all(c.dataset_id == sample_chart.dataset_id for c in charts)

    @pytest.mark.asyncio
    async def test_get_by_type(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test getting charts by type"""
        charts = await chart_repo.get_by_type("kline")

        assert len(charts) > 0
        assert all(c.chart_type == "kline" for c in charts)

    @pytest.mark.asyncio
    async def test_count_by_dataset(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test counting charts by dataset"""
        count = await chart_repo.count_by_dataset(sample_chart.dataset_id)
        assert count > 0

    @pytest.mark.asyncio
    async def test_search_by_name(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test searching charts by name"""
        results = await chart_repo.search_by_name("Test")

        assert len(results) > 0
        assert any("Test" in c.name for c in results)

    @pytest.mark.asyncio
    async def test_duplicate_chart(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test duplicating a chart"""
        duplicate = await chart_repo.duplicate_chart(
            sample_chart.id,
            "Duplicated Chart"
        )

        assert duplicate is not None
        assert duplicate.id != sample_chart.id
        assert duplicate.name == "Duplicated Chart"
        assert duplicate.dataset_id == sample_chart.dataset_id
        assert duplicate.chart_type == sample_chart.chart_type

    @pytest.mark.asyncio
    async def test_get_statistics(self, chart_repo: ChartRepository, sample_chart: ChartConfig):
        """Test getting chart statistics"""
        stats = await chart_repo.get_statistics()

        assert "total" in stats
        assert "by_type" in stats
        assert stats["total"] > 0


class TestUserPreferencesRepository:
    """Tests for UserPreferencesRepository"""

    @pytest.mark.asyncio
    async def test_create_user_prefs(self, user_prefs_repo: UserPreferencesRepository):
        """Test creating user preferences"""
        prefs_data = {
            "user_id": "new-user",
            "mode": "expert",
            "language": "zh",
            "theme": "dark",
            "show_tooltips": False,
            "completed_guides": [],
            "settings": {}
        }

        prefs = await user_prefs_repo.create(prefs_data)

        assert prefs.id is not None
        assert prefs.user_id == "new-user"
        assert prefs.mode == "expert"

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test getting preferences by user ID"""
        prefs = await user_prefs_repo.get_by_user_id(sample_user_prefs.user_id)

        assert prefs is not None
        assert prefs.user_id == sample_user_prefs.user_id

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test get_or_create with existing preferences"""
        prefs, created = await user_prefs_repo.get_or_create(sample_user_prefs.user_id)

        assert prefs is not None
        assert created is False
        assert prefs.id == sample_user_prefs.id

    @pytest.mark.asyncio
    async def test_get_or_create_new(self, user_prefs_repo: UserPreferencesRepository):
        """Test get_or_create with new user"""
        prefs, created = await user_prefs_repo.get_or_create(
            "brand-new-user",
            defaults={"mode": "expert", "language": "zh"}
        )

        assert prefs is not None
        assert created is True
        assert prefs.user_id == "brand-new-user"
        assert prefs.mode == "expert"

    @pytest.mark.asyncio
    async def test_update_mode(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test updating user mode"""
        updated = await user_prefs_repo.update_mode(sample_user_prefs.user_id, "expert")

        assert updated is not None
        assert updated.mode == "expert"

    @pytest.mark.asyncio
    async def test_update_language(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test updating language"""
        updated = await user_prefs_repo.update_language(sample_user_prefs.user_id, "zh")

        assert updated is not None
        assert updated.language == "zh"

    @pytest.mark.asyncio
    async def test_update_theme(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test updating theme"""
        updated = await user_prefs_repo.update_theme(sample_user_prefs.user_id, "dark")

        assert updated is not None
        assert updated.theme == "dark"

    @pytest.mark.asyncio
    async def test_toggle_tooltips(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test toggling tooltips"""
        original_value = sample_user_prefs.show_tooltips
        updated = await user_prefs_repo.toggle_tooltips(sample_user_prefs.user_id)

        assert updated is not None
        assert updated.show_tooltips != original_value

    @pytest.mark.asyncio
    async def test_add_completed_guide(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test adding a completed guide"""
        updated = await user_prefs_repo.add_completed_guide(
            sample_user_prefs.user_id,
            "intro-tour"
        )

        assert updated is not None
        assert "intro-tour" in updated.completed_guides

    @pytest.mark.asyncio
    async def test_remove_completed_guide(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test removing a completed guide"""
        # First add a guide
        await user_prefs_repo.add_completed_guide(sample_user_prefs.user_id, "test-guide")

        # Then remove it
        updated = await user_prefs_repo.remove_completed_guide(
            sample_user_prefs.user_id,
            "test-guide"
        )

        assert updated is not None
        assert "test-guide" not in updated.completed_guides

    @pytest.mark.asyncio
    async def test_has_completed_guide(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test checking if guide is completed"""
        # Add a guide
        await user_prefs_repo.add_completed_guide(sample_user_prefs.user_id, "test-guide")

        # Check if it exists
        has_completed = await user_prefs_repo.has_completed_guide(
            sample_user_prefs.user_id,
            "test-guide"
        )

        assert has_completed is True

        # Check for non-existent guide
        has_not_completed = await user_prefs_repo.has_completed_guide(
            sample_user_prefs.user_id,
            "non-existent-guide"
        )

        assert has_not_completed is False

    @pytest.mark.asyncio
    async def test_update_settings(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test updating custom settings"""
        updated = await user_prefs_repo.update_settings(
            sample_user_prefs.user_id,
            {"auto_save": True, "chart_type": "kline"}
        )

        assert updated is not None
        assert updated.settings["auto_save"] is True
        assert updated.settings["chart_type"] == "kline"

    @pytest.mark.asyncio
    async def test_get_setting(self, user_prefs_repo: UserPreferencesRepository, sample_user_prefs: UserPreferences):
        """Test getting a specific setting"""
        # First set a setting
        await user_prefs_repo.update_settings(
            sample_user_prefs.user_id,
            {"test_key": "test_value"}
        )

        # Then retrieve it
        value = await user_prefs_repo.get_setting(
            sample_user_prefs.user_id,
            "test_key"
        )

        assert value == "test_value"

        # Test default value
        default_value = await user_prefs_repo.get_setting(
            sample_user_prefs.user_id,
            "non_existent_key",
            default="default"
        )

        assert default_value == "default"


class TestBaseRepositoryFeatures:
    """Tests for BaseRepository common features"""

    @pytest.mark.asyncio
    async def test_bulk_create(self, dataset_repo: DatasetRepository):
        """Test bulk creating datasets"""
        datasets_data = [
            {
                "name": f"Dataset {i}",
                "source": "local",
                "file_path": f"/path/{i}.csv",
                "status": "valid",
                "row_count": 100 * i,
                "columns": ["col1"],
                "metadata": {}
            }
            for i in range(5)
        ]

        datasets = await dataset_repo.bulk_create(datasets_data)

        assert len(datasets) == 5
        assert all(d.id is not None for d in datasets)

    @pytest.mark.asyncio
    async def test_restore_deleted(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test restoring a soft-deleted record"""
        # Delete the dataset
        await dataset_repo.delete(sample_dataset.id, soft=True)

        # Restore it
        restored = await dataset_repo.restore(sample_dataset.id)

        assert restored is not None
        assert restored.is_deleted is False
        assert restored.deleted_at is None

    @pytest.mark.asyncio
    async def test_exists(self, dataset_repo: DatasetRepository, sample_dataset: Dataset):
        """Test checking if a record exists"""
        exists = await dataset_repo.exists(sample_dataset.id)
        assert exists is True

        not_exists = await dataset_repo.exists("non-existent-id")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_pagination(self, dataset_repo: DatasetRepository):
        """Test pagination functionality"""
        # Create multiple datasets
        datasets_data = [
            {
                "name": f"Dataset {i}",
                "source": "local",
                "file_path": f"/path/{i}.csv",
                "status": "valid",
                "row_count": 100,
                "columns": [],
                "metadata": {}
            }
            for i in range(15)
        ]
        await dataset_repo.bulk_create(datasets_data)

        # Get first page
        page1 = await dataset_repo.get_multi(skip=0, limit=10)
        assert len(page1) == 10

        # Get second page
        page2 = await dataset_repo.get_multi(skip=10, limit=10)
        assert len(page2) == 5

        # Ensure no overlap
        page1_ids = {d.id for d in page1}
        page2_ids = {d.id for d in page2}
        assert page1_ids.isdisjoint(page2_ids)
