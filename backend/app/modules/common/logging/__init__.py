"""
Structured Logging Module for Qlib-UI

This module provides comprehensive structured logging capabilities:
- JSON formatting for production environments
- Human-readable formatting for development
- Correlation ID tracking across requests
- PII and secret filtering
- Async logging for performance
- Database query logging
- Security audit logging
"""

from .config import setup_logging, get_logger
from .context import (
    LogContext,
    get_correlation_id,
    set_correlation_id,
    get_user_id,
    set_user_id,
    clear_context,
)
from .decorators import log_execution, log_async_execution, log_error
from .audit import AuditLogger, AuditEventType, AuditSeverity
from .filters import sanitize_log_data

__all__ = [
    "setup_logging",
    "get_logger",
    "LogContext",
    "get_correlation_id",
    "set_correlation_id",
    "get_user_id",
    "set_user_id",
    "clear_context",
    "log_execution",
    "log_async_execution",
    "log_error",
    "AuditLogger",
    "AuditEventType",
    "AuditSeverity",
    "sanitize_log_data",
]
