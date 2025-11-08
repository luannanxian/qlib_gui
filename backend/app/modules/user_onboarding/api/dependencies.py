"""Shared API Dependencies

Common dependencies used across user onboarding API modules to eliminate code duplication.
"""

from uuid import uuid4
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repositories.user_preferences import UserPreferencesRepository
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
    """
    return "user123"


def get_user_prefs_repo(db: AsyncSession = Depends(get_db)) -> UserPreferencesRepository:
    """
    Dependency to get UserPreferencesRepository instance.

    Args:
        db: Database session

    Returns:
        UserPreferencesRepository instance
    """
    return UserPreferencesRepository(db)
