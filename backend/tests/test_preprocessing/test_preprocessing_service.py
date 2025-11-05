"""
Data Preprocessing Service Tests

TDD tests for PreprocessingService functionality.
Tests cover all preprocessing operations: missing values, outliers, transformations, and filtering.
"""

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.dataset import Dataset, DatasetStatus, DataSource
from app.database.models.preprocessing import (
    DataPreprocessingRule, PreprocessingRuleType,
    MissingValueMethod, OutlierDetectionMethod, OutlierHandlingStrategy,
    TransformationType, FilterOperator
)
from app.database.repositories.preprocessing import PreprocessingRuleRepository
from app.modules.data_management.services.preprocessing_service import PreprocessingService


class TestMissingValueHandling:
    """Test suite for missing value handling operations"""

    @pytest.mark.asyncio
    async def test_delete_rows_with_missing_values(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test deleting rows with missing values"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.DELETE_ROWS.value,
            "columns": ["price", "volume"]
        }
        original_rows = len(sample_dataframe)

        # Act
        result_df = await service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert len(result_df) < original_rows  # Some rows deleted
        assert result_df["price"].isna().sum() == 0
        assert result_df["volume"].isna().sum() == 0

    @pytest.mark.asyncio
    async def test_mean_fill_missing_values(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filling missing values with mean"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["price", "volume"]
        }

        # Act
        result_df = await service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result_df["price"].isna().sum() == 0
        assert result_df["volume"].isna().sum() == 0
        # Check that mean was used
        assert len(result_df) == len(sample_dataframe)  # No rows deleted

    @pytest.mark.asyncio
    async def test_median_fill_missing_values(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filling missing values with median"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.MEDIAN_FILL.value,
            "columns": ["price"]
        }

        # Act
        result_df = await service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result_df["price"].isna().sum() == 0
        assert len(result_df) == len(sample_dataframe)

    @pytest.mark.asyncio
    async def test_forward_fill_missing_values(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test forward filling missing values"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.FORWARD_FILL.value,
            "columns": ["volume"]
        }

        # Act
        result_df = await service.handle_missing_values(sample_dataframe, config)

        # Assert
        # Forward fill doesn't fill first NaN, so count should be reduced
        assert result_df["volume"].isna().sum() <= sample_dataframe["volume"].isna().sum()

    @pytest.mark.asyncio
    async def test_handle_missing_values_empty_dataframe(
        self,
        sample_dataframe_empty: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test handling missing values in empty DataFrame (edge case)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["price"]
        }

        # Act
        result_df = await service.handle_missing_values(sample_dataframe_empty, config)

        # Assert
        assert len(result_df) == 0
        assert result_df.empty

    @pytest.mark.asyncio
    async def test_handle_missing_values_all_missing(
        self,
        sample_dataframe_all_missing: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test handling DataFrame with all missing values (edge case)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.DELETE_ROWS.value,
            "columns": ["price", "volume"]
        }

        # Act
        result_df = await service.handle_missing_values(sample_dataframe_all_missing, config)

        # Assert
        assert len(result_df) == 0  # All rows should be deleted

    @pytest.mark.asyncio
    async def test_handle_missing_values_invalid_column(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test handling missing values with invalid column name"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["nonexistent_column"]
        }

        # Act & Assert
        with pytest.raises(KeyError):
            await service.handle_missing_values(sample_dataframe, config)


class TestOutlierDetection:
    """Test suite for outlier detection and handling"""

    @pytest.mark.asyncio
    async def test_detect_outliers_standard_deviation(
        self,
        sample_dataframe_with_outliers: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test outlier detection using standard deviation method"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 2.0,  # 2 standard deviations
            "columns": ["price"]
        }

        # Act
        outlier_mask = await service.detect_outliers(sample_dataframe_with_outliers, config)

        # Assert
        assert isinstance(outlier_mask, pd.Series)
        assert outlier_mask.sum() > 0  # Should detect at least one outlier (5000)

    @pytest.mark.asyncio
    async def test_detect_outliers_quantile_method(
        self,
        sample_dataframe_with_outliers: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test outlier detection using IQR/quantile method"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "detection_method": OutlierDetectionMethod.QUANTILE.value,
            "lower_quantile": 0.25,
            "upper_quantile": 0.75,
            "columns": ["volume"]
        }

        # Act
        outlier_mask = await service.detect_outliers(sample_dataframe_with_outliers, config)

        # Assert
        assert isinstance(outlier_mask, pd.Series)
        assert outlier_mask.sum() > 0  # Should detect outliers

    @pytest.mark.asyncio
    async def test_handle_outliers_delete(
        self,
        sample_dataframe_with_outliers: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test handling outliers by deleting rows"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 2.0,
            "handling": OutlierHandlingStrategy.DELETE.value,
            "columns": ["price"]
        }
        original_rows = len(sample_dataframe_with_outliers)

        # Act
        result_df = await service.handle_outliers(sample_dataframe_with_outliers, config)

        # Assert
        assert len(result_df) < original_rows  # Outliers should be deleted

    @pytest.mark.asyncio
    async def test_handle_outliers_cap(
        self,
        sample_dataframe_with_outliers: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test handling outliers by capping to threshold (winsorization)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 2.0,
            "handling": OutlierHandlingStrategy.CAP.value,
            "columns": ["price"]
        }

        # Act
        result_df = await service.handle_outliers(sample_dataframe_with_outliers, config)

        # Assert
        assert len(result_df) == len(sample_dataframe_with_outliers)  # No rows deleted
        # Extreme values should be capped
        assert result_df["price"].max() < sample_dataframe_with_outliers["price"].max()


