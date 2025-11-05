"""
Logging Configuration Module

Provides centralized loguru configuration with:
- Environment-specific settings (dev vs production)
- Multiple output formats (JSON, human-readable)
- Log rotation and retention policies
- Performance-optimized async logging
- Integration with Python's standard logging
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from functools import lru_cache

from app.config import settings
from .formatters import JsonFormatter, DevelopmentFormatter
from .filters import SensitiveDataFilter


class LogConfig:
    """Centralized logging configuration"""

    # Log levels mapping
    LOG_LEVELS = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }

    # Rotation settings
    ROTATION_SIZE = "100 MB"  # Rotate when file reaches 100MB
    ROTATION_TIME = "00:00"  # Rotate daily at midnight
    RETENTION_DAYS = 30  # Keep logs for 30 days
    COMPRESSION = "zip"  # Compress rotated logs

    # Performance settings
    ENQUEUE = True  # Async logging to avoid blocking
    BACKTRACE = True  # Include full traceback in errors
    DIAGNOSE = True  # Include variable values in tracebacks (disable in production)

    # Module-specific log levels
    MODULE_LOG_LEVELS: Dict[str, str] = {
        "sqlalchemy.engine": "WARNING",  # Only log SQL warnings/errors
        "sqlalchemy.pool": "WARNING",
        "uvicorn.access": "INFO",
        "uvicorn.error": "ERROR",
        "celery": "INFO",
        "fastapi": "INFO",
    }


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    environment: Optional[str] = None,
) -> None:
    """
    Setup comprehensive logging configuration using loguru.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        environment: Environment name (development, staging, production)

    Example:
        >>> setup_logging(log_level="INFO", environment="production")
    """
    # Remove default handler
    logger.remove()

    # Determine environment
    env = environment or settings.APP_ENV
    is_production = env == "production"
    is_development = env == "development"

    # Determine log level
    level = log_level or settings.LOG_LEVEL

    # Determine log directory
    logs_path = Path(log_dir or settings.LOG_DIR)
    logs_path.mkdir(parents=True, exist_ok=True)

    # Configure formatters
    json_formatter = JsonFormatter()
    dev_formatter = DevelopmentFormatter()
    sensitive_filter = SensitiveDataFilter()

    # Console handler - human readable in dev, JSON in production
    if is_development:
        logger.add(
            sys.stdout,
            format=dev_formatter.format,
            level=level,
            colorize=True,
            enqueue=LogConfig.ENQUEUE,
            backtrace=LogConfig.BACKTRACE,
            diagnose=LogConfig.DIAGNOSE,
            filter=sensitive_filter.filter_record,
        )
    else:
        logger.add(
            sys.stdout,
            serialize=True,
            level=level,
            enqueue=LogConfig.ENQUEUE,
            backtrace=LogConfig.BACKTRACE,
            diagnose=False,  # Disable in production for security
            filter=sensitive_filter.filter_record,
        )

    # Application log file - JSON format for all environments
    logger.add(
        logs_path / "app_{time:YYYY-MM-DD}.log",
        serialize=True,
        level=level,
        rotation=LogConfig.ROTATION_TIME,
        retention=f"{LogConfig.RETENTION_DAYS} days",
        compression=LogConfig.COMPRESSION,
        enqueue=LogConfig.ENQUEUE,
        backtrace=LogConfig.BACKTRACE,
        diagnose=not is_production,
        filter=sensitive_filter.filter_record,
    )

    # Error log file - Only errors and critical
    logger.add(
        logs_path / "error_{time:YYYY-MM-DD}.log",
        serialize=True,
        level="ERROR",
        rotation=LogConfig.ROTATION_TIME,
        retention=f"{LogConfig.RETENTION_DAYS * 2} days",  # Keep errors longer
        compression=LogConfig.COMPRESSION,
        enqueue=LogConfig.ENQUEUE,
        backtrace=LogConfig.BACKTRACE,
        diagnose=not is_production,
        filter=sensitive_filter.filter_record,
    )

    # Performance/Audit log file - For security and performance tracking
    logger.add(
        logs_path / "audit_{time:YYYY-MM-DD}.log",
        serialize=True,
        level="INFO",
        rotation=LogConfig.ROTATION_TIME,
        retention=f"{LogConfig.RETENTION_DAYS * 3} days",  # Keep audit logs longer
        compression=LogConfig.COMPRESSION,
        enqueue=LogConfig.ENQUEUE,
        filter=lambda record: record["extra"].get("audit", False),
    )

    # Database query log file - SQL queries and performance
    logger.add(
        logs_path / "database_{time:YYYY-MM-DD}.log",
        serialize=True,
        level="DEBUG" if is_development else "INFO",
        rotation=LogConfig.ROTATION_SIZE,
        retention=f"{LogConfig.RETENTION_DAYS} days",
        compression=LogConfig.COMPRESSION,
        enqueue=LogConfig.ENQUEUE,
        filter=lambda record: record["extra"].get("database", False),
    )

    # Integrate with Python's standard logging
    _setup_standard_logging_integration()

    # Configure module-specific log levels
    _configure_module_log_levels()

    logger.info(
        "Logging configured",
        extra={
            "environment": env,
            "log_level": level,
            "log_dir": str(logs_path),
            "is_production": is_production,
        },
    )


def _setup_standard_logging_integration() -> None:
    """
    Integrate Python's standard logging with loguru.

    This allows third-party libraries using standard logging
    to output through loguru handlers.
    """

    class InterceptHandler(logging.Handler):
        """
        Intercept standard logging messages and redirect to loguru.
        """

        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # Remove all existing handlers from root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LogConfig.LOG_LEVELS.get(settings.LOG_LEVEL, logging.INFO))

    # Intercept specific loggers
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy",
        "celery",
    ]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]


def _configure_module_log_levels() -> None:
    """Configure log levels for specific modules"""
    for module_name, level in LogConfig.MODULE_LOG_LEVELS.items():
        logging.getLogger(module_name).setLevel(level)


@lru_cache()
def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with optional name binding.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        Logger instance bound to the given name

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("Application started")
    """
    if name:
        return logger.bind(module=name)
    return logger


def configure_log_level(module: str, level: str) -> None:
    """
    Dynamically configure log level for a specific module.

    Args:
        module: Module name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> configure_log_level("sqlalchemy.engine", "DEBUG")
    """
    LogConfig.MODULE_LOG_LEVELS[module] = level
    logging.getLogger(module).setLevel(level)
    logger.info(f"Updated log level for {module} to {level}")
