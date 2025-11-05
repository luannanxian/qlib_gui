"""
Logging Middleware for FastAPI

Provides comprehensive request/response logging with:
- Request ID and correlation ID tracking
- Request/response timing
- Request body logging (with size limits)
- Response status and size logging
- Error logging with stack traces
- User context tracking
"""

import time
import json
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from .context import (
    set_correlation_id,
    set_request_id,
    set_user_id,
    clear_context,
    get_correlation_id,
)
from .filters import sanitize_log_data


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.

    Logs:
    - Incoming requests with headers, method, path, query params
    - Outgoing responses with status code, size, timing
    - Errors with stack traces
    - User information if authenticated
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        log_request_body: bool = True,
        log_response_body: bool = False,
        max_body_size: int = 10000,  # 10KB default
        skip_paths: Optional[list] = None,
        skip_healthcheck: bool = True,
    ):
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies (caution: performance)
            max_body_size: Maximum body size to log in bytes
            skip_paths: List of paths to skip logging
            skip_healthcheck: Skip logging health check endpoints
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.skip_paths = skip_paths or []
        self.skip_healthcheck = skip_healthcheck

        # Add default skip paths
        if skip_healthcheck:
            self.skip_paths.extend(["/health", "/healthz", "/ready", "/live"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from the application
        """
        # Check if we should skip this path
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Setup context
        correlation_id = self._extract_correlation_id(request)
        request_id = set_request_id()
        set_correlation_id(correlation_id)

        # Extract user ID if available (from JWT or session)
        user_id = self._extract_user_id(request)
        if user_id:
            set_user_id(user_id)

        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id

        # Log incoming request
        await self._log_request(request, correlation_id, request_id, user_id)

        # Process request
        response = None
        error = None

        try:
            response = await call_next(request)
        except Exception as exc:
            error = exc
            # Log error
            logger.exception(
                "Request processing failed",
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                },
            )
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log outgoing response
            if response:
                await self._log_response(
                    request, response, duration_ms, correlation_id, request_id, user_id
                )

            # Clear context
            clear_context()

        return response

    def _should_skip(self, path: str) -> bool:
        """
        Check if logging should be skipped for this path.

        Args:
            path: Request path

        Returns:
            True if logging should be skipped
        """
        return any(path.startswith(skip_path) for skip_path in self.skip_paths)

    def _extract_correlation_id(self, request: Request) -> str:
        """
        Extract or generate correlation ID from request.

        Checks headers in order:
        1. X-Correlation-ID
        2. X-Request-ID
        3. X-Trace-ID
        4. Generate new ID

        Args:
            request: FastAPI request

        Returns:
            Correlation ID
        """
        headers_to_check = [
            "x-correlation-id",
            "x-request-id",
            "x-trace-id",
        ]

        for header in headers_to_check:
            value = request.headers.get(header)
            if value:
                return value

        # Generate new correlation ID
        return set_correlation_id()

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from request.

        This is a placeholder - implement based on your auth system.

        Args:
            request: FastAPI request

        Returns:
            User ID if authenticated, None otherwise
        """
        # Try to get from request state (if set by auth middleware)
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            return str(request.state.user.id)

        # Try to get from headers (for service-to-service calls)
        user_id_header = request.headers.get("x-user-id")
        if user_id_header:
            return user_id_header

        return None

    async def _log_request(
        self,
        request: Request,
        correlation_id: str,
        request_id: str,
        user_id: Optional[str],
    ) -> None:
        """
        Log incoming request.

        Args:
            request: FastAPI request
            correlation_id: Correlation ID
            request_id: Request ID
            user_id: User ID if authenticated
        """
        # Build request info
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Add request body if enabled
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await self._get_request_body(request)
                if body:
                    request_info["body"] = body
            except Exception as e:
                logger.warning(
                    f"Failed to log request body: {e}",
                    extra={"correlation_id": correlation_id},
                )

        # Sanitize sensitive data
        request_info = sanitize_log_data(request_info)

        logger.info(
            f"Incoming {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "request_id": request_id,
                "user_id": user_id,
                "request": request_info,
                "event_type": "http_request",
            },
        )

    async def _log_response(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        correlation_id: str,
        request_id: str,
        user_id: Optional[str],
    ) -> None:
        """
        Log outgoing response.

        Args:
            request: FastAPI request
            response: FastAPI response
            duration_ms: Request duration in milliseconds
            correlation_id: Correlation ID
            request_id: Request ID
            user_id: User ID if authenticated
        """
        # Get response info
        response_info = {
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Add content length if available
        if hasattr(response, "headers") and "content-length" in response.headers:
            response_info["content_length"] = int(response.headers["content-length"])

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        # Add slow request flag
        if duration_ms > 1000:  # > 1 second
            response_info["slow_request"] = True

        # Log response
        log_method = getattr(logger, log_level)
        log_method(
            f"Completed {request.method} {request.url.path} {response.status_code} in {duration_ms:.2f}ms",
            extra={
                "correlation_id": correlation_id,
                "request_id": request_id,
                "user_id": user_id,
                "response": response_info,
                "event_type": "http_response",
            },
        )

    async def _get_request_body(self, request: Request) -> Optional[dict]:
        """
        Get request body as dictionary.

        Args:
            request: FastAPI request

        Returns:
            Request body as dict or None if not JSON
        """
        try:
            # Get raw body
            body_bytes = await request.body()

            # Check size
            if len(body_bytes) > self.max_body_size:
                return {
                    "_truncated": True,
                    "_size": len(body_bytes),
                    "_message": f"Body too large ({len(body_bytes)} bytes)",
                }

            # Try to parse as JSON
            if body_bytes:
                body_str = body_bytes.decode("utf-8")
                try:
                    return json.loads(body_str)
                except json.JSONDecodeError:
                    # Not JSON, return truncated string
                    return {
                        "_raw": body_str[:1000] if len(body_str) > 1000 else body_str,
                        "_truncated": len(body_str) > 1000,
                    }

        except Exception:
            return None

        return None


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware to only inject correlation ID into responses.

    Use this if you want correlation ID tracking without full logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add correlation ID to response headers.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-request-id")
            or set_correlation_id()
        )

        # Set in context
        set_correlation_id(correlation_id)

        # Store in request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Clear context
        clear_context()

        return response


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware focused on performance metrics logging.

    Logs detailed performance metrics for analysis and optimization.
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_threshold_ms: float = 1000.0,
        very_slow_threshold_ms: float = 5000.0,
    ):
        """
        Initialize performance logging middleware.

        Args:
            app: FastAPI application
            slow_threshold_ms: Threshold for slow requests (ms)
            very_slow_threshold_ms: Threshold for very slow requests (ms)
        """
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
        self.very_slow_threshold_ms = very_slow_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log performance metrics.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from the application
        """
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log if slow
        if duration_ms > self.slow_threshold_ms:
            log_level = (
                "error" if duration_ms > self.very_slow_threshold_ms else "warning"
            )

            log_method = getattr(logger, log_level)
            log_method(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "performance": {
                        "duration_ms": round(duration_ms, 2),
                        "slow_threshold_ms": self.slow_threshold_ms,
                        "is_very_slow": duration_ms > self.very_slow_threshold_ms,
                    },
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                },
            )

        return response
