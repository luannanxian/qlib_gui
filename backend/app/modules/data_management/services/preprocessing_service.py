"""
Data Preprocessing Service

Business logic layer for data preprocessing operations including:
- Missing value handling
- Outlier detection and handling
- Data transformation (normalization, standardization)
- Data filtering with multi-condition support
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from app.database.repositories.preprocessing import PreprocessingRuleRepository
from app.database.models.preprocessing import (
    MissingValueMethod, OutlierDetectionMethod, OutlierHandlingStrategy,
    TransformationType, FilterOperator
)


class PreprocessingService:
    """
    Service for data preprocessing operations

    Handles all preprocessing logic including missing values, outliers,
    transformations, and filtering.
    """

    def __init__(self, rule_repository: PreprocessingRuleRepository):
        """
        Initialize preprocessing service

        Args:
            rule_repository: Repository for preprocessing rules
        """
        self.rule_repo = rule_repository

    async def handle_missing_values(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Handle missing values in DataFrame based on configuration

        Args:
            df: Input DataFrame
            config: Configuration dict with:
                - method: Missing value handling method
                - columns: List of columns to process
                - fill_value: Optional constant value for constant_fill

        Returns:
            DataFrame with missing values handled

        Raises:
            KeyError: If specified columns don't exist

        Example:
            config = {
                "method": "mean_fill",
                "columns": ["price", "volume"]
            }
            result_df = await service.handle_missing_values(df, config)
        """
        if df.empty:
            return df

        method = config.get("method")
        columns = config.get("columns", [])

        # Validate columns exist
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

        result_df = df.copy()

        if method == MissingValueMethod.DELETE_ROWS.value:
            # Delete rows with any missing values in specified columns
            result_df = result_df.dropna(subset=columns)

        elif method == MissingValueMethod.MEAN_FILL.value:
            # Fill missing values with column mean
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    result_df[col] = result_df[col].fillna(result_df[col].mean())

        elif method == MissingValueMethod.MEDIAN_FILL.value:
            # Fill missing values with column median
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    result_df[col] = result_df[col].fillna(result_df[col].median())

        elif method == MissingValueMethod.FORWARD_FILL.value:
            # Forward fill (use previous value)
            result_df[columns] = result_df[columns].ffill()

        elif method == MissingValueMethod.BACKWARD_FILL.value:
            # Backward fill (use next value)
            result_df[columns] = result_df[columns].bfill()

        elif method == MissingValueMethod.CONSTANT_FILL.value:
            # Fill with constant value
            fill_value = config.get("fill_value", 0)
            result_df[columns] = result_df[columns].fillna(fill_value)

        logger.info(f"Handled missing values using {method} for columns: {columns}")
        return result_df

    async def detect_outliers(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.Series:
        """
        Detect outliers in DataFrame based on configuration

        Args:
            df: Input DataFrame
            config: Configuration dict with:
                - detection_method: Outlier detection method
                - threshold: Threshold value (for std_dev method)
                - lower_quantile: Lower quantile (for quantile method)
                - upper_quantile: Upper quantile (for quantile method)
                - columns: List of columns to check

        Returns:
            Boolean Series indicating outlier rows (True = outlier)

        Example:
            config = {
                "detection_method": "std_dev",
                "threshold": 3.0,
                "columns": ["price"]
            }
            outlier_mask = await service.detect_outliers(df, config)
        """
        detection_method = config.get("detection_method")
        columns = config.get("columns", [])

        # Initialize outlier mask (all False)
        outlier_mask = pd.Series([False] * len(df), index=df.index)

        if detection_method == OutlierDetectionMethod.STANDARD_DEVIATION.value:
            # Z-score method: |value - mean| / std > threshold
            threshold = config.get("threshold", 3.0)

            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    mean = df[col].mean()
                    std = df[col].std()

                    if std > 0:  # Avoid division by zero
                        z_scores = np.abs((df[col] - mean) / std)
                        outlier_mask |= (z_scores > threshold)

        elif detection_method == OutlierDetectionMethod.QUANTILE.value:
            # IQR method: value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR
            lower_q = config.get("lower_quantile", 0.25)
            upper_q = config.get("upper_quantile", 0.75)

            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    Q1 = df[col].quantile(lower_q)
                    Q3 = df[col].quantile(upper_q)
                    IQR = Q3 - Q1

                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    outlier_mask |= ((df[col] < lower_bound) | (df[col] > upper_bound))

        logger.info(f"Detected {outlier_mask.sum()} outliers using {detection_method}")
        return outlier_mask

    async def handle_outliers(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Handle outliers in DataFrame based on configuration

        Args:
            df: Input DataFrame
            config: Configuration dict with:
                - detection_method: Outlier detection method
                - handling: Outlier handling strategy
                - threshold: Detection threshold
                - columns: List of columns to process

        Returns:
            DataFrame with outliers handled

        Example:
            config = {
                "detection_method": "std_dev",
                "threshold": 3.0,
                "handling": "cap",
                "columns": ["price"]
            }
            result_df = await service.handle_outliers(df, config)
        """
        # First detect outliers
        outlier_mask = await self.detect_outliers(df, config)

        result_df = df.copy()
        handling = config.get("handling")
        columns = config.get("columns", [])

        if handling == OutlierHandlingStrategy.DELETE.value:
            # Delete rows with outliers
            result_df = result_df[~outlier_mask]

        elif handling == OutlierHandlingStrategy.CAP.value:
            # Cap outliers to threshold (winsorization)
            detection_method = config.get("detection_method")

            if detection_method == OutlierDetectionMethod.STANDARD_DEVIATION.value:
                threshold = config.get("threshold", 3.0)

                for col in columns:
                    if pd.api.types.is_numeric_dtype(result_df[col]):
                        mean = result_df[col].mean()
                        std = result_df[col].std()

                        if std > 0:
                            lower_bound = mean - threshold * std
                            upper_bound = mean + threshold * std

                            result_df[col] = result_df[col].clip(lower=lower_bound, upper=upper_bound)

            elif detection_method == OutlierDetectionMethod.QUANTILE.value:
                lower_q = config.get("lower_quantile", 0.25)
                upper_q = config.get("upper_quantile", 0.75)

                for col in columns:
                    if pd.api.types.is_numeric_dtype(result_df[col]):
                        Q1 = result_df[col].quantile(lower_q)
                        Q3 = result_df[col].quantile(upper_q)
                        IQR = Q3 - Q1

                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR

                        result_df[col] = result_df[col].clip(lower=lower_bound, upper=upper_bound)

        elif handling == OutlierHandlingStrategy.REPLACE_MEAN.value:
            # Replace outliers with column mean
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    mean_val = result_df.loc[~outlier_mask, col].mean()
                    result_df.loc[outlier_mask, col] = mean_val

        elif handling == OutlierHandlingStrategy.REPLACE_MEDIAN.value:
            # Replace outliers with column median
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    median_val = result_df.loc[~outlier_mask, col].median()
                    result_df.loc[outlier_mask, col] = median_val

        logger.info(f"Handled {outlier_mask.sum()} outliers using {handling} strategy")
        return result_df

    async def transform_data(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Transform data based on configuration

        Args:
            df: Input DataFrame
            config: Configuration dict with:
                - type: Transformation type
                - columns: List of columns to transform
                - range: Target range for normalization [min, max]

        Returns:
            DataFrame with transformed data

        Example:
            config = {
                "type": "normalize",
                "columns": ["price"],
                "range": [0, 1]
            }
            result_df = await service.transform_data(df, config)
        """
        if df.empty:
            return df

        result_df = df.copy()
        transform_type = config.get("type")
        columns = config.get("columns", [])

        if transform_type == TransformationType.NORMALIZE.value:
            # Min-Max normalization
            target_range = config.get("range", [0, 1])
            target_min, target_max = target_range

            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    col_min = result_df[col].min()
                    col_max = result_df[col].max()

                    if col_max > col_min:  # Avoid division by zero
                        # Normalize to [0, 1] then scale to target range
                        normalized = (result_df[col] - col_min) / (col_max - col_min)
                        result_df[col] = normalized * (target_max - target_min) + target_min

        elif transform_type == TransformationType.STANDARDIZE.value:
            # Z-score standardization
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    mean = result_df[col].mean()
                    std = result_df[col].std()

                    if std > 0:  # Avoid division by zero
                        result_df[col] = (result_df[col] - mean) / std

        elif transform_type == TransformationType.LOG_TRANSFORM.value:
            # Logarithmic transformation
            for col in columns:
                if pd.api.types.is_numeric_dtype(result_df[col]):
                    # Add small constant to avoid log(0)
                    result_df[col] = np.log(result_df[col] + 1)

        logger.info(f"Transformed data using {transform_type} for columns: {columns}")
        return result_df

    async def filter_data(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Filter data based on multiple conditions

        Args:
            df: Input DataFrame
            config: Configuration dict with:
                - conditions: List of filter conditions
                - logic: Logical operator ("AND" or "OR")

        Returns:
            Filtered DataFrame

        Example:
            config = {
                "conditions": [
                    {"column": "price", "operator": "gt", "value": 100},
                    {"column": "volume", "operator": "lt", "value": 5000}
                ],
                "logic": "AND"
            }
            result_df = await service.filter_data(df, config)
        """
        conditions = config.get("conditions", [])
        logic = config.get("logic", "AND").upper()

        if not conditions:
            return df

        # Build filter masks for each condition
        masks = []

        for condition in conditions:
            column = condition["column"]
            operator = condition["operator"]
            value = condition["value"]

            if column not in df.columns:
                logger.warning(f"Column {column} not found in DataFrame, skipping condition")
                continue

            # Build condition mask based on operator
            if operator == FilterOperator.EQUALS.value:
                mask = df[column] == value
            elif operator == FilterOperator.NOT_EQUALS.value:
                mask = df[column] != value
            elif operator == FilterOperator.GREATER_THAN.value:
                mask = df[column] > value
            elif operator == FilterOperator.GREATER_EQUAL.value:
                mask = df[column] >= value
            elif operator == FilterOperator.LESS_THAN.value:
                mask = df[column] < value
            elif operator == FilterOperator.LESS_EQUAL.value:
                mask = df[column] <= value
            elif operator == FilterOperator.IN.value:
                mask = df[column].isin(value if isinstance(value, list) else [value])
            elif operator == FilterOperator.NOT_IN.value:
                mask = ~df[column].isin(value if isinstance(value, list) else [value])
            elif operator == FilterOperator.CONTAINS.value:
                mask = df[column].astype(str).str.contains(str(value), na=False)
            elif operator == FilterOperator.IS_NULL.value:
                mask = df[column].isna()
            elif operator == FilterOperator.NOT_NULL.value:
                mask = df[column].notna()
            else:
                logger.warning(f"Unknown operator: {operator}, skipping condition")
                continue

            masks.append(mask)

        if not masks:
            return df

        # Combine masks based on logic
        if logic == "AND":
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask &= mask
        else:  # OR
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask |= mask

        result_df = df[final_mask]
        logger.info(f"Filtered data: {len(result_df)} rows remaining from {len(df)}")
        return result_df
