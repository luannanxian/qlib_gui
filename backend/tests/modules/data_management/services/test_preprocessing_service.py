"""
Tests for PreprocessingService

This test suite covers all data preprocessing methods including:
- Missing value handling (delete, mean, median, forward/backward fill, constant)
- Outlier detection (standard deviation, quantile methods)
- Outlier handling (delete, cap, replace with mean/median)
- Data transformation (normalize, standardize, log transform)
- Data filtering (multi-condition with AND/OR logic)

Test Strategy:
- Use TDD approach with AAA pattern (Arrange-Act-Assert)
- Test all method variations and edge cases
- Verify pandas DataFrame operations are correct
- Test error handling and validation
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.modules.data_management.services.preprocessing_service import PreprocessingService
from app.database.repositories.preprocessing import PreprocessingRuleRepository
from app.database.models.preprocessing import (
    MissingValueMethod,
    OutlierDetectionMethod,
    OutlierHandlingStrategy,
    TransformationType,
    FilterOperator
)


@pytest.fixture
def mock_rule_repository():
    """Create mock PreprocessingRuleRepository"""
    repo = Mock(spec=PreprocessingRuleRepository)
    return repo


@pytest.fixture
def preprocessing_service(mock_rule_repository):
    """Create PreprocessingService instance with mock repository"""
    return PreprocessingService(rule_repository=mock_rule_repository)


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame with various data types and missing values"""
    return pd.DataFrame({
        'price': [100.0, 105.0, np.nan, 110.0, 115.0, 120.0, 125.0, 130.0],
        'volume': [1000, 1100, 1200, np.nan, 1400, 1500, 1600, 1700],
        'close': [99.0, 104.0, 108.0, 112.0, 116.0, 121.0, 126.0, 131.0],
        'name': ['A', 'B', None, 'D', 'E', 'F', 'G', 'H']
    })


@pytest.fixture
def outlier_dataframe():
    """Create DataFrame with outliers for testing"""
    np.random.seed(42)
    normal_data = np.random.normal(100, 10, 98)
    outliers = [300, 500]  # Clear outliers

    return pd.DataFrame({
        'price': np.concatenate([normal_data, outliers]),
        'volume': np.concatenate([np.random.normal(1000, 100, 98), [5000, 10000]])
    })


# ============================================================================
# Tests for handle_missing_values
# ============================================================================

