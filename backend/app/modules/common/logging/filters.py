"""
Log Filters Module

Provides filtering and sanitization of sensitive data in logs:
- PII (Personally Identifiable Information)
- Secrets (passwords, API keys, tokens)
- Credit card numbers
- Email addresses (optional)
- IP addresses (optional)
"""

import re
from typing import Dict, Any, List, Set, Optional, Pattern
from copy import deepcopy


class SensitiveDataFilter:
    """
    Filter to sanitize sensitive data from log records.

    Removes or masks PII, secrets, and other sensitive information.
    """

    # Sensitive field names (case-insensitive)
    SENSITIVE_FIELDS: Set[str] = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "api_key",
        "apikey",
        "api-key",
        "access_token",
        "refresh_token",
        "token",
        "authorization",
        "auth",
        "credit_card",
        "creditcard",
        "card_number",
        "cvv",
        "ssn",
        "social_security",
        "private_key",
        "privatekey",
        "session_id",
        "cookie",
        "csrf_token",
        "jwt",
    }

    # Regex patterns for sensitive data
    PATTERNS: Dict[str, Pattern] = {
        # Credit card numbers (basic pattern)
        "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        # Social Security Numbers
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        # API keys (common formats)
        "api_key": re.compile(r"(?i)(api[_-]?key|apikey)[\s:=]+['\"]?([a-zA-Z0-9_\-]{20,})['\"]?"),
        # Bearer tokens
        "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        # JWT tokens
        "jwt": re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"),
        # AWS keys
        "aws_key": re.compile(r"(?i)(AKIA|ASIA)[A-Z0-9]{16}"),
        # Private keys
        "private_key": re.compile(r"-----BEGIN.*PRIVATE KEY-----.*-----END.*PRIVATE KEY-----", re.DOTALL),
        # Password in URLs
        "password_in_url": re.compile(r"://[^:]+:([^@]+)@"),
    }

    # Mask string
    MASK = "***REDACTED***"

    def __init__(
        self,
        additional_fields: Optional[Set[str]] = None,
        additional_patterns: Optional[Dict[str, Pattern]] = None,
    ):
        """
        Initialize sensitive data filter.

        Args:
            additional_fields: Additional field names to filter
            additional_patterns: Additional regex patterns to apply
        """
        self.sensitive_fields = self.SENSITIVE_FIELDS.copy()
        if additional_fields:
            self.sensitive_fields.update(additional_fields)

        self.patterns = self.PATTERNS.copy()
        if additional_patterns:
            self.patterns.update(additional_patterns)

    def filter_record(self, record: Dict[str, Any]) -> bool:
        """
        Filter sensitive data from a log record.

        Args:
            record: Loguru record dictionary

        Returns:
            True to process the record, False to skip it
        """
        # Sanitize message
        if record.get("message"):
            record["message"] = self.sanitize_string(record["message"])

        # Sanitize extra fields
        if record.get("extra"):
            record["extra"] = self.sanitize_dict(record["extra"])

        # Always return True to process the record
        return True

    def sanitize_string(self, text: str) -> str:
        """
        Sanitize sensitive data from a string using regex patterns.

        Args:
            text: Input string

        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return text

        # Apply all patterns
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == "password_in_url":
                # Special handling for passwords in URLs
                text = pattern.sub(f"://***:{self.MASK}@", text)
            else:
                text = pattern.sub(self.MASK, text)

        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize sensitive data from a dictionary.

        Args:
            data: Input dictionary

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}

        for key, value in data.items():
            # Check if key is sensitive
            if key.lower() in self.sensitive_fields:
                sanitized[key] = self.MASK
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize lists
                sanitized[key] = self.sanitize_list(value)
            elif isinstance(value, str):
                # Sanitize strings with regex patterns
                sanitized[key] = self.sanitize_string(value)
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Sanitize sensitive data from a list.

        Args:
            data: Input list

        Returns:
            Sanitized list
        """
        if not isinstance(data, list):
            return data

        sanitized = []

        for item in data:
            if isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            elif isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            else:
                sanitized.append(item)

        return sanitized


def sanitize_log_data(data: Any) -> Any:
    """
    Utility function to sanitize data before logging.

    Args:
        data: Data to sanitize (dict, list, string, or other)

    Returns:
        Sanitized data

    Example:
        >>> user_data = {"username": "john", "password": "secret123"}
        >>> log.info("User data", extra=sanitize_log_data(user_data))
    """
    filter_instance = SensitiveDataFilter()

    if isinstance(data, dict):
        return filter_instance.sanitize_dict(data)
    elif isinstance(data, list):
        return filter_instance.sanitize_list(data)
    elif isinstance(data, str):
        return filter_instance.sanitize_string(data)
    else:
        return data


