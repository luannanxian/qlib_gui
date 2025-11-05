"""
Logging Decorators Module

Provides decorators for automatic function/method logging:
- Execution time tracking
- Error logging with stack traces
- Parameter and return value logging
- Async support
"""

import time
import functools
import inspect
from typing import Callable, Any, Optional
from loguru import logger

from .context import get_current_context
from .filters import sanitize_log_data


def log_execution(
    *,
    level: str = "INFO",
    log_args: bool = True,
    log_result: bool = False,
    log_time: bool = True,
    sanitize: bool = True,
):
    """
    Decorator to log function execution.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_args: Whether to log function arguments
        log_result: Whether to log return value
        log_time: Whether to log execution time
        sanitize: Whether to sanitize sensitive data

    Example:
        >>> @log_execution(level="DEBUG", log_args=True, log_result=True)
        >>> def process_data(data: dict):
        >>>     return {"processed": True}
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function info
            func_name = func.__name__
            module_name = func.__module__

            # Get context
            context = get_current_context().to_dict()

            # Prepare log data
            log_data = {
                "function": func_name,
                "module": module_name,
                **context,
            }

            # Log arguments if enabled
            if log_args:
                # Get argument names
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                args_dict = dict(bound_args.arguments)

                # Sanitize if enabled
                if sanitize:
                    args_dict = sanitize_log_data(args_dict)

                log_data["arguments"] = args_dict

            # Log function entry
            logger.log(
                level,
                f"Executing {func_name}",
                extra=log_data,
            )

            # Execute function with timing
            start_time = time.perf_counter()
            result = None
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Calculate execution time
                execution_time_ms = (time.perf_counter() - start_time) * 1000

                # Prepare completion log
                completion_data = {
                    "function": func_name,
                    "module": module_name,
                    **context,
                }

                if log_time:
                    completion_data["execution_time_ms"] = round(execution_time_ms, 2)

                # Log result if enabled and no error
                if log_result and result is not None and error is None:
                    result_to_log = result
                    if sanitize:
                        result_to_log = sanitize_log_data(result_to_log)
                    completion_data["result"] = result_to_log

                # Log completion or error
                if error:
                    logger.error(
                        f"Failed {func_name}: {type(error).__name__}",
                        extra={
                            **completion_data,
                            "error_type": type(error).__name__,
                            "error_message": str(error),
                        },
                    )
                else:
                    logger.log(
                        level,
                        f"Completed {func_name} in {execution_time_ms:.2f}ms",
                        extra=completion_data,
                    )

        return wrapper

    return decorator


def log_async_execution(
    *,
    level: str = "INFO",
    log_args: bool = True,
    log_result: bool = False,
    log_time: bool = True,
    sanitize: bool = True,
):
    """
    Decorator to log async function execution.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_args: Whether to log function arguments
        log_result: Whether to log return value
        log_time: Whether to log execution time
        sanitize: Whether to sanitize sensitive data

    Example:
        >>> @log_async_execution(level="DEBUG", log_args=True)
        >>> async def fetch_data(url: str):
        >>>     return await client.get(url)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function info
            func_name = func.__name__
            module_name = func.__module__

            # Get context
            context = get_current_context().to_dict()

            # Prepare log data
            log_data = {
                "function": func_name,
                "module": module_name,
                "async": True,
                **context,
            }

            # Log arguments if enabled
            if log_args:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                args_dict = dict(bound_args.arguments)

                if sanitize:
                    args_dict = sanitize_log_data(args_dict)

                log_data["arguments"] = args_dict

            # Log function entry
            logger.log(
                level,
                f"Executing async {func_name}",
                extra=log_data,
            )

            # Execute function with timing
            start_time = time.perf_counter()
            result = None
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Calculate execution time
                execution_time_ms = (time.perf_counter() - start_time) * 1000

                # Prepare completion log
                completion_data = {
                    "function": func_name,
                    "module": module_name,
                    "async": True,
                    **context,
                }

                if log_time:
                    completion_data["execution_time_ms"] = round(execution_time_ms, 2)

                # Log result if enabled
                if log_result and result is not None and error is None:
                    result_to_log = result
                    if sanitize:
                        result_to_log = sanitize_log_data(result_to_log)
                    completion_data["result"] = result_to_log

                # Log completion or error
                if error:
                    logger.error(
                        f"Failed async {func_name}: {type(error).__name__}",
                        extra={
                            **completion_data,
                            "error_type": type(error).__name__,
                            "error_message": str(error),
                        },
                    )
                else:
                    logger.log(
                        level,
                        f"Completed async {func_name} in {execution_time_ms:.2f}ms",
                        extra=completion_data,
                    )

        return wrapper

    return decorator


