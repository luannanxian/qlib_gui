"""
Pytest configuration for Service layer tests.

Provides fixtures for:
- Service instances (with repository dependencies)
- Common test data (sample indicators, factors, library items)
- Database session (reused from repository conftest)
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Import fixtures from repository conftest
from tests.modules.indicator.repositories.conftest import *

from app.database.models.indicator import (
    IndicatorComponent, CustomFactor, UserFactorLibrary,
    IndicatorCategory, IndicatorSource, FactorStatus
)
from app.database.repositories.indicator_repository import IndicatorRepository
from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository
from app.modules.indicator.services.indicator_service import IndicatorService
from app.modules.indicator.services.custom_factor_service import CustomFactorService
from app.modules.indicator.services.user_library_service import UserLibraryService


# ===================== Repository Fixtures =====================

@pytest_asyncio.fixture
async def indicator_repo(db_session: AsyncSession) -> IndicatorRepository:
    """
    Create IndicatorRepository instance.

    Args:
        db_session: Database session from repository conftest

    Returns:
        IndicatorRepository instance
    """
    return IndicatorRepository(db_session)


@pytest_asyncio.fixture
async def custom_factor_repo(db_session: AsyncSession) -> CustomFactorRepository:
    """
    Create CustomFactorRepository instance.

    Args:
        db_session: Database session from repository conftest

    Returns:
        CustomFactorRepository instance
    """
    return CustomFactorRepository(db_session)


@pytest_asyncio.fixture
async def user_library_repo(db_session: AsyncSession) -> UserFactorLibraryRepository:
    """
    Create UserFactorLibraryRepository instance.

    Args:
        db_session: Database session from repository conftest

    Returns:
        UserFactorLibraryRepository instance
    """
    return UserFactorLibraryRepository(db_session)


# ===================== Service Fixtures =====================

@pytest_asyncio.fixture
async def indicator_service(indicator_repo: IndicatorRepository) -> IndicatorService:
    """
    Create IndicatorService instance.

    Args:
        indicator_repo: IndicatorRepository instance

    Returns:
        IndicatorService instance
    """
    return IndicatorService(indicator_repo)


@pytest_asyncio.fixture
async def custom_factor_service(custom_factor_repo: CustomFactorRepository) -> CustomFactorService:
    """
    Create CustomFactorService instance.

    Args:
        custom_factor_repo: CustomFactorRepository instance

    Returns:
        CustomFactorService instance
    """
    return CustomFactorService(custom_factor_repo)


@pytest_asyncio.fixture
async def user_library_service(user_library_repo: UserFactorLibraryRepository) -> UserLibraryService:
    """
    Create UserLibraryService instance.

    Args:
        user_library_repo: UserFactorLibraryRepository instance

    Returns:
        UserLibraryService instance
    """
    return UserLibraryService(user_library_repo)


# ===================== Test Data Fixtures =====================

@pytest_asyncio.fixture
async def sample_indicator(db_session: AsyncSession) -> IndicatorComponent:
    """
    Create sample indicator for testing.

    Returns:
        IndicatorComponent instance
    """
    indicator = IndicatorComponent(
        code="SMA",
        name_zh="简单移动平均",
        name_en="Simple Moving Average",
        category=IndicatorCategory.TREND.value,
        source=IndicatorSource.TALIB.value,
        description_zh="简单移动平均线，用于识别趋势方向",
        description_en="Simple Moving Average for trend identification",
        formula="SMA(close, N)",
        parameters={"N": {"type": "integer", "min": 1, "max": 100, "default": 20}},
        default_params={"N": 20},
        is_enabled=True,
        usage_count=100
    )
    db_session.add(indicator)
    await db_session.commit()
    await db_session.refresh(indicator)
    return indicator


@pytest_asyncio.fixture
async def sample_indicators_batch(db_session: AsyncSession) -> list[IndicatorComponent]:
    """
    Create batch of sample indicators for pagination testing.

    Returns:
        List of IndicatorComponent instances
    """
    indicators = [
        IndicatorComponent(
            code=f"IND_{i}",
            name_zh=f"指标{i}",
            name_en=f"Indicator {i}",
            category=IndicatorCategory.TREND.value if i % 2 == 0 else IndicatorCategory.MOMENTUM.value,
            source=IndicatorSource.QLIB.value,
            is_enabled=True,
            usage_count=i * 10
        )
        for i in range(1, 26)  # 25 indicators
    ]

    for ind in indicators:
        db_session.add(ind)
    await db_session.commit()

    for ind in indicators:
        await db_session.refresh(ind)

    return indicators


@pytest_asyncio.fixture
async def sample_custom_factor(db_session: AsyncSession, sample_indicator: IndicatorComponent) -> CustomFactor:
    """
    Create sample custom factor for testing.

    Args:
        db_session: Database session
        sample_indicator: Sample indicator to use as base

    Returns:
        CustomFactor instance
    """
    factor = CustomFactor(
        factor_name="我的动量因子",
        user_id="user123",
        formula="(close - open) / open",
        formula_language="qlib_alpha",
        description="基于开盘和收盘价的动量因子",
        status=FactorStatus.DRAFT.value,
        is_public=False,
        base_indicator_id=sample_indicator.id,
        usage_count=5
    )
    db_session.add(factor)
    await db_session.commit()
    await db_session.refresh(factor)
    return factor


@pytest_asyncio.fixture
async def sample_public_factor(db_session: AsyncSession) -> CustomFactor:
    """
    Create sample public factor for testing.

    Returns:
        CustomFactor instance
    """
    factor = CustomFactor(
        factor_name="公开动量因子",
        user_id="user456",
        formula="(close - Ref(close, 20)) / Ref(close, 20)",
        formula_language="qlib_alpha",
        description="20日动量因子",
        status=FactorStatus.PUBLISHED.value,
        is_public=True,
        usage_count=50,
        clone_count=10
    )
    db_session.add(factor)
    await db_session.commit()
    await db_session.refresh(factor)
    return factor


@pytest_asyncio.fixture
async def sample_library_item(
    db_session: AsyncSession,
    sample_custom_factor: CustomFactor
) -> UserFactorLibrary:
    """
    Create sample library item for testing.

    Args:
        db_session: Database session
        sample_custom_factor: Sample custom factor

    Returns:
        UserFactorLibrary instance
    """
    library_item = UserFactorLibrary(
        user_id="user123",
        factor_id=sample_custom_factor.id,
        is_favorite=False,
        usage_count=10
    )
    db_session.add(library_item)
    await db_session.commit()
    await db_session.refresh(library_item)
    return library_item


@pytest_asyncio.fixture
async def sample_library_items_batch(
    db_session: AsyncSession
) -> list[UserFactorLibrary]:
    """
    Create batch of library items for pagination testing.

    Returns:
        List of UserFactorLibrary instances
    """
    # First create factors
    factors = [
        CustomFactor(
            factor_name=f"因子{i}",
            user_id="user999",
            formula=f"close * {i}",
            formula_language="qlib_alpha",
            status=FactorStatus.PUBLISHED.value,
            is_public=False
        )
        for i in range(1, 16)  # 15 factors
    ]

    for factor in factors:
        db_session.add(factor)
    await db_session.commit()

    for factor in factors:
        await db_session.refresh(factor)

    # Create library items
    library_items = [
        UserFactorLibrary(
            user_id="user123",
            factor_id=factor.id,
            is_favorite=(i % 3 == 0),  # Every 3rd is favorite
            usage_count=i * 5
        )
        for i, factor in enumerate(factors, 1)
    ]

    for item in library_items:
        db_session.add(item)
    await db_session.commit()

    for item in library_items:
        await db_session.refresh(item)

    return library_items
