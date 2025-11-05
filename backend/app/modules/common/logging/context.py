"""
Log Context Module

Provides context management for logging with:
- Correlation IDs for request tracing
- User IDs for user-specific logging
- Request IDs for request identification
- Thread-safe context variables using contextvars
"""

import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


# Context variables for thread-safe storage
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_extra_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("extra_context", default=None)


@dataclass
class LogContext:
    """
    Logging context data structure.

    Holds all contextual information for a request/operation.
    """

    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        context = {}

        if self.correlation_id:
            context["correlation_id"] = self.correlation_id
        if self.request_id:
            context["request_id"] = self.request_id
        if self.user_id:
            context["user_id"] = self.user_id
        if self.session_id:
            context["session_id"] = self.session_id
        if self.extra:
            context.update(self.extra)

        return context


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID.

    Returns:
        UUID4 string without hyphens
    """
    return uuid.uuid4().hex


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set the correlation ID in context.

    Args:
        correlation_id: Correlation ID to set. If None, generates a new one.

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    _correlation_id.set(correlation_id)
    return correlation_id


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Request ID or None if not set
    """
    return _request_id.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the request ID in context.

    Args:
        request_id: Request ID to set. If None, generates a new one.

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = uuid.uuid4().hex
    _request_id.set(request_id)
    return request_id


def get_user_id() -> Optional[str]:
    """
    Get the current user ID from context.

    Returns:
        User ID or None if not set
    """
    return _user_id.get()


def set_user_id(user_id: Optional[str]) -> None:
    """
    Set the user ID in context.

    Args:
        user_id: User ID to set
    """
    _user_id.set(user_id)


def get_session_id() -> Optional[str]:
    """
    Get the current session ID from context.

    Returns:
        Session ID or None if not set
    """
    return _session_id.get()


def set_session_id(session_id: Optional[str]) -> None:
    """
    Set the session ID in context.

    Args:
        session_id: Session ID to set
    """
    _session_id.set(session_id)


def get_extra_context() -> Dict[str, Any]:
    """
    Get extra context data.

    Returns:
        Dictionary of extra context data
    """
    context = _extra_context.get()
    return context if context is not None else {}


def set_extra_context(key: str, value: Any) -> None:
    """
    Set a value in extra context.

    Args:
        key: Context key
        value: Context value
    """
    extra = _extra_context.get()
    if extra is None:
        extra = {}
    extra[key] = value
    _extra_context.set(extra)


def update_extra_context(data: Dict[str, Any]) -> None:
    """
    Update extra context with multiple values.

    Args:
        data: Dictionary of context data to add
    """
    extra = _extra_context.get()
    if extra is None:
        extra = {}
    extra.update(data)
    _extra_context.set(extra)


def get_current_context() -> LogContext:
    """
    Get the complete current logging context.

    Returns:
        LogContext object with all current context data
    """
    return LogContext(
        correlation_id=get_correlation_id(),
        request_id=get_request_id(),
        user_id=get_user_id(),
        session_id=get_session_id(),
        extra=get_extra_context(),
    )


def clear_context() -> None:
    """
    Clear all context variables.

    Should be called at the end of request processing.
    """
    _correlation_id.set(None)
    _request_id.set(None)
    _user_id.set(None)
    _session_id.set(None)
    _extra_context.set(None)


class ContextualLogger:
    """
    Logger wrapper that automatically includes context in all log calls.

    Example:
        >>> from loguru import logger
        >>> set_correlation_id("abc123")
        >>> set_user_id("user_456")
        >>> contextual_logger = ContextualLogger(logger)
        >>> contextual_logger.info("User action")  # Includes correlation_id and user_id
    """

    def __init__(self, logger_instance):
        """
        Initialize contextual logger.

        Args:
            logger_instance: Loguru logger instance
        """
        self._logger = logger_instance

    def _bind_context(self):
        """Bind current context to logger."""
        context = get_current_context().to_dict()
        return self._logger.bind(**context)

    def trace(self, message: str, **kwargs):
        """Log trace message with context."""
        self._bind_context().trace(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._bind_context().debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._bind_context().info(message, **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message with context."""
        self._bind_context().success(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._bind_context().warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._bind_context().error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._bind_context().critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with context."""
        self._bind_context().exception(message, **kwargs)


def with_context(**context_data):
    """
    Decorator to set context for a function execution.

    Args:
        **context_data: Context data to set

    Example:
        >>> @with_context(operation="data_processing")
        >>> async def process_data():
        >>>     # All logs in this function will include operation="data_processing"
        >>>     pass
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Store previous extra context (copy to avoid mutations)
            previous_extra = get_extra_context()
            previous_extra_copy = previous_extra.copy() if previous_extra else None

            # Update context
            update_extra_context(context_data)

            try:
                return await func(*args, **kwargs)
            finally:
                # Restore previous context
                _extra_context.set(previous_extra_copy)

        def sync_wrapper(*args, **kwargs):
            # Store previous extra context (copy to avoid mutations)
            previous_extra = get_extra_context()
            previous_extra_copy = previous_extra.copy() if previous_extra else None

            # Update context
            update_extra_context(context_data)

            try:
                return func(*args, **kwargs)
            finally:
                # Restore previous context
                _extra_context.set(previous_extra_copy)

        # Check if function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
