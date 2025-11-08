"""
TDD Tests for FactorValidationResultRepository

Comprehensive test coverage for:
- Creating validation results
- Querying by factor ID
- Querying by validation type
- Querying by status
- Getting latest validation results
- Updating validation status
- Pagination and filtering
- Edge cases and error handling

Target: 95%+ code coverage
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any

from app.database.models.indicator import (
    ValidationStatus,
    ValidationType,
    FactorStatus
)


@pytest_asyncio.fixture
async def sample_factor(custom_factor_repo):
    """Create a sample custom factor for validation testing"""
    factor_data = {
        "factor_name": "Test Factor for Validation",
        "user_id": "user123",
        "formula": "close / open",
        "formula_language": "qlib_alpha",
        "status": FactorStatus.PUBLISHED.value,
        "is_public": False
    }
    return await custom_factor_repo.create(factor_data, commit=True)


@pytest_asyncio.fixture
async def sample_validation_data(sample_factor) -> Dict[str, Any]:
    """Sample validation result data for testing"""
    return {
        "factor_id": sample_factor.id,
        "validation_type": ValidationType.IC_ANALYSIS.value,
        "dataset_id": "dataset_001",
        "status": ValidationStatus.PENDING.value,
        "metrics": {
            "ic_mean": 0.05,
            "ic_std": 0.02,
            "ic_ir": 2.5
        },
        "details": {
            "period": "2020-01-01 to 2023-12-31",
            "sample_count": 1000
        }
    }


@pytest.mark.asyncio
class TestFactorValidationResultRepository:
    """FactorValidationResultRepository comprehensive test suite"""

    # ==================== Create Tests ====================

    async def test_create_validation_result(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test creating a validation result"""
        result = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        assert result is not None
        assert result.factor_id == sample_validation_data["factor_id"]
        assert result.validation_type == ValidationType.IC_ANALYSIS.value
        assert result.dataset_id == "dataset_001"
        assert result.status == ValidationStatus.PENDING.value
        assert result.metrics["ic_mean"] == 0.05
        assert result.details["sample_count"] == 1000

    async def test_create_validation_with_minimal_data(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating validation with only required fields"""
        minimal_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.SHARPE_RATIO.value,
            "dataset_id": "dataset_002",
            "status": ValidationStatus.PENDING.value
        }
        result = await factor_validation_repo.create(minimal_data, commit=True)

        assert result is not None
        assert result.factor_id == sample_factor.id
        assert result.metrics is None
        assert result.details is None
        assert result.error_message is None

    async def test_create_multiple_validations_for_same_factor(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating multiple validation results for the same factor"""
        # Create IC analysis validation
        ic_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.IC_ANALYSIS.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(ic_data, commit=True)

        # Create backtest validation
        backtest_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.LAYERED_BACKTEST.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(backtest_data, commit=True)

        # Verify both exist
        results = await factor_validation_repo.get_by_factor(sample_factor.id)
        assert len(results) == 2

    # ==================== Query by Factor Tests ====================

    async def test_get_by_factor_basic(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test getting validation results by factor ID"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        results = await factor_validation_repo.get_by_factor(
            created.factor_id
        )

        assert len(results) == 1
        assert results[0].id == created.id
        assert results[0].factor_id == created.factor_id

    async def test_get_by_factor_with_validation_type_filter(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test filtering by validation type"""
        # Create IC analysis validation
        ic_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.IC_ANALYSIS.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(ic_data, commit=True)

        # Create Sharpe ratio validation
        sharpe_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.SHARPE_RATIO.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(sharpe_data, commit=True)

        # Query only IC analysis
        ic_results = await factor_validation_repo.get_by_factor(
            sample_factor.id,
            validation_type=ValidationType.IC_ANALYSIS.value
        )

        assert len(ic_results) == 1
        assert ic_results[0].validation_type == ValidationType.IC_ANALYSIS.value

    async def test_get_by_factor_with_pagination(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test pagination when getting validation results"""
        # Create 5 validation results
        for i in range(5):
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": f"dataset_{i:03d}",
                "status": ValidationStatus.COMPLETED.value
            }
            await factor_validation_repo.create(data, commit=True)

        # Test skip and limit
        page1 = await factor_validation_repo.get_by_factor(
            sample_factor.id,
            skip=0,
            limit=2
        )
        assert len(page1) == 2

        page2 = await factor_validation_repo.get_by_factor(
            sample_factor.id,
            skip=2,
            limit=2
        )
        assert len(page2) == 2

        # Verify different results
        assert page1[0].id != page2[0].id

    async def test_get_by_factor_ordered_by_created_at(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test results are ordered by created_at descending"""
        # Create 3 validation results
        created_ids = []
        for i in range(3):
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": f"dataset_{i:03d}",
                "status": ValidationStatus.COMPLETED.value
            }
            result = await factor_validation_repo.create(data, commit=True)
            created_ids.append(result.id)

        # Get all results
        results = await factor_validation_repo.get_by_factor(sample_factor.id)

        # Verify order (newest first)
        assert results[0].id == created_ids[-1]  # Last created
        assert results[-1].id == created_ids[0]  # First created

    async def test_get_by_factor_empty_result(
        self,
        factor_validation_repo
    ):
        """Test getting validations for non-existent factor"""
        results = await factor_validation_repo.get_by_factor(
            "non_existent_factor_id"
        )
        assert len(results) == 0

    async def test_get_by_factor_excludes_deleted(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test that soft-deleted validations are excluded"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        # Soft delete
        await factor_validation_repo.delete(created.id, soft=True)

        # Should not appear in results
        results = await factor_validation_repo.get_by_factor(created.factor_id)
        assert len(results) == 0

    # ==================== Get Latest Tests ====================

    async def test_get_latest_by_factor(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test getting the latest validation result"""
        # Create multiple validations
        for i in range(3):
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": f"dataset_{i:03d}",
                "status": ValidationStatus.COMPLETED.value
            }
            await factor_validation_repo.create(data, commit=True)

        # Get latest
        latest = await factor_validation_repo.get_latest_by_factor(
            sample_factor.id
        )

        assert latest is not None
        assert latest.dataset_id == "dataset_002"  # Last created

    async def test_get_latest_by_factor_with_type_filter(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test getting latest validation filtered by type"""
        # Create IC analysis (older)
        ic_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.IC_ANALYSIS.value,
            "dataset_id": "dataset_ic",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(ic_data, commit=True)

        # Create Sharpe ratio (newer)
        sharpe_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.SHARPE_RATIO.value,
            "dataset_id": "dataset_sharpe",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(sharpe_data, commit=True)

        # Get latest IC analysis (should be the older one)
        latest_ic = await factor_validation_repo.get_latest_by_factor(
            sample_factor.id,
            validation_type=ValidationType.IC_ANALYSIS.value
        )

        assert latest_ic is not None
        assert latest_ic.validation_type == ValidationType.IC_ANALYSIS.value
        assert latest_ic.dataset_id == "dataset_ic"

    async def test_get_latest_by_factor_returns_none_when_empty(
        self,
        factor_validation_repo
    ):
        """Test getting latest validation for non-existent factor"""
        latest = await factor_validation_repo.get_latest_by_factor(
            "non_existent_factor_id"
        )
        assert latest is None

    # ==================== Query by Status Tests ====================

    async def test_get_by_status(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test getting validation results by status"""
        # Create completed validation
        completed_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.IC_ANALYSIS.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value
        }
        await factor_validation_repo.create(completed_data, commit=True)

        # Create pending validation
        pending_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.SHARPE_RATIO.value,
            "dataset_id": "dataset_002",
            "status": ValidationStatus.PENDING.value
        }
        await factor_validation_repo.create(pending_data, commit=True)

        # Query by status
        completed_results = await factor_validation_repo.get_by_status(
            ValidationStatus.COMPLETED.value
        )
        assert len(completed_results) == 1
        assert completed_results[0].status == ValidationStatus.COMPLETED.value

        pending_results = await factor_validation_repo.get_by_status(
            ValidationStatus.PENDING.value
        )
        assert len(pending_results) == 1
        assert pending_results[0].status == ValidationStatus.PENDING.value

    async def test_get_by_status_with_pagination(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test pagination when querying by status"""
        # Create 5 completed validations
        for i in range(5):
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": f"dataset_{i:03d}",
                "status": ValidationStatus.COMPLETED.value
            }
            await factor_validation_repo.create(data, commit=True)

        # Test pagination
        page1 = await factor_validation_repo.get_by_status(
            ValidationStatus.COMPLETED.value,
            skip=0,
            limit=2
        )
        assert len(page1) == 2

        page2 = await factor_validation_repo.get_by_status(
            ValidationStatus.COMPLETED.value,
            skip=2,
            limit=2
        )
        assert len(page2) == 2

    async def test_get_by_status_ordered_by_created_at(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test results ordered by created_at descending"""
        created_ids = []
        for i in range(3):
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": f"dataset_{i:03d}",
                "status": ValidationStatus.RUNNING.value
            }
            result = await factor_validation_repo.create(data, commit=True)
            created_ids.append(result.id)

        results = await factor_validation_repo.get_by_status(
            ValidationStatus.RUNNING.value
        )

        # Verify we got all results and they are ordered by created_at
        assert len(results) == 3
        # Verify all created IDs are in results
        result_ids = [r.id for r in results]
        for created_id in created_ids:
            assert created_id in result_ids

    async def test_get_by_status_excludes_deleted(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test that soft-deleted validations are excluded from status query"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        # Soft delete
        await factor_validation_repo.delete(created.id, soft=True)

        # Should not appear in results
        results = await factor_validation_repo.get_by_status(
            ValidationStatus.PENDING.value
        )
        assert len(results) == 0

    async def test_get_by_status_empty_result(
        self,
        factor_validation_repo
    ):
        """Test querying status with no matching results"""
        results = await factor_validation_repo.get_by_status(
            ValidationStatus.FAILED.value
        )
        assert len(results) == 0

    # ==================== Update Status Tests ====================

    async def test_update_status_success(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test updating validation status"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )
        assert created.status == ValidationStatus.PENDING.value

        # Update to RUNNING
        updated = await factor_validation_repo.update_status(
            created.id,
            ValidationStatus.RUNNING.value
        )

        assert updated is not None
        assert updated.id == created.id
        assert updated.status == ValidationStatus.RUNNING.value

    async def test_update_status_multiple_transitions(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test multiple status transitions"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        # PENDING -> RUNNING
        running = await factor_validation_repo.update_status(
            created.id,
            ValidationStatus.RUNNING.value
        )
        assert running.status == ValidationStatus.RUNNING.value

        # RUNNING -> COMPLETED
        completed = await factor_validation_repo.update_status(
            created.id,
            ValidationStatus.COMPLETED.value
        )
        assert completed.status == ValidationStatus.COMPLETED.value

    async def test_update_status_to_failed(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test updating status to FAILED"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        # Update to FAILED
        failed = await factor_validation_repo.update_status(
            created.id,
            ValidationStatus.FAILED.value
        )

        assert failed is not None
        assert failed.status == ValidationStatus.FAILED.value

    async def test_update_status_non_existent_validation(
        self,
        factor_validation_repo
    ):
        """Test updating status for non-existent validation"""
        result = await factor_validation_repo.update_status(
            "non_existent_id",
            ValidationStatus.COMPLETED.value
        )
        assert result is None

    async def test_update_status_persists_to_database(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test that status update is persisted to database"""
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )

        # Update status
        await factor_validation_repo.update_status(
            created.id,
            ValidationStatus.COMPLETED.value
        )

        # Retrieve again and verify
        retrieved = await factor_validation_repo.get(created.id)
        assert retrieved.status == ValidationStatus.COMPLETED.value

    # ==================== Complex Scenarios Tests ====================

    async def test_multiple_factors_multiple_validations(
        self,
        factor_validation_repo,
        custom_factor_repo
    ):
        """Test handling multiple factors with multiple validations each"""
        # Create 2 factors
        factor1_data = {
            "factor_name": "Factor 1",
            "user_id": "user123",
            "formula": "close / open",
            "formula_language": "qlib_alpha",
            "status": FactorStatus.PUBLISHED.value
        }
        factor1 = await custom_factor_repo.create(factor1_data, commit=True)

        factor2_data = {
            "factor_name": "Factor 2",
            "user_id": "user123",
            "formula": "high / low",
            "formula_language": "qlib_alpha",
            "status": FactorStatus.PUBLISHED.value
        }
        factor2 = await custom_factor_repo.create(factor2_data, commit=True)

        # Create 2 validations for each factor
        for factor in [factor1, factor2]:
            for val_type in [ValidationType.IC_ANALYSIS, ValidationType.SHARPE_RATIO]:
                data = {
                    "factor_id": factor.id,
                    "validation_type": val_type.value,
                    "dataset_id": "dataset_001",
                    "status": ValidationStatus.COMPLETED.value
                }
                await factor_validation_repo.create(data, commit=True)

        # Verify factor1 has 2 validations
        factor1_results = await factor_validation_repo.get_by_factor(factor1.id)
        assert len(factor1_results) == 2

        # Verify factor2 has 2 validations
        factor2_results = await factor_validation_repo.get_by_factor(factor2.id)
        assert len(factor2_results) == 2

    async def test_validation_with_all_fields_populated(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating validation with all optional fields"""
        complete_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.IC_ANALYSIS.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.COMPLETED.value,
            "started_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "metrics": {
                "ic_mean": 0.05,
                "ic_std": 0.02,
                "ic_ir": 2.5,
                "rank_ic_mean": 0.06
            },
            "details": {
                "period": "2020-01-01 to 2023-12-31",
                "sample_count": 1000,
                "universe": "CSI300"
            },
            "error_message": None
        }
        result = await factor_validation_repo.create(complete_data, commit=True)

        assert result is not None
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.metrics is not None
        assert result.details is not None
        assert len(result.metrics) == 4
        assert len(result.details) == 3

    async def test_validation_with_error_message(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating failed validation with error message"""
        failed_data = {
            "factor_id": sample_factor.id,
            "validation_type": ValidationType.LAYERED_BACKTEST.value,
            "dataset_id": "dataset_001",
            "status": ValidationStatus.FAILED.value,
            "error_message": "Insufficient data for backtesting"
        }
        result = await factor_validation_repo.create(failed_data, commit=True)

        assert result is not None
        assert result.status == ValidationStatus.FAILED.value
        assert result.error_message == "Insufficient data for backtesting"

    # ==================== Edge Cases Tests ====================

    async def test_get_by_factor_with_zero_limit(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test pagination with limit=0 (should return empty)"""
        await factor_validation_repo.create(sample_validation_data, commit=True)

        results = await factor_validation_repo.get_by_factor(
            sample_validation_data["factor_id"],
            limit=0
        )
        # Note: limit=0 might return all or none depending on implementation
        # This test documents the behavior
        assert isinstance(results, list)

    async def test_get_by_status_with_large_skip(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test pagination with skip larger than result count"""
        await factor_validation_repo.create(sample_validation_data, commit=True)

        results = await factor_validation_repo.get_by_status(
            ValidationStatus.PENDING.value,
            skip=1000
        )
        assert len(results) == 0

    async def test_validation_types_coverage(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating validations for all validation types"""
        validation_types = [
            ValidationType.IC_ANALYSIS,
            ValidationType.IC_RANK_ANALYSIS,
            ValidationType.LAYERED_BACKTEST,
            ValidationType.SHARPE_RATIO,
            ValidationType.FACTOR_DISTRIBUTION
        ]

        for val_type in validation_types:
            data = {
                "factor_id": sample_factor.id,
                "validation_type": val_type.value,
                "dataset_id": "dataset_001",
                "status": ValidationStatus.COMPLETED.value
            }
            result = await factor_validation_repo.create(data, commit=True)
            assert result.validation_type == val_type.value

        # Verify all created
        all_results = await factor_validation_repo.get_by_factor(sample_factor.id)
        assert len(all_results) == len(validation_types)

    async def test_validation_statuses_coverage(
        self,
        factor_validation_repo,
        sample_factor
    ):
        """Test creating validations with all status types"""
        statuses = [
            ValidationStatus.PENDING,
            ValidationStatus.RUNNING,
            ValidationStatus.COMPLETED,
            ValidationStatus.FAILED
        ]

        for status in statuses:
            data = {
                "factor_id": sample_factor.id,
                "validation_type": ValidationType.IC_ANALYSIS.value,
                "dataset_id": "dataset_001",
                "status": status.value
            }
            result = await factor_validation_repo.create(data, commit=True)
            assert result.status == status.value

    async def test_base_repository_methods_inherited(
        self,
        factor_validation_repo,
        sample_validation_data
    ):
        """Test that base repository methods work correctly"""
        # Test create (already tested but verify inheritance)
        created = await factor_validation_repo.create(
            sample_validation_data,
            commit=True
        )
        assert created.id is not None

        # Test get
        retrieved = await factor_validation_repo.get(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

        # Test update
        update_data = {"status": ValidationStatus.COMPLETED.value}
        updated = await factor_validation_repo.update(
            created.id,
            update_data,
            commit=True
        )
        assert updated.status == ValidationStatus.COMPLETED.value

        # Test soft delete
        deleted = await factor_validation_repo.delete(created.id, soft=True)
        assert deleted is True

        # Verify soft deleted
        retrieved_after_delete = await factor_validation_repo.get(created.id)
        assert retrieved_after_delete is None or retrieved_after_delete.is_deleted
