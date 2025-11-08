"""
Code Security API Dependencies

Dependency injection functions for the code security API endpoints.
"""

from uuid import uuid4
from fastapi import Request

from app.modules.code_security.simple_executor import SimpleCodeExecutor
from app.modules.common.logging import set_correlation_id


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


# TODO: Replace with real authentication
def get_current_user_id() -> str:
    """
    Temporary: Return a mock user ID until authentication is implemented.

    Returns:
        Mock user ID

    Note:
        This should be replaced with actual JWT/OAuth authentication
        that extracts the user ID from the authentication token.

    TODO for production:
        - Implement JWT token validation
        - Extract user_id from token claims
        - Handle token expiration and refresh
        - Implement role-based access control (RBAC)
    """
    return "user123"


def get_code_executor() -> SimpleCodeExecutor:
    """
    Factory function to create a SimpleCodeExecutor instance.

    Returns a pre-configured code executor with default settings.
    This can be customized per-request if needed.

    Returns:
        SimpleCodeExecutor: Configured code executor instance

    Note:
        Default settings:
        - Timeout: 30 seconds
        - Memory limit: 512 MB

        These can be overridden by request parameters.
    """
    # Return a new executor instance with default settings
    # The actual timeout and memory limits will be set per-request
    return SimpleCodeExecutor(timeout=30, max_memory_mb=512)
