"""
Backtest Repository

This module provides data access layer for backtest operations.
Handles CRUD operations for BacktestConfig and BacktestResult models.

Features:
- Create, read, update, delete operations
- Query by strategy, status, date range
- Soft delete support
- Pagination support
- Performance metrics queries
"""

from datetime import date
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.backtest import BacktestConfig, BacktestResult, BacktestStatus


class BacktestRepository:
    """Repository for backtest configuration and result operations"""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    # ==================== BacktestConfig Operations ====================

    async def create_config(self, config_data: Dict[str, Any]) -> BacktestConfig:
        """
        Create a new backtest configuration.

        Args:
            config_data: Dictionary containing config fields

        Returns:
            Created BacktestConfig instance
        """
        config = BacktestConfig(**config_data)
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def get_config_by_id(self, config_id: str) -> Optional[BacktestConfig]:
        """
        Retrieve a backtest configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            BacktestConfig instance or None if not found
        """
        stmt = select(BacktestConfig).where(
            and_(
                BacktestConfig.id == config_id,
                BacktestConfig.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_configs_by_strategy(self, strategy_id: str) -> List[BacktestConfig]:
        """
        Retrieve all configurations for a specific strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            List of BacktestConfig instances
        """
        stmt = select(BacktestConfig).where(
            and_(
                BacktestConfig.strategy_id == strategy_id,
                BacktestConfig.is_deleted == False
            )
        ).order_by(BacktestConfig.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_configs(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[BacktestConfig]:
        """
        Retrieve backtest configurations with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of BacktestConfig instances
        """
        stmt = select(BacktestConfig).where(
            BacktestConfig.is_deleted == False
        ).order_by(
            BacktestConfig.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_configs_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[BacktestConfig]:
        """
        Retrieve configurations that overlap with the given date range.

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            List of BacktestConfig instances
        """
        stmt = select(BacktestConfig).where(
            and_(
                BacktestConfig.is_deleted == False,
                BacktestConfig.start_date <= end_date,
                BacktestConfig.end_date >= start_date
            )
        ).order_by(BacktestConfig.start_date)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_config(
        self,
        config_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[BacktestConfig]:
        """
        Update a backtest configuration.

        Args:
            config_id: Configuration ID
            update_data: Dictionary containing fields to update

        Returns:
            Updated BacktestConfig instance or None if not found
        """
        config = await self.get_config_by_id(config_id)
        if not config:
            return None

        for key, value in update_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def delete_config(self, config_id: str) -> bool:
        """
        Soft delete a backtest configuration.

        Args:
            config_id: Configuration ID

        Returns:
            True if deleted, False if not found
        """
        config = await self.get_config_by_id(config_id)
        if not config:
            return False

        config.is_deleted = True
        await self.session.commit()
        return True

    # ==================== BacktestResult Operations ====================

    async def create_result(self, result_data: Dict[str, Any]) -> BacktestResult:
        """
        Create a new backtest result.

        Args:
            result_data: Dictionary containing result fields

        Returns:
            Created BacktestResult instance
        """
        result = BacktestResult(**result_data)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_result_by_id(self, result_id: str) -> Optional[BacktestResult]:
        """
        Retrieve a backtest result by ID.

        Args:
            result_id: Result ID

        Returns:
            BacktestResult instance or None if not found
        """
        stmt = select(BacktestResult).where(
            and_(
                BacktestResult.id == result_id,
                BacktestResult.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_results_by_config(self, config_id: str) -> List[BacktestResult]:
        """
        Retrieve all results for a specific configuration.

        Args:
            config_id: Configuration ID

        Returns:
            List of BacktestResult instances
        """
        stmt = select(BacktestResult).where(
            and_(
                BacktestResult.config_id == config_id,
                BacktestResult.is_deleted == False
            )
        ).order_by(BacktestResult.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_results_by_status(self, status: str) -> List[BacktestResult]:
        """
        Retrieve all results with a specific status.

        Args:
            status: Backtest status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)

        Returns:
            List of BacktestResult instances
        """
        stmt = select(BacktestResult).where(
            and_(
                BacktestResult.status == status,
                BacktestResult.is_deleted == False
            )
        ).order_by(BacktestResult.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_result_status(
        self,
        result_id: str,
        status: str
    ) -> Optional[BacktestResult]:
        """
        Update the status of a backtest result.

        Args:
            result_id: Result ID
            status: New status value

        Returns:
            Updated BacktestResult instance or None if not found
        """
        result = await self.get_result_by_id(result_id)
        if not result:
            return None

        result.status = status
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def update_result(
        self,
        result_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[BacktestResult]:
        """
        Update a backtest result.

        Args:
            result_id: Result ID
            update_data: Dictionary containing fields to update

        Returns:
            Updated BacktestResult instance or None if not found
        """
        result = await self.get_result_by_id(result_id)
        if not result:
            return None

        for key, value in update_data.items():
            if hasattr(result, key):
                setattr(result, key, value)

        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def delete_result(self, result_id: str) -> bool:
        """
        Soft delete a backtest result.

        Args:
            result_id: Result ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.get_result_by_id(result_id)
        if not result:
            return False

        result.is_deleted = True
        await self.session.commit()
        return True

    # ==================== Query Operations ====================

    async def get_best_performing_results(
        self,
        limit: int = 10
    ) -> List[BacktestResult]:
        """
        Retrieve best performing backtest results sorted by total return.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of BacktestResult instances sorted by total_return descending
        """
        stmt = select(BacktestResult).where(
            and_(
                BacktestResult.is_deleted == False,
                BacktestResult.status == BacktestStatus.COMPLETED.value
            )
        ).order_by(
            BacktestResult.total_return.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_results_by_status(self, status: str) -> int:
        """
        Count the number of results with a specific status.

        Args:
            status: Backtest status

        Returns:
            Count of results with the given status
        """
        stmt = select(func.count(BacktestResult.id)).where(
            and_(
                BacktestResult.status == status,
                BacktestResult.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
