"""Shared API Dependencies

Common dependencies used across indicator API modules to eliminate code duplication.
"""

from uuid import uuid4
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repositories.indicator_repository import IndicatorRepository
from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository
from app.modules.indicator.services.indicator_service import IndicatorService
from app.modules.indicator.services.custom_factor_service import CustomFactorService
from app.modules.indicator.services.user_library_service import UserLibraryService
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


def get_indicator_service(db: AsyncSession = Depends(get_db)) -> IndicatorService:
    """
    Dependency to get IndicatorService instance.

    Args:
        db: Database session

    Returns:
        IndicatorService instance
    """
    indicator_repo = IndicatorRepository(db)
    return IndicatorService(indicator_repo)


def get_custom_factor_service(db: AsyncSession = Depends(get_db)) -> CustomFactorService:
    """
    Dependency to get CustomFactorService instance.

    Args:
        db: Database session

    Returns:
        CustomFactorService instance
    """
    custom_factor_repo = CustomFactorRepository(db)
    return CustomFactorService(custom_factor_repo)


def get_user_library_service(db: AsyncSession = Depends(get_db)) -> UserLibraryService:
    """
    Dependency to get UserLibraryService instance.

    Args:
        db: Database session

    Returns:
        UserLibraryService instance
    """
    user_library_repo = UserFactorLibraryRepository(db)
    return UserLibraryService(user_library_repo)