class EmailFilter:
    """
    Optional filter for email addresses.

    Can be used to mask or partially mask email addresses in logs.
    """

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )

    @staticmethod
    def mask_email(email: str, show_domain: bool = True) -> str:
        """
        Mask an email address.

        Args:
            email: Email address to mask
            show_domain: Whether to show the domain part

        Returns:
            Masked email

        Example:
            >>> EmailFilter.mask_email("user@example.com")
            "u***@example.com"
            >>> EmailFilter.mask_email("user@example.com", show_domain=False)
            "u***@***.com"
        """
        if "@" not in email:
            return email

        local, domain = email.split("@", 1)

        # Mask local part
        if len(local) > 2:
            masked_local = local[0] + "***"
        else:
            masked_local = "***"

        # Optionally mask domain
        if show_domain:
            return f"{masked_local}@{domain}"
        else:
            # Show only TLD
            parts = domain.split(".")
            if len(parts) > 1:
                tld = parts[-1]
                return f"{masked_local}@***.{tld}"
            else:
                return f"{masked_local}@***"

    @classmethod
    def filter_string(cls, text: str, show_domain: bool = True) -> str:
        """
        Filter email addresses from a string.

        Args:
            text: Input string
            show_domain: Whether to show the domain part

        Returns:
            String with masked email addresses
        """

        def replace_email(match):
            return cls.mask_email(match.group(0), show_domain)

        return cls.EMAIL_PATTERN.sub(replace_email, text)


class IPAddressFilter:
    """
    Optional filter for IP addresses.

    Can be used to mask IP addresses for privacy compliance (GDPR, etc.)
    """

    IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    IPV6_PATTERN = re.compile(
        r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b"
    )

    @staticmethod
    def mask_ipv4(ip: str, keep_network: bool = True) -> str:
        """
        Mask an IPv4 address.

        Args:
            ip: IPv4 address to mask
            keep_network: Whether to keep the network portion (first 2 octets)

        Returns:
            Masked IP address

        Example:
            >>> IPAddressFilter.mask_ipv4("192.168.1.100")
            "192.168.*.***"
            >>> IPAddressFilter.mask_ipv4("192.168.1.100", keep_network=False)
            "***.***.***.***"
        """
        if keep_network:
            parts = ip.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.*.***"
        return "***.***.***.***"

    @staticmethod
    def mask_ipv6(ip: str) -> str:
        """
        Mask an IPv6 address.

        Args:
            ip: IPv6 address to mask

        Returns:
            Masked IP address
        """
        parts = ip.split(":")
        if len(parts) > 2:
            return f"{parts[0]}:{parts[1]}:***:***:***:***:***:***"
        return "***:***:***:***:***:***:***:***"

    @classmethod
    def filter_string(cls, text: str, keep_network: bool = True) -> str:
        """
        Filter IP addresses from a string.

        Args:
            text: Input string
            keep_network: Whether to keep the network portion for IPv4

        Returns:
            String with masked IP addresses
        """
        # Mask IPv4
        text = cls.IPV4_PATTERN.sub(
            lambda m: cls.mask_ipv4(m.group(0), keep_network), text
        )

        # Mask IPv6
        text = cls.IPV6_PATTERN.sub(
            lambda m: cls.mask_ipv6(m.group(0)), text
        )

        return text


class PerformanceFilter:
    """
    Filter to mark slow operations for special attention.
    """

    def __init__(self, slow_threshold_ms: float = 1000.0):
        """
        Initialize performance filter.

        Args:
            slow_threshold_ms: Threshold in milliseconds for slow operations
        """
        self.slow_threshold_ms = slow_threshold_ms

    def filter_record(self, record: Dict[str, Any]) -> bool:
        """
        Add performance flags to log records.

        Args:
            record: Loguru record dictionary

        Returns:
            True to process the record
        """
        # Check execution time
        if record["extra"].get("execution_time_ms"):
            exec_time = record["extra"]["execution_time_ms"]
            if exec_time > self.slow_threshold_ms:
                record["extra"]["slow_operation"] = True

        # Check database query time
        if record["extra"].get("query_time_ms"):
            query_time = record["extra"]["query_time_ms"]
            if query_time > self.slow_threshold_ms / 10:  # 100ms for queries
                record["extra"]["slow_query"] = True

        return True