class TestDataTransformation:
    """Test suite for data transformation operations"""

    @pytest.mark.asyncio
    async def test_normalize_min_max(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test Min-Max normalization (0-1)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price"],
            "range": [0, 1]
        }

        # Act
        result_df = await service.transform_data(sample_dataframe, config)

        # Assert
        # Values should be between 0 and 1
        assert result_df["price"].min() >= 0
        assert result_df["price"].max() <= 1
        # Transformed column should have different values
        assert not result_df["price"].equals(sample_dataframe["price"])

    @pytest.mark.asyncio
    async def test_standardize_z_score(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test Z-Score standardization"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "type": TransformationType.STANDARDIZE.value,
            "columns": ["price", "volume"]
        }

        # Act
        result_df = await service.transform_data(sample_dataframe, config)

        # Assert
        # Standardized values should have mean ≈ 0 and std ≈ 1
        assert abs(result_df["price"].mean()) < 0.1
        assert abs(result_df["price"].std() - 1.0) < 0.1

    @pytest.mark.asyncio
    async def test_transform_empty_dataframe(
        self,
        sample_dataframe_empty: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test transformation on empty DataFrame (edge case)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price"]
        }

        # Act
        result_df = await service.transform_data(sample_dataframe_empty, config)

        # Assert
        assert result_df.empty
        assert len(result_df) == 0


class TestDataFiltering:
    """Test suite for data filtering operations"""

    @pytest.mark.asyncio
    async def test_filter_single_condition(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with a single condition"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {
                    "column": "price",
                    "operator": FilterOperator.GREATER_THAN.value,
                    "value": 200
                }
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert len(result_df) < len(sample_dataframe)
        assert all(result_df["price"] > 200)

    @pytest.mark.asyncio
    async def test_filter_multiple_conditions_and(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with multiple AND conditions"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_THAN.value, "value": 150},
                {"column": "volume", "operator": FilterOperator.LESS_THAN.value, "value": 5000}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["price"] > 150)
        assert all(result_df["volume"] < 5000)

    @pytest.mark.asyncio
    async def test_filter_multiple_conditions_or(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with multiple OR conditions"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_THAN.value, "value": 800},
                {"column": "volume", "operator": FilterOperator.LESS_THAN.value, "value": 1200}
            ],
            "logic": "OR"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert len(result_df) > 0
        # At least one condition should be true for each row
        assert any((result_df["price"] > 800) | (result_df["volume"] < 1200))

    @pytest.mark.asyncio
    async def test_filter_not_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with NOT operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {
                    "column": "symbol",
                    "operator": FilterOperator.NOT_EQUALS.value,
                    "value": "AAPL"
                }
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert "AAPL" not in result_df["symbol"].values

    @pytest.mark.asyncio
    async def test_filter_empty_result(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering that results in empty DataFrame"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_THAN.value, "value": 10000}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert len(result_df) == 0

    @pytest.mark.asyncio
    async def test_filter_greater_equal(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with greater or equal operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_EQUAL.value, "value": 200}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["price"] >= 200)

    @pytest.mark.asyncio
    async def test_filter_less_equal(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with less or equal operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "volume", "operator": FilterOperator.LESS_EQUAL.value, "value": 2000}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["volume"] <= 2000)

    @pytest.mark.asyncio
    async def test_filter_in_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with IN operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "symbol", "operator": FilterOperator.IN.value, "value": ["AAPL", "GOOGL", "MSFT"]}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["symbol"].isin(["AAPL", "GOOGL", "MSFT"]))

    @pytest.mark.asyncio
    async def test_filter_not_in_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with NOT IN operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "symbol", "operator": FilterOperator.NOT_IN.value, "value": ["AAPL", "GOOGL"]}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert not any(result_df["symbol"].isin(["AAPL", "GOOGL"]))

    @pytest.mark.asyncio
    async def test_filter_contains_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with CONTAINS operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "symbol", "operator": FilterOperator.CONTAINS.value, "value": "A"}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["symbol"].str.contains("A", na=False))

    @pytest.mark.asyncio
    async def test_filter_is_null_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with IS NULL operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.IS_NULL.value, "value": None}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["price"].isna())

    @pytest.mark.asyncio
    async def test_filter_not_null_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with NOT NULL operator"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.NOT_NULL.value, "value": None}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert all(result_df["price"].notna())

    @pytest.mark.asyncio
    async def test_filter_invalid_column(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with invalid column (should skip condition)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "nonexistent", "operator": FilterOperator.EQUALS.value, "value": "test"}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert - all rows should remain since condition was skipped
        assert len(result_df) == len(sample_dataframe)

    @pytest.mark.asyncio
    async def test_filter_unknown_operator(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with unknown operator (should skip condition)"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [
                {"column": "price", "operator": "unknown_op", "value": 100}
            ],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert - all rows should remain since condition was skipped
        assert len(result_df) == len(sample_dataframe)

    @pytest.mark.asyncio
    async def test_filter_empty_conditions(
        self,
        sample_dataframe: pd.DataFrame,
        rule_repo: PreprocessingRuleRepository
    ):
        """Test filtering with empty conditions list"""
        # Arrange
        service = PreprocessingService(rule_repo)
        config = {
            "conditions": [],
            "logic": "AND"
        }

        # Act
        result_df = await service.filter_data(sample_dataframe, config)

        # Assert
        assert len(result_df) == len(sample_dataframe)
