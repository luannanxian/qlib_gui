"""
Chart Configuration Repository

This module provides repository pattern implementation for ChartConfig model
with custom query methods specific to chart operations.
"""

from typing import List, Optional, Dict, Any

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chart import ChartConfig, ChartType
from app.database.repositories.base import BaseRepository


class ChartRepository(BaseRepository[ChartConfig]):
    """
    Repository for ChartConfig model with specialized query methods.

    Extends BaseRepository with chart-specific operations such as:
    - Get charts by dataset
    - Get charts by type
    - Count charts per dataset
    - Search charts by name
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize chart repository.

        Args:
            session: Async database session
        """
        super().__init__(ChartConfig, session)

    async def get_by_dataset(
        self,
        dataset_id: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ChartConfig]:
        """
        Get all charts for a specific dataset.

        Args:
            dataset_id: Dataset ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of ChartConfig instances

        Example:
            charts = await repo.get_by_dataset("dataset-uuid-123")
        """
        stmt = select(ChartConfig).where(ChartConfig.dataset_id == dataset_id)

        if not include_deleted:
            stmt = stmt.where(ChartConfig.is_deleted == False)

        stmt = stmt.order_by(ChartConfig.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        chart_type: ChartType | str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ChartConfig]:
        """
        Get charts by chart type.

        Args:
            chart_type: Chart type (kline, line, bar, scatter, heatmap)
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of ChartConfig instances

        Example:
            kline_charts = await repo.get_by_type("kline")
        """
        # Convert enum to string if needed
        type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type

        stmt = select(ChartConfig).where(ChartConfig.chart_type == type_str)

        if not include_deleted:
            stmt = stmt.where(ChartConfig.is_deleted == False)

        stmt = stmt.order_by(ChartConfig.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_dataset_and_type(
        self,
        dataset_id: str,
        chart_type: ChartType | str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ChartConfig]:
        """
        Get charts filtered by both dataset and type.

        Args:
            dataset_id: Dataset ID
            chart_type: Chart type
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of ChartConfig instances

        Example:
            charts = await repo.get_by_dataset_and_type(
                "dataset-uuid-123",
                "kline"
            )
        """
        # Convert enum to string if needed
        type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type

        stmt = select(ChartConfig).where(
            ChartConfig.dataset_id == dataset_id,
            ChartConfig.chart_type == type_str
        )

        if not include_deleted:
            stmt = stmt.where(ChartConfig.is_deleted == False)

        stmt = stmt.order_by(ChartConfig.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        dataset_id: Optional[str] = None,
        chart_type: Optional[ChartType | str] = None,
        search_term: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Count charts with optional filtering.

        This method overrides BaseRepository.count() to properly handle
        None values in filters and support search_term filtering.

        Args:
            dataset_id: Optional dataset ID filter
            chart_type: Optional chart type filter
            search_term: Optional name search term (case-insensitive)
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of matching charts

        Example:
            # Count all charts
            total = await repo.count()

            # Count charts for a specific dataset
            dataset_total = await repo.count(dataset_id="dataset-uuid-123")

            # Count charts by type
            kline_total = await repo.count(chart_type="kline")

            # Count charts with search term
            search_total = await repo.count(search_term="Bitcoin")
        """
        # For search_term, we need custom query logic
        if search_term:
            stmt = select(func.count()).select_from(ChartConfig)

            # Apply filters
            if dataset_id is not None:
                stmt = stmt.where(ChartConfig.dataset_id == dataset_id)

            if chart_type is not None:
                type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type
                stmt = stmt.where(ChartConfig.chart_type == type_str)

            # Apply search term
            stmt = stmt.where(ChartConfig.name.ilike(f"%{search_term}%"))

            if not include_deleted:
                stmt = stmt.where(ChartConfig.is_deleted == False)

            result = await self.session.execute(stmt)
            return result.scalar_one()

        # No search term, use BaseRepository.count()
        filters = {}

        if dataset_id is not None:
            filters["dataset_id"] = dataset_id

        if chart_type is not None:
            # Convert enum to string if needed
            type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type
            filters["chart_type"] = type_str

        # Call parent count with filtered parameters
        return await super().count(include_deleted=include_deleted, **filters)

    async def count_by_dataset(
        self,
        dataset_id: str,
        include_deleted: bool = False
    ) -> int:
        """
        Count charts for a specific dataset.

        Args:
            dataset_id: Dataset ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of charts for the dataset

        Example:
            count = await repo.count_by_dataset("dataset-uuid-123")
        """
        return await self.count(
            include_deleted=include_deleted,
            dataset_id=dataset_id
        )

    async def count_by_type(
        self,
        chart_type: ChartType | str,
        include_deleted: bool = False
    ) -> int:
        """
        Count charts by type.

        Args:
            chart_type: Chart type
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of charts of the given type

        Example:
            count = await repo.count_by_type("kline")
        """
        type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type
        return await self.count(
            include_deleted=include_deleted,
            chart_type=type_str
        )

    async def search_by_name(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ChartConfig]:
        """
        Search charts by name (case-insensitive partial match).

        Args:
            search_term: Search term to match against chart names
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of ChartConfig instances matching the search term

        Example:
            results = await repo.search_by_name("price", limit=10)
        """
        stmt = select(ChartConfig).where(
            ChartConfig.name.ilike(f"%{search_term}%")
        )

        if not include_deleted:
            stmt = stmt.where(ChartConfig.is_deleted == False)

        stmt = stmt.order_by(ChartConfig.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_filters(
        self,
        dataset_id: Optional[str] = None,
        chart_type: Optional[ChartType | str] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ChartConfig]:
        """
        Get charts with multiple filters combined.

        Args:
            dataset_id: Optional dataset ID filter
            chart_type: Optional chart type filter
            search_term: Optional name search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of ChartConfig instances matching all filters

        Example:
            charts = await repo.get_with_filters(
                dataset_id="dataset-uuid-123",
                chart_type="kline",
                search_term="price"
            )
        """
        stmt = select(ChartConfig)

        # Apply filters
        if dataset_id:
            stmt = stmt.where(ChartConfig.dataset_id == dataset_id)

        if chart_type:
            type_str = chart_type.value if isinstance(chart_type, ChartType) else chart_type
            stmt = stmt.where(ChartConfig.chart_type == type_str)

        if search_term:
            stmt = stmt.where(ChartConfig.name.ilike(f"%{search_term}%"))

        if not include_deleted:
            stmt = stmt.where(ChartConfig.is_deleted == False)

        stmt = stmt.order_by(ChartConfig.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get chart statistics (total, counts by type).

        Returns:
            Dictionary with statistics

        Example:
            stats = await repo.get_statistics()
            # Returns: {
            #     "total": 50,
            #     "by_type": {
            #         "kline": 20,
            #         "line": 15,
            #         "bar": 10,
            #         "scatter": 3,
            #         "heatmap": 2
            #     }
            # }
        """
        # Total count
        total = await self.count()

        # Count by type
        by_type = {}
        for chart_type in ChartType:
            by_type[chart_type.value] = await self.count_by_type(chart_type)

        stats = {
            "total": total,
            "by_type": by_type,
        }

        logger.debug(f"Chart statistics: {stats}")
        return stats

    async def soft_delete(
        self,
        chart_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Soft delete a chart configuration.

        This method marks the chart as deleted without removing it from the database.
        It delegates to BaseRepository.delete() with soft=True.

        Args:
            chart_id: Chart ID to delete
            user_id: Optional user ID for audit trail

        Returns:
            True if deleted successfully, False if chart not found

        Example:
            success = await repo.soft_delete("chart-uuid-123")
            if success:
                print("Chart deleted successfully")
        """
        success = await self.delete(chart_id, soft=True, user_id=user_id)

        if success:
            logger.info(f"Soft deleted chart: id={chart_id}")
        else:
            logger.warning(f"Chart not found for deletion: id={chart_id}")

        return success

    async def duplicate_chart(
        self,
        chart_id: str,
        new_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[ChartConfig]:
        """
        Duplicate an existing chart with a new name.

        Args:
            chart_id: ID of the chart to duplicate
            new_name: Optional new name (defaults to "Copy of [original name]")
            user_id: Optional user ID for audit trail

        Returns:
            New ChartConfig instance or None if original not found

        Example:
            new_chart = await repo.duplicate_chart(
                "chart-uuid-123",
                "My New Chart"
            )
        """
        # Get original chart
        original = await self.get(chart_id)
        if original is None:
            logger.warning(f"Chart not found for duplication: id={chart_id}")
            return None

        # Create duplicate
        duplicate_data = {
            "name": new_name or f"Copy of {original.name}",
            "chart_type": original.chart_type,
            "dataset_id": original.dataset_id,
            "config": original.config,
            "description": original.description,
        }

        duplicate = await self.create(duplicate_data, user_id=user_id)
        logger.info(f"Duplicated chart {chart_id} to {duplicate.id}")
        return duplicate
