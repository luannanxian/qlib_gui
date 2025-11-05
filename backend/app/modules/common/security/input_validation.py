"""
Input Validation and Sanitization

This module provides utilities for validating and sanitizing user input
to prevent injection attacks and ensure data integrity.
"""

import re
from typing import Optional
from loguru import logger


class InputValidator:
    """Validator for user input with security-focused sanitization"""

    # Maximum lengths for various inputs
    MAX_SEARCH_TERM_LENGTH = 200
    MAX_NAME_LENGTH = 255
    MAX_PATH_LENGTH = 1000
    MAX_JSON_SIZE_BYTES = 1_000_000  # 1 MB

    # Dangerous patterns that could indicate injection attempts
    SQL_INJECTION_PATTERNS = [
        r"(\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+)",
        r"(--|\#|/\*|\*/)",  # SQL comments
        r"(\bor\b.*=.*\b)",  # OR 1=1 patterns
        r"(;.*\s*(drop|delete|update|insert))",  # Multiple statements
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # ../
        r"\.\.",  # ..
        r"%2e%2e",  # URL encoded ..
        r"\.\.\\",  # ..\
    ]

    @classmethod
    def sanitize_search_term(cls, search_term: Optional[str]) -> Optional[str]:
        """
        Sanitize search term for database queries.

        Args:
            search_term: Raw search term from user

        Returns:
            Sanitized search term or None if invalid

        Raises:
            ValueError: If search term contains malicious patterns
        """
        if not search_term:
            return None

        # Trim whitespace
        search_term = search_term.strip()

        # Check length
        if len(search_term) > cls.MAX_SEARCH_TERM_LENGTH:
            raise ValueError(
                f"Search term too long (max {cls.MAX_SEARCH_TERM_LENGTH} characters)"
            )

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, search_term, re.IGNORECASE):
                logger.warning(
                    f"Potential SQL injection attempt detected in search term",
                    extra={"search_term": search_term, "pattern": pattern}
                )
                raise ValueError("Invalid search term: contains forbidden patterns")

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, search_term, re.IGNORECASE):
                logger.warning(
                    f"Potential XSS attempt detected in search term",
                    extra={"search_term": search_term}
                )
                raise ValueError("Invalid search term: contains forbidden patterns")

        # Additional sanitization: escape SQL LIKE wildcards if needed
        # Note: SQLAlchemy handles parameter binding, but we still sanitize
        # Remove or escape dangerous characters
        search_term = search_term.replace("\\", "")  # Remove backslashes

        return search_term

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """
        Sanitize name fields (dataset name, user name, etc.).

        Args:
            name: Raw name from user

        Returns:
            Sanitized name

        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError("Name cannot be empty")

        name = name.strip()

        if len(name) > cls.MAX_NAME_LENGTH:
            raise ValueError(f"Name too long (max {cls.MAX_NAME_LENGTH} characters)")

        if len(name) < 1:
            raise ValueError("Name must be at least 1 character")

        # Check for XSS patterns in names
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                raise ValueError("Invalid name: contains forbidden patterns")

        return name

    @classmethod
    def sanitize_file_path(cls, file_path: str) -> str:
        """
        Sanitize file paths to prevent path traversal attacks.

        Args:
            file_path: Raw file path from user

        Returns:
            Sanitized file path

        Raises:
            ValueError: If path contains traversal patterns
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        file_path = file_path.strip()

        if len(file_path) > cls.MAX_PATH_LENGTH:
            raise ValueError(f"Path too long (max {cls.MAX_PATH_LENGTH} characters)")

        # Check for path traversal patterns
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                logger.warning(
                    f"Potential path traversal attempt detected",
                    extra={"file_path": file_path}
                )
                raise ValueError("Invalid path: contains forbidden patterns")

        return file_path

    @classmethod
    def validate_json_size(cls, data: bytes | str) -> None:
        """
        Validate JSON payload size to prevent DoS attacks.

        Args:
            data: JSON data as bytes or string

        Raises:
            ValueError: If JSON is too large
        """
        size = len(data) if isinstance(data, bytes) else len(data.encode('utf-8'))

        if size > cls.MAX_JSON_SIZE_BYTES:
            raise ValueError(
                f"JSON payload too large: {size} bytes "
                f"(max {cls.MAX_JSON_SIZE_BYTES} bytes)"
            )

    @classmethod
    def sanitize_pagination_params(cls, skip: int, limit: int) -> tuple[int, int]:
        """
        Sanitize and validate pagination parameters.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (sanitized_skip, sanitized_limit)

        Raises:
            ValueError: If parameters are invalid
        """
        if skip < 0:
            raise ValueError("Skip must be non-negative")

        if limit < 1:
            raise ValueError("Limit must be positive")

        # Enforce maximum limit to prevent DoS
        MAX_LIMIT = 1000
        if limit > MAX_LIMIT:
            logger.warning(
                f"Limit {limit} exceeds maximum, capping to {MAX_LIMIT}"
            )
            limit = MAX_LIMIT

        return skip, limit


# Convenience functions
def sanitize_search(search: Optional[str]) -> Optional[str]:
    """Convenience function for sanitizing search terms"""
    return InputValidator.sanitize_search_term(search)


def sanitize_name(name: str) -> str:
    """Convenience function for sanitizing names"""
    return InputValidator.sanitize_name(name)


def sanitize_path(path: str) -> str:
    """Convenience function for sanitizing file paths"""
    return InputValidator.sanitize_file_path(path)


def validate_pagination(skip: int, limit: int) -> tuple[int, int]:
    """Convenience function for validating pagination"""
    return InputValidator.sanitize_pagination_params(skip, limit)