def log_error(
    *,
    level: str = "ERROR",
    reraise: bool = True,
    default_return: Any = None,
):
    """
    Decorator to log errors with stack traces.

    Args:
        level: Log level for errors
        reraise: Whether to reraise the exception
        default_return: Default value to return if error caught

    Example:
        >>> @log_error(reraise=False, default_return={})
        >>> def risky_operation():
        >>>     # Will log error and return {} instead of raising
        >>>     raise ValueError("Something went wrong")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get context
                context = get_current_context().to_dict()

                # Log exception with full traceback
                logger.opt(exception=True).log(
                    level,
                    f"Error in {func.__name__}: {type(e).__name__}",
                    extra={
                        "function": func.__name__,
                        "module": func.__module__,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        **context,
                    },
                )

                if reraise:
                    raise

                return default_return

        # Check if function is async
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    context = get_current_context().to_dict()

                    logger.opt(exception=True).log(
                        level,
                        f"Error in async {func.__name__}: {type(e).__name__}",
                        extra={
                            "function": func.__name__,
                            "module": func.__module__,
                            "async": True,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            **context,
                        },
                    )

                    if reraise:
                        raise

                    return default_return

            return async_wrapper

        return wrapper

    return decorator


def log_slow_execution(threshold_ms: float = 1000.0, level: str = "WARNING"):
    """
    Decorator to log slow function execution.

    Only logs if execution time exceeds threshold.

    Args:
        threshold_ms: Time threshold in milliseconds
        level: Log level for slow executions

    Example:
        >>> @log_slow_execution(threshold_ms=500)
        >>> def potentially_slow_operation():
        >>>     # Will log if takes > 500ms
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                return func(*args, **kwargs)
            finally:
                execution_time_ms = (time.perf_counter() - start_time) * 1000

                if execution_time_ms > threshold_ms:
                    context = get_current_context().to_dict()

                    logger.log(
                        level,
                        f"Slow execution detected in {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "module": func.__module__,
                            "execution_time_ms": round(execution_time_ms, 2),
                            "threshold_ms": threshold_ms,
                            "slow_operation": True,
                            **context,
                        },
                    )

        # Check if function is async
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    return await func(*args, **kwargs)
                finally:
                    execution_time_ms = (time.perf_counter() - start_time) * 1000

                    if execution_time_ms > threshold_ms:
                        context = get_current_context().to_dict()

                        logger.log(
                            level,
                            f"Slow async execution detected in {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "module": func.__module__,
                                "async": True,
                                "execution_time_ms": round(execution_time_ms, 2),
                                "threshold_ms": threshold_ms,
                                "slow_operation": True,
                                **context,
                            },
                        )

            return async_wrapper

        return wrapper

    return decorator


class LogExecutionContext:
    """
    Context manager for logging code block execution.

    Example:
        >>> with LogExecutionContext("data_processing"):
        >>>     # Code here will be logged
        >>>     process_data()
    """

    def __init__(
        self,
        operation_name: str,
        level: str = "INFO",
        log_time: bool = True,
        **extra_context,
    ):
        """
        Initialize execution context.

        Args:
            operation_name: Name of the operation
            level: Log level
            log_time: Whether to log execution time
            **extra_context: Additional context to log
        """
        self.operation_name = operation_name
        self.level = level
        self.log_time = log_time
        self.extra_context = extra_context
        self.start_time = None

    def __enter__(self):
        """Enter context."""
        self.start_time = time.perf_counter()

        context = get_current_context().to_dict()

        logger.log(
            self.level,
            f"Starting {self.operation_name}",
            extra={
                "operation": self.operation_name,
                **context,
                **self.extra_context,
            },
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        execution_time_ms = (time.perf_counter() - self.start_time) * 1000

        context = get_current_context().to_dict()
        log_data = {
            "operation": self.operation_name,
            **context,
            **self.extra_context,
        }

        if self.log_time:
            log_data["execution_time_ms"] = round(execution_time_ms, 2)

        if exc_type is not None:
            # Error occurred
            logger.error(
                f"Failed {self.operation_name}: {exc_type.__name__}",
                extra={
                    **log_data,
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                },
            )
        else:
            # Success
            logger.log(
                self.level,
                f"Completed {self.operation_name} in {execution_time_ms:.2f}ms",
                extra=log_data,
            )

        # Don't suppress exceptions
        return False
