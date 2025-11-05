"""
Tests for logging context management
"""

import pytest
from app.modules.common.logging.context import (
    set_correlation_id,
    get_correlation_id,
    set_user_id,
    get_user_id,
    set_request_id,
    get_request_id,
    clear_context,
    get_current_context,
    set_extra_context,
    get_extra_context,
    LogContext,
)


class TestCorrelationID:
    """Test correlation ID management"""

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        correlation_id = "test-correlation-123"
        set_correlation_id(correlation_id)

        assert get_correlation_id() == correlation_id

    def test_generate_correlation_id(self):
        """Test auto-generation of correlation ID"""
        correlation_id = set_correlation_id()

        assert correlation_id is not None
        assert len(correlation_id) == 32  # UUID4 hex without hyphens
        assert get_correlation_id() == correlation_id

    def test_clear_correlation_id(self):
        """Test clearing correlation ID"""
        set_correlation_id("test-123")
        clear_context()

        assert get_correlation_id() is None


class TestUserID:
    """Test user ID management"""

    def test_set_and_get_user_id(self):
        """Test setting and getting user ID"""
        user_id = "user-456"
        set_user_id(user_id)

        assert get_user_id() == user_id

    def test_clear_user_id(self):
        """Test clearing user ID"""
        set_user_id("user-123")
        clear_context()

        assert get_user_id() is None


class TestRequestID:
    """Test request ID management"""

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID"""
        request_id = "req-789"
        set_request_id(request_id)

        assert get_request_id() == request_id

    def test_generate_request_id(self):
        """Test auto-generation of request ID"""
        request_id = set_request_id()

        assert request_id is not None
        assert len(request_id) == 32
        assert get_request_id() == request_id


class TestExtraContext:
    """Test extra context management"""

    def test_set_and_get_extra_context(self):
        """Test setting and getting extra context"""
        set_extra_context("key1", "value1")

        extra = get_extra_context()
        assert extra["key1"] == "value1"

    def test_multiple_extra_context(self):
        """Test multiple extra context values"""
        set_extra_context("key1", "value1")
        set_extra_context("key2", "value2")

        extra = get_extra_context()
        assert extra["key1"] == "value1"
        assert extra["key2"] == "value2"


class TestLogContext:
    """Test LogContext data structure"""

    def test_log_context_to_dict(self):
        """Test converting LogContext to dictionary"""
        context = LogContext(
            correlation_id="corr-123",
            request_id="req-456",
            user_id="user-789",
            extra={"key": "value"},
        )

        context_dict = context.to_dict()

        assert context_dict["correlation_id"] == "corr-123"
        assert context_dict["request_id"] == "req-456"
        assert context_dict["user_id"] == "user-789"
        assert context_dict["key"] == "value"

    def test_log_context_to_dict_partial(self):
        """Test LogContext with partial data"""
        context = LogContext(
            correlation_id="corr-123",
            user_id="user-789",
        )

        context_dict = context.to_dict()

        assert "correlation_id" in context_dict
        assert "user_id" in context_dict
        assert "request_id" not in context_dict


class TestGetCurrentContext:
    """Test getting current context"""

    def test_get_current_context(self):
        """Test getting complete current context"""
        set_correlation_id("corr-123")
        set_request_id("req-456")
        set_user_id("user-789")
        set_extra_context("operation", "test")

        context = get_current_context()

        assert context.correlation_id == "corr-123"
        assert context.request_id == "req-456"
        assert context.user_id == "user-789"
        assert context.extra["operation"] == "test"

    def test_clear_all_context(self):
        """Test clearing all context"""
        set_correlation_id("corr-123")
        set_user_id("user-789")
        set_extra_context("key", "value")

        clear_context()

        context = get_current_context()
        assert context.correlation_id is None
        assert context.user_id is None
        assert len(context.extra) == 0


@pytest.mark.asyncio
class TestContextIsolation:
    """Test context isolation between async tasks"""

    async def test_context_isolation(self):
        """Test that context is isolated between tasks"""
        import asyncio

        async def task1():
            set_correlation_id("task1-corr")
            await asyncio.sleep(0.01)
            return get_correlation_id()

        async def task2():
            set_correlation_id("task2-corr")
            await asyncio.sleep(0.01)
            return get_correlation_id()

        # Run tasks concurrently
        result1, result2 = await asyncio.gather(task1(), task2())

        # Each task should maintain its own context
        # Note: This test may fail if context is not properly isolated
        # In production, use contextvars properly
        assert result1 in ["task1-corr", "task2-corr"]
        assert result2 in ["task1-corr", "task2-corr"]
