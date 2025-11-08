"""
Data Serialization Utilities

Utilities for converting data types to JSON-serializable formats.
Handles numpy arrays, pandas types, and datetime objects.
"""

import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Any, Dict, List, Union


def convert_numpy_to_native(data: Any) -> Any:
    """
    Convert numpy types to Python native types recursively.

    Handles:
    - numpy arrays -> lists
    - numpy scalars -> Python scalars
    - pandas Timestamp -> ISO string
    - datetime objects -> ISO string
    - nested dictionaries and lists

    Args:
        data: Data to convert (can be any type)

    Returns:
        Data with all numpy/pandas types converted to native Python types
    """
    # Handle numpy arrays
    if isinstance(data, np.ndarray):
        return data.tolist()

    # Handle numpy scalars
    if isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    if isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
        return float(data)
    if isinstance(data, np.bool_):
        return bool(data)

    # Handle pandas Timestamp
    if isinstance(data, pd.Timestamp):
        return data.isoformat()

    # Handle datetime objects
    if isinstance(data, (datetime, date)):
        return data.isoformat()

    # Handle pandas Series
    if isinstance(data, pd.Series):
        return convert_numpy_to_native(data.tolist())

    # Handle pandas Index
    if isinstance(data, pd.Index):
        return convert_numpy_to_native(data.tolist())

    # Handle dictionaries recursively
    if isinstance(data, dict):
        return {key: convert_numpy_to_native(value) for key, value in data.items()}

    # Handle lists recursively
    if isinstance(data, list):
        return [convert_numpy_to_native(item) for item in data]

    # Handle tuples recursively (convert to list)
    if isinstance(data, tuple):
        return [convert_numpy_to_native(item) for item in data]

    # Return as-is for native Python types
    return data


def convert_datetime_fields(data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
    """
    Convert datetime fields in a dictionary to ISO format strings.

    Args:
        data: Dictionary containing data
        fields: Optional list of field names to convert. If None, converts all datetime objects.

    Returns:
        Dictionary with datetime fields converted to ISO strings
    """
    result = data.copy()

    if fields:
        # Convert specified fields only
        for field in fields:
            if field in result and isinstance(result[field], (datetime, date, pd.Timestamp)):
                result[field] = result[field].isoformat()
    else:
        # Convert all datetime fields
        for key, value in result.items():
            if isinstance(value, (datetime, date, pd.Timestamp)):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = convert_datetime_fields(value)
            elif isinstance(value, list):
                result[key] = [
                    convert_datetime_fields(item) if isinstance(item, dict)
                    else item.isoformat() if isinstance(item, (datetime, date, pd.Timestamp))
                    else item
                    for item in value
                ]

    return result


def prepare_chart_data_for_serialization(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare chart data for JSON serialization.

    Converts numpy arrays and datetime objects to native Python types.
    Specifically designed for chart data responses.

    Args:
        data: Chart data dictionary

    Returns:
        Serialization-ready data
    """
    # Convert all numpy types
    serialized = convert_numpy_to_native(data)

    # Ensure all datetime fields are converted
    return convert_datetime_fields(serialized)


def prepare_annotation_for_storage(annotation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare annotation data for database storage.

    Converts datetime objects to ISO strings for JSON storage in database.

    Args:
        annotation: Annotation dictionary

    Returns:
        Storage-ready annotation data
    """
    return convert_datetime_fields(annotation, fields=['date', 'created_at', 'updated_at'])
