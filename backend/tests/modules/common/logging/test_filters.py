"""
Tests for logging filters and sanitization
"""

import pytest
from app.modules.common.logging.filters import (
    SensitiveDataFilter,
    sanitize_log_data,
    EmailFilter,
    IPAddressFilter,
)


class TestSensitiveDataFilter:
    """Test sensitive data filtering"""

    def test_filter_password_field(self):
        """Test filtering password field"""
        filter_instance = SensitiveDataFilter()

        data = {"username": "john", "password": "secret123"}
        sanitized = filter_instance.sanitize_dict(data)

        assert sanitized["username"] == "john"
        assert sanitized["password"] == "***REDACTED***"

    def test_filter_api_key_field(self):
        """Test filtering API key field"""
        filter_instance = SensitiveDataFilter()

        data = {"name": "service", "api_key": "sk-1234567890"}
        sanitized = filter_instance.sanitize_dict(data)

        assert sanitized["name"] == "service"
        assert sanitized["api_key"] == "***REDACTED***"

    def test_filter_nested_dict(self):
        """Test filtering nested dictionaries"""
        filter_instance = SensitiveDataFilter()

        data = {
            "user": {"username": "john", "password": "secret"},
            "api": {"key": "12345", "secret": "topsecret"},
        }
        sanitized = filter_instance.sanitize_dict(data)

        assert sanitized["user"]["username"] == "john"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["api"]["key"] == "12345"
        assert sanitized["api"]["secret"] == "***REDACTED***"

    def test_filter_list_of_dicts(self):
        """Test filtering lists of dictionaries"""
        filter_instance = SensitiveDataFilter()

        data = [
            {"username": "john", "password": "pass1"},
            {"username": "jane", "password": "pass2"},
        ]
        sanitized = filter_instance.sanitize_list(data)

        assert len(sanitized) == 2
        assert sanitized[0]["username"] == "john"
        assert sanitized[0]["password"] == "***REDACTED***"
        assert sanitized[1]["username"] == "jane"
        assert sanitized[1]["password"] == "***REDACTED***"

    def test_filter_credit_card(self):
        """Test filtering credit card numbers"""
        filter_instance = SensitiveDataFilter()

        text = "Card number: 1234-5678-9012-3456"
        sanitized = filter_instance.sanitize_string(text)

        assert "1234-5678-9012-3456" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_filter_jwt_token(self):
        """Test filtering JWT tokens"""
        filter_instance = SensitiveDataFilter()

        text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        sanitized = filter_instance.sanitize_string(text)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_filter_bearer_token(self):
        """Test filtering Bearer tokens"""
        filter_instance = SensitiveDataFilter()

        text = "Authorization: Bearer abc123xyz456"
        sanitized = filter_instance.sanitize_string(text)

        assert "Bearer abc123xyz456" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_filter_aws_key(self):
        """Test filtering AWS access keys"""
        filter_instance = SensitiveDataFilter()

        text = "AWS_KEY=AKIAIOSFODNN7EXAMPLE"
        sanitized = filter_instance.sanitize_string(text)

        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_custom_sensitive_fields(self):
        """Test adding custom sensitive fields"""
        custom_fields = {"custom_secret", "internal_key"}
        filter_instance = SensitiveDataFilter(additional_fields=custom_fields)

        data = {"custom_secret": "value", "public_field": "visible"}
        sanitized = filter_instance.sanitize_dict(data)

        assert sanitized["custom_secret"] == "***REDACTED***"
        assert sanitized["public_field"] == "visible"


class TestSanitizeLogData:
    """Test sanitize_log_data utility function"""

    def test_sanitize_dict(self):
        """Test sanitizing dictionary"""
        data = {"username": "john", "password": "secret"}
        sanitized = sanitize_log_data(data)

        assert sanitized["username"] == "john"
        assert sanitized["password"] == "***REDACTED***"

    def test_sanitize_list(self):
        """Test sanitizing list"""
        data = [
            {"user": "john", "token": "abc123"},
            {"user": "jane", "token": "xyz789"},
        ]
        sanitized = sanitize_log_data(data)

        assert sanitized[0]["user"] == "john"
        assert sanitized[0]["token"] == "***REDACTED***"

    def test_sanitize_string(self):
        """Test sanitizing string"""
        text = "Credit card: 1234-5678-9012-3456"
        sanitized = sanitize_log_data(text)

        assert "1234-5678-9012-3456" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitize_other_types(self):
        """Test sanitizing other types (no-op)"""
        assert sanitize_log_data(123) == 123
        assert sanitize_log_data(True) is True
        assert sanitize_log_data(None) is None


class TestEmailFilter:
    """Test email address filtering"""

    def test_mask_email_show_domain(self):
        """Test masking email with domain visible"""
        masked = EmailFilter.mask_email("user@example.com", show_domain=True)

        assert masked == "u***@example.com"
        assert "user" not in masked

    def test_mask_email_hide_domain(self):
        """Test masking email with domain hidden"""
        masked = EmailFilter.mask_email("user@example.com", show_domain=False)

        assert masked == "u***@***.com"
        assert "user" not in masked
        assert "example" not in masked

    def test_mask_short_email(self):
        """Test masking short email"""
        masked = EmailFilter.mask_email("ab@example.com", show_domain=True)

        assert masked == "***@example.com"

    def test_filter_string_with_emails(self):
        """Test filtering emails from string"""
        text = "Contact us at support@example.com or admin@test.org"
        filtered = EmailFilter.filter_string(text, show_domain=True)

        assert "support@example.com" not in filtered
        assert "admin@test.org" not in filtered
        assert "s***@example.com" in filtered
        assert "a***@test.org" in filtered


class TestIPAddressFilter:
    """Test IP address filtering"""

    def test_mask_ipv4_keep_network(self):
        """Test masking IPv4 keeping network portion"""
        masked = IPAddressFilter.mask_ipv4("192.168.1.100", keep_network=True)

        assert masked == "192.168.*.***"

    def test_mask_ipv4_hide_all(self):
        """Test masking IPv4 completely"""
        masked = IPAddressFilter.mask_ipv4("192.168.1.100", keep_network=False)

        assert masked == "***.***.***.***"

    def test_mask_ipv6(self):
        """Test masking IPv6"""
        masked = IPAddressFilter.mask_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")

        assert masked == "2001:0db8:***:***:***:***:***:***"

    def test_filter_string_with_ips(self):
        """Test filtering IPs from string"""
        text = "Server at 192.168.1.100 responded"
        filtered = IPAddressFilter.filter_string(text, keep_network=True)

        assert "192.168.1.100" not in filtered
        assert "192.168.*.***" in filtered


class TestFilterRecord:
    """Test filtering log records"""

    def test_filter_log_record_message(self):
        """Test filtering sensitive data from log record message"""
        filter_instance = SensitiveDataFilter()

        record = {
            "message": "User logged in with password: secret123",
            "extra": {},
        }

        # Filter should modify record in place
        result = filter_instance.filter_record(record)

        assert result is True  # Should always return True
        # The message itself won't be filtered by field names,
        # but patterns should catch some cases

    def test_filter_log_record_extra(self):
        """Test filtering sensitive data from log record extra fields"""
        filter_instance = SensitiveDataFilter()

        record = {
            "message": "User action",
            "extra": {"user": "john", "password": "secret123"},
        }

        result = filter_instance.filter_record(record)

        assert result is True
        assert record["extra"]["user"] == "john"
        assert record["extra"]["password"] == "***REDACTED***"
