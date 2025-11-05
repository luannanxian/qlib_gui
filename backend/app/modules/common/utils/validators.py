"""Common validation utilities"""

import os
from pathlib import Path
from typing import Optional


def validate_file_path(
    file_path: str,
    allowed_base: Optional[str] = None
) -> str:
    """
    Validate file path to prevent path traversal attacks.

    Args:
        file_path: The file path to validate
        allowed_base: Base directory that file must be within (default: /data)

    Returns:
        Validated absolute file path

    Raises:
        ValueError: If path is invalid or outside allowed directory

    Examples:
        >>> validate_file_path("/data/test.csv")
        '/data/test.csv'
        >>> validate_file_path("../../../etc/passwd")  # doctest: +SKIP
        ValueError: Path traversal detected
    """
    if allowed_base is None:
        allowed_base = os.environ.get("DATA_DIR", "/data")

    try:
        # Resolve to absolute path (removes .. and .)
        abs_path = Path(file_path).resolve()
        allowed_base_path = Path(allowed_base).resolve()

        # Check if path is within allowed directory
        try:
            abs_path.relative_to(allowed_base_path)
        except ValueError:
            raise ValueError(
                f"Path '{file_path}' is outside allowed directory '{allowed_base}'. "
                f"Resolved to: {abs_path}"
            )

        return str(abs_path)

    except Exception as e:
        if isinstance(e, ValueError) and "outside allowed directory" in str(e):
            raise
        raise ValueError(f"Invalid file path '{file_path}': {e}")