@pytest.mark.asyncio
class TestHandleMissingValues:
    """Test missing value handling with various methods"""

    async def test_handle_missing_delete_rows(self, preprocessing_service, sample_dataframe):
        """Test DELETE_ROWS method removes rows with missing values"""
        # Arrange
        config = {
            "method": MissingValueMethod.DELETE_ROWS.value,
            "columns": ["price", "volume"]
        }

        # Act
        result = await preprocessing_service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert len(result) == 6  # 2 rows removed (one with NaN in price, one in volume)
        assert result['price'].isna().sum() == 0
        assert result['volume'].isna().sum() == 0

    async def test_handle_missing_mean_fill(self, preprocessing_service, sample_dataframe):
        """Test MEAN_FILL method fills missing values with column mean"""
        # Arrange
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["price", "volume"]
        }
        original_price_mean = sample_dataframe['price'].mean()
        original_volume_mean = sample_dataframe['volume'].mean()

        # Act
        result = await preprocessing_service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result['price'].isna().sum() == 0
        assert result['volume'].isna().sum() == 0
        # Verify filled value is approximately the mean
        assert abs(result.loc[2, 'price'] - original_price_mean) < 1.0
        assert abs(result.loc[3, 'volume'] - original_volume_mean) < 1.0

    async def test_handle_missing_median_fill(self, preprocessing_service, sample_dataframe):
        """Test MEDIAN_FILL method fills missing values with column median"""
        # Arrange
        config = {
            "method": MissingValueMethod.MEDIAN_FILL.value,
            "columns": ["price"]
        }
        original_median = sample_dataframe['price'].median()

        # Act
        result = await preprocessing_service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result['price'].isna().sum() == 0
        assert result.loc[2, 'price'] == original_median

    async def test_handle_missing_forward_fill(self, preprocessing_service):
        """Test FORWARD_FILL method propagates previous value forward"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, 105.0, np.nan, np.nan, 115.0]
        })
        config = {
            "method": MissingValueMethod.FORWARD_FILL.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_missing_values(df, config)

        # Assert
        assert result['price'].isna().sum() == 0
        assert result.loc[2, 'price'] == 105.0  # Forward filled from index 1
        assert result.loc[3, 'price'] == 105.0  # Forward filled from index 1

    async def test_handle_missing_backward_fill(self, preprocessing_service):
        """Test BACKWARD_FILL method propagates next value backward"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, np.nan, np.nan, 115.0, 120.0]
        })
        config = {
            "method": MissingValueMethod.BACKWARD_FILL.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_missing_values(df, config)

        # Assert
        assert result['price'].isna().sum() == 0
        assert result.loc[1, 'price'] == 115.0  # Backward filled from index 3
        assert result.loc[2, 'price'] == 115.0  # Backward filled from index 3

    async def test_handle_missing_constant_fill(self, preprocessing_service, sample_dataframe):
        """Test CONSTANT_FILL method fills missing values with constant"""
        # Arrange
        config = {
            "method": MissingValueMethod.CONSTANT_FILL.value,
            "columns": ["price", "volume"],
            "fill_value": 999
        }

        # Act
        result = await preprocessing_service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result['price'].isna().sum() == 0
        assert result['volume'].isna().sum() == 0
        assert result.loc[2, 'price'] == 999
        assert result.loc[3, 'volume'] == 999

    async def test_handle_missing_constant_fill_default_zero(self, preprocessing_service, sample_dataframe):
        """Test CONSTANT_FILL defaults to 0 if fill_value not specified"""
        # Arrange
        config = {
            "method": MissingValueMethod.CONSTANT_FILL.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_missing_values(sample_dataframe, config)

        # Assert
        assert result.loc[2, 'price'] == 0

    async def test_handle_missing_empty_dataframe(self, preprocessing_service):
        """Test handling missing values on empty DataFrame returns empty DataFrame"""
        # Arrange
        df = pd.DataFrame()
        config = {"method": MissingValueMethod.MEAN_FILL.value, "columns": []}

        # Act
        result = await preprocessing_service.handle_missing_values(df, config)

        # Assert
        assert result.empty

    async def test_handle_missing_nonexistent_column(self, preprocessing_service, sample_dataframe):
        """Test handling missing values raises KeyError for non-existent columns"""
        # Arrange
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["nonexistent_column"]
        }

        # Act & Assert
        with pytest.raises(KeyError, match="Columns not found in DataFrame"):
            await preprocessing_service.handle_missing_values(sample_dataframe, config)

    async def test_handle_missing_non_numeric_column_mean_fill(self, preprocessing_service):
        """Test MEAN_FILL skips non-numeric columns"""
        # Arrange
        df = pd.DataFrame({
            'name': ['A', 'B', None, 'D'],
            'price': [100.0, np.nan, 110.0, 115.0]
        })
        config = {
            "method": MissingValueMethod.MEAN_FILL.value,
            "columns": ["name", "price"]
        }

        # Act
        result = await preprocessing_service.handle_missing_values(df, config)

        # Assert
        # Non-numeric column 'name' should remain unchanged
        assert pd.isna(result.loc[2, 'name'])
        # Numeric column 'price' should be filled
        assert not pd.isna(result.loc[1, 'price'])


# ============================================================================
# Tests for detect_outliers
# ============================================================================

@pytest.mark.asyncio
class TestDetectOutliers:
    """Test outlier detection methods"""

    async def test_detect_outliers_standard_deviation(self, preprocessing_service, outlier_dataframe):
        """Test standard deviation method detects outliers correctly"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "columns": ["price"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(outlier_dataframe, config)

        # Assert
        assert outlier_mask.sum() >= 2  # At least 2 outliers (300 and 500)
        assert isinstance(outlier_mask, pd.Series)
        assert len(outlier_mask) == len(outlier_dataframe)

    async def test_detect_outliers_quantile_method(self, preprocessing_service, outlier_dataframe):
        """Test quantile (IQR) method detects outliers correctly"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.QUANTILE.value,
            "lower_quantile": 0.25,
            "upper_quantile": 0.75,
            "columns": ["price"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(outlier_dataframe, config)

        # Assert
        assert outlier_mask.sum() >= 2  # At least 2 outliers
        assert isinstance(outlier_mask, pd.Series)

    async def test_detect_outliers_multiple_columns(self, preprocessing_service, outlier_dataframe):
        """Test outlier detection on multiple columns"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "columns": ["price", "volume"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(outlier_dataframe, config)

        # Assert
        # Should detect outliers in both price and volume columns
        assert outlier_mask.sum() >= 2

    async def test_detect_outliers_zero_std_dev(self, preprocessing_service):
        """Test outlier detection with zero standard deviation (constant column)"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0] * 10  # All same values
        })
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "columns": ["price"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(df, config)

        # Assert
        assert outlier_mask.sum() == 0  # No outliers detected (std = 0)

    async def test_detect_outliers_custom_quantiles(self, preprocessing_service, outlier_dataframe):
        """Test quantile method with custom quantile values"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.QUANTILE.value,
            "lower_quantile": 0.1,
            "upper_quantile": 0.9,
            "columns": ["price"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(outlier_dataframe, config)

        # Assert
        # Wider quantile range should still detect extreme outliers
        assert outlier_mask.sum() >= 2

    async def test_detect_outliers_non_numeric_column(self, preprocessing_service):
        """Test outlier detection skips non-numeric columns"""
        # Arrange
        df = pd.DataFrame({
            'name': ['A', 'B', 'C', 'D', 'E'],
            'price': [100, 105, 110, 115, 120]
        })
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "columns": ["name", "price"]
        }

        # Act
        outlier_mask = await preprocessing_service.detect_outliers(df, config)

        # Assert
        # Should complete without error, skipping non-numeric 'name' column
        assert isinstance(outlier_mask, pd.Series)


# ============================================================================
# Tests for handle_outliers
# ============================================================================

@pytest.mark.asyncio
class TestHandleOutliers:
    """Test outlier handling strategies"""

    async def test_handle_outliers_delete_strategy(self, preprocessing_service, outlier_dataframe):
        """Test DELETE strategy removes outlier rows"""
        # Arrange
        original_len = len(outlier_dataframe)
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "handling": OutlierHandlingStrategy.DELETE.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        assert len(result) < original_len  # Some rows removed
        # Extreme outliers should be removed
        assert 300 not in result['price'].values
        assert 500 not in result['price'].values

    async def test_handle_outliers_cap_strategy_std_dev(self, preprocessing_service, outlier_dataframe):
        """Test CAP strategy with standard deviation method"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "handling": OutlierHandlingStrategy.CAP.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        # Outliers should be capped, not removed
        assert len(result) == len(outlier_dataframe)
        # Extreme values should be capped
        mean = outlier_dataframe['price'].mean()
        std = outlier_dataframe['price'].std()
        upper_bound = mean + 3 * std
        assert result['price'].max() <= upper_bound + 1  # Allow small floating point error

    async def test_handle_outliers_cap_strategy_quantile(self, preprocessing_service, outlier_dataframe):
        """Test CAP strategy with quantile method"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.QUANTILE.value,
            "lower_quantile": 0.25,
            "upper_quantile": 0.75,
            "handling": OutlierHandlingStrategy.CAP.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        # All rows should remain
        assert len(result) == len(outlier_dataframe)
        # Outliers should be capped to IQR bounds
        Q1 = outlier_dataframe['price'].quantile(0.25)
        Q3 = outlier_dataframe['price'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        assert result['price'].max() <= upper_bound + 1

    async def test_handle_outliers_replace_mean(self, preprocessing_service, outlier_dataframe):
        """Test REPLACE_MEAN strategy replaces outliers with column mean"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "handling": OutlierHandlingStrategy.REPLACE_MEAN.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        # All rows should remain
        assert len(result) == len(outlier_dataframe)
        # Outliers should be replaced, so max should be lower than original
        assert result['price'].max() < outlier_dataframe['price'].max()

    async def test_handle_outliers_replace_median(self, preprocessing_service, outlier_dataframe):
        """Test REPLACE_MEDIAN strategy replaces outliers with column median"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "handling": OutlierHandlingStrategy.REPLACE_MEDIAN.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        # All rows should remain
        assert len(result) == len(outlier_dataframe)
        # Outliers should be replaced
        assert result['price'].max() < outlier_dataframe['price'].max()

    async def test_handle_outliers_multiple_columns(self, preprocessing_service, outlier_dataframe):
        """Test handling outliers on multiple columns"""
        # Arrange
        config = {
            "detection_method": OutlierDetectionMethod.STANDARD_DEVIATION.value,
            "threshold": 3.0,
            "handling": OutlierHandlingStrategy.CAP.value,
            "columns": ["price", "volume"]
        }

        # Act
        result = await preprocessing_service.handle_outliers(outlier_dataframe, config)

        # Assert
        assert len(result) == len(outlier_dataframe)
        # Both columns should have capped values
        assert result['price'].max() < outlier_dataframe['price'].max()
        assert result['volume'].max() < outlier_dataframe['volume'].max()


# ============================================================================
# Tests for transform_data
# ============================================================================

@pytest.mark.asyncio
class TestTransformData:
    """Test data transformation methods"""

    async def test_transform_normalize_default_range(self, preprocessing_service):
        """Test NORMALIZE transformation with default [0, 1] range"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, 150.0, 200.0, 250.0, 300.0]
        })
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        assert result['price'].min() == 0.0
        assert result['price'].max() == 1.0
        assert abs(result['price'].iloc[2] - 0.5) < 0.01  # Middle value should be ~0.5

    async def test_transform_normalize_custom_range(self, preprocessing_service):
        """Test NORMALIZE transformation with custom range"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, 150.0, 200.0, 250.0, 300.0]
        })
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price"],
            "range": [-1, 1]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        assert abs(result['price'].min() - (-1.0)) < 0.01
        assert abs(result['price'].max() - 1.0) < 0.01

    async def test_transform_normalize_zero_range(self, preprocessing_service):
        """Test NORMALIZE with constant column (zero range)"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0] * 5  # All same values
        })
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # Should remain unchanged (no division by zero)
        assert (result['price'] == 100.0).all()

    async def test_transform_standardize(self, preprocessing_service):
        """Test STANDARDIZE transformation (z-score)"""
        # Arrange
        np.random.seed(42)
        df = pd.DataFrame({
            'price': np.random.normal(100, 10, 100)
        })
        config = {
            "type": TransformationType.STANDARDIZE.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # Standardized data should have mean ≈ 0 and std ≈ 1
        assert abs(result['price'].mean()) < 0.1
        assert abs(result['price'].std() - 1.0) < 0.1

    async def test_transform_standardize_zero_std(self, preprocessing_service):
        """Test STANDARDIZE with zero standard deviation"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0] * 5
        })
        config = {
            "type": TransformationType.STANDARDIZE.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # Should remain unchanged (no division by zero)
        assert (result['price'] == 100.0).all()

    async def test_transform_log(self, preprocessing_service):
        """Test LOG_TRANSFORM transformation"""
        # Arrange
        df = pd.DataFrame({
            'price': [10.0, 100.0, 1000.0, 10000.0]
        })
        config = {
            "type": TransformationType.LOG_TRANSFORM.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # Log transform should reduce variance
        original_std = df['price'].std()
        transformed_std = result['price'].std()
        assert transformed_std < original_std
        # Verify log(x+1) was applied
        assert abs(result['price'].iloc[0] - np.log(11.0)) < 0.01

    async def test_transform_log_with_zero(self, preprocessing_service):
        """Test LOG_TRANSFORM handles zero values correctly"""
        # Arrange
        df = pd.DataFrame({
            'price': [0.0, 10.0, 100.0]
        })
        config = {
            "type": TransformationType.LOG_TRANSFORM.value,
            "columns": ["price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # log(0+1) = 0, should not raise error
        assert result['price'].iloc[0] == 0.0
        assert not result['price'].isna().any()

    async def test_transform_empty_dataframe(self, preprocessing_service):
        """Test transformation on empty DataFrame returns empty DataFrame"""
        # Arrange
        df = pd.DataFrame()
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": []
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        assert result.empty

    async def test_transform_multiple_columns(self, preprocessing_service):
        """Test transformation on multiple columns"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, 150.0, 200.0],
            'volume': [1000.0, 1500.0, 2000.0]
        })
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["price", "volume"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        assert result['price'].min() == 0.0
        assert result['price'].max() == 1.0
        assert result['volume'].min() == 0.0
        assert result['volume'].max() == 1.0

    async def test_transform_non_numeric_column(self, preprocessing_service):
        """Test transformation skips non-numeric columns"""
        # Arrange
        df = pd.DataFrame({
            'name': ['A', 'B', 'C'],
            'price': [100.0, 150.0, 200.0]
        })
        config = {
            "type": TransformationType.NORMALIZE.value,
            "columns": ["name", "price"]
        }

        # Act
        result = await preprocessing_service.transform_data(df, config)

        # Assert
        # Non-numeric column should remain unchanged
        assert (result['name'] == df['name']).all()
        # Numeric column should be normalized
        assert result['price'].min() == 0.0


# ============================================================================
# Tests for filter_data
# ============================================================================

@pytest.mark.asyncio
class TestFilterData:
    """Test data filtering with various conditions"""

    async def test_filter_equals_operator(self, preprocessing_service):
        """Test EQUALS filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.EQUALS.value, "value": 110}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]['price'] == 110

    async def test_filter_not_equals_operator(self, preprocessing_service):
        """Test NOT_EQUALS filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 100, 110, 115, 120]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.NOT_EQUALS.value, "value": 100}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert 100 not in result['price'].values

    async def test_filter_greater_than_operator(self, preprocessing_service):
        """Test GREATER_THAN filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_THAN.value, "value": 110}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 2
        assert (result['price'] > 110).all()

    async def test_filter_greater_equal_operator(self, preprocessing_service):
        """Test GREATER_EQUAL filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_EQUAL.value, "value": 110}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert (result['price'] >= 110).all()

    async def test_filter_less_than_operator(self, preprocessing_service):
        """Test LESS_THAN filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.LESS_THAN.value, "value": 110}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 2
        assert (result['price'] < 110).all()

    async def test_filter_less_equal_operator(self, preprocessing_service):
        """Test LESS_EQUAL filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.LESS_EQUAL.value, "value": 110}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert (result['price'] <= 110).all()

    async def test_filter_in_operator(self, preprocessing_service):
        """Test IN filter operator with list of values"""
        # Arrange
        df = pd.DataFrame({
            'category': ['A', 'B', 'C', 'D', 'E']
        })
        config = {
            "conditions": [
                {"column": "category", "operator": FilterOperator.IN.value, "value": ['A', 'C', 'E']}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert set(result['category']) == {'A', 'C', 'E'}

    async def test_filter_not_in_operator(self, preprocessing_service):
        """Test NOT_IN filter operator"""
        # Arrange
        df = pd.DataFrame({
            'category': ['A', 'B', 'C', 'D', 'E']
        })
        config = {
            "conditions": [
                {"column": "category", "operator": FilterOperator.NOT_IN.value, "value": ['A', 'C']}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert 'A' not in result['category'].values
        assert 'C' not in result['category'].values

    async def test_filter_contains_operator(self, preprocessing_service):
        """Test CONTAINS filter operator for string matching"""
        # Arrange
        df = pd.DataFrame({
            'name': ['Apple Inc', 'Microsoft Corp', 'Amazon.com', 'Google LLC', 'Meta Platforms']
        })
        config = {
            "conditions": [
                {"column": "name", "operator": FilterOperator.CONTAINS.value, "value": "Corp"}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 1
        assert 'Corp' in result.iloc[0]['name']

    async def test_filter_is_null_operator(self, preprocessing_service):
        """Test IS_NULL filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, np.nan, 110.0, np.nan, 120.0]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.IS_NULL.value, "value": None}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 2
        assert result['price'].isna().all()

    async def test_filter_not_null_operator(self, preprocessing_service):
        """Test NOT_NULL filter operator"""
        # Arrange
        df = pd.DataFrame({
            'price': [100.0, np.nan, 110.0, np.nan, 120.0]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.NOT_NULL.value, "value": None}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == 3
        assert result['price'].notna().all()

    async def test_filter_and_logic(self, preprocessing_service):
        """Test multiple conditions with AND logic"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_THAN.value, "value": 105},
                {"column": "volume", "operator": FilterOperator.LESS_THAN.value, "value": 1300}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        # price > 105: [110, 115, 120]
        # volume < 1300: [1000, 1100, 1200]
        # AND: only index 2 (110, 1200)
        assert len(result) == 1
        assert (result['price'] > 105).all()
        assert (result['volume'] < 1300).all()

    async def test_filter_or_logic(self, preprocessing_service):
        """Test multiple conditions with OR logic"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.LESS_THAN.value, "value": 105},
                {"column": "volume", "operator": FilterOperator.GREATER_THAN.value, "value": 1300}
            ],
            "logic": "OR"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        # price < 105: [100] (index 0)
        # volume > 1300: [1400] (index 4)
        # OR: index 0 and index 4
        assert len(result) == 2

    async def test_filter_empty_conditions(self, preprocessing_service):
        """Test filtering with empty conditions returns original DataFrame"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110]
        })
        config = {
            "conditions": [],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        assert len(result) == len(df)
        assert result.equals(df)

    async def test_filter_nonexistent_column(self, preprocessing_service):
        """Test filtering with non-existent column logs warning and skips condition"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110]
        })
        config = {
            "conditions": [
                {"column": "nonexistent", "operator": FilterOperator.EQUALS.value, "value": 100}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        # Should return original DataFrame (condition skipped)
        assert len(result) == len(df)

    async def test_filter_complex_multi_condition(self, preprocessing_service):
        """Test complex filtering with multiple conditions"""
        # Arrange
        df = pd.DataFrame({
            'price': [100, 105, 110, 115, 120, 125, 130],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600],
            'category': ['A', 'B', 'A', 'C', 'B', 'A', 'C']
        })
        config = {
            "conditions": [
                {"column": "price", "operator": FilterOperator.GREATER_EQUAL.value, "value": 110},
                {"column": "volume", "operator": FilterOperator.LESS_EQUAL.value, "value": 1500},
                {"column": "category", "operator": FilterOperator.IN.value, "value": ['A', 'B']}
            ],
            "logic": "AND"
        }

        # Act
        result = await preprocessing_service.filter_data(df, config)

        # Assert
        # price >= 110 AND volume <= 1500 AND category in ['A', 'B']
        # Index 2: price=110, volume=1200, category='A' ✓
        # Index 4: price=120, volume=1400, category='B' ✓
        # Index 5: price=125, volume=1500, category='A' ✓
        assert len(result) == 3
        assert (result['price'] >= 110).all()
        assert (result['volume'] <= 1500).all()
        assert result['category'].isin(['A', 'B']).all()
