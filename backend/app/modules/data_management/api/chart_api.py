"""Chart API endpoints for data visualization"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from loguru import logger
import pandas as pd
from datetime import datetime

from app.database.session import get_db
from app.database.repositories.chart import ChartRepository
from app.database.repositories.dataset import DatasetRepository
from app.modules.data_management.schemas.chart import (
    ChartConfigCreate,
    ChartConfigUpdate,
    ChartConfigResponse,
    ChartConfigListResponse,
    ChartDataRequest,
    ChartDataResponse,
    ChartExportRequest,
    ChartExportResponse,
    AnnotationRequest
)
from app.modules.data_management.services.chart_service import ChartService
from app.modules.common.schemas.response import SuccessResponse, ErrorResponse
from app.modules.data_management.utils.serialization import (
    prepare_chart_data_for_serialization,
    prepare_annotation_for_storage
)

router = APIRouter(prefix="/api/charts", tags=["Charts"])


@router.post("", response_model=ChartConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_chart(
    chart_data: ChartConfigCreate,
    db: AsyncSession = Depends(get_db)
) -> ChartConfigResponse:
    """
    Create a new chart configuration.

    Args:
        chart_data: Chart configuration data
        db: Database session

    Returns:
        Created chart configuration

    Raises:
        HTTPException: If dataset not found or creation fails
    """
    try:
        # Verify dataset exists
        dataset_repo = DatasetRepository(db)
        dataset = await dataset_repo.get(chart_data.dataset_id)

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {chart_data.dataset_id}"
            )

        # Create chart configuration
        chart_repo = ChartRepository(db)
        chart = await chart_repo.create(chart_data.model_dump())

        logger.info(f"Created chart configuration: {chart.id}")

        return ChartConfigResponse.model_validate(chart)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chart: {str(e)}"
        )


@router.get("", response_model=ChartConfigListResponse)
async def list_charts(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    chart_type: Optional[str] = Query(None, description="Filter by chart type"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db)
) -> ChartConfigListResponse:
    """
    List chart configurations with optional filtering.

    Args:
        dataset_id: Optional dataset ID filter
        chart_type: Optional chart type filter
        search: Optional name search term
        skip: Records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of chart configurations
    """
    try:
        chart_repo = ChartRepository(db)

        # Get charts with filters
        charts = await chart_repo.get_with_filters(
            dataset_id=dataset_id,
            chart_type=chart_type,
            search_term=search,
            skip=skip,
            limit=limit
        )

        # Count total with same filters (including search)
        total = await chart_repo.count(
            dataset_id=dataset_id,
            chart_type=chart_type,
            search_term=search
        )

        return ChartConfigListResponse(
            total=total,
            items=[ChartConfigResponse.model_validate(chart) for chart in charts]
        )

    except Exception as e:
        logger.error(f"Error listing charts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list charts: {str(e)}"
        )


@router.get("/{chart_id}", response_model=ChartConfigResponse)
async def get_chart(
    chart_id: str,
    db: AsyncSession = Depends(get_db)
) -> ChartConfigResponse:
    """
    Get a specific chart configuration by ID.

    Args:
        chart_id: Chart ID
        db: Database session

    Returns:
        Chart configuration

    Raises:
        HTTPException: If chart not found
    """
    try:
        chart_repo = ChartRepository(db)
        chart = await chart_repo.get(chart_id)

        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        return ChartConfigResponse.model_validate(chart)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart: {str(e)}"
        )


@router.put("/{chart_id}", response_model=ChartConfigResponse)
async def update_chart(
    chart_id: str,
    chart_data: ChartConfigUpdate,
    db: AsyncSession = Depends(get_db)
) -> ChartConfigResponse:
    """
    Update a chart configuration.

    Args:
        chart_id: Chart ID
        chart_data: Updated chart data
        db: Database session

    Returns:
        Updated chart configuration

    Raises:
        HTTPException: If chart not found or update fails
    """
    try:
        chart_repo = ChartRepository(db)

        # Check if chart exists
        existing_chart = await chart_repo.get(chart_id)
        if not existing_chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        # Update chart
        update_data = chart_data.model_dump(exclude_unset=True)
        updated_chart = await chart_repo.update(chart_id, update_data)

        logger.info(f"Updated chart configuration: {chart_id}")

        return ChartConfigResponse.model_validate(updated_chart)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chart: {str(e)}"
        )


@router.delete("/{chart_id}", response_model=SuccessResponse)
async def delete_chart(
    chart_id: str,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete a chart configuration (soft delete).

    Args:
        chart_id: Chart ID
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If chart not found or deletion fails
    """
    try:
        chart_repo = ChartRepository(db)

        # Check if chart exists
        existing_chart = await chart_repo.get(chart_id)
        if not existing_chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        # Soft delete
        await chart_repo.soft_delete(chart_id)

        logger.info(f"Deleted chart configuration: {chart_id}")

        return SuccessResponse(
            message=f"Chart {chart_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chart: {str(e)}"
        )


@router.post("/{chart_id}/data", response_model=ChartDataResponse)
async def get_chart_data(
    chart_id: str,
    request: ChartDataRequest,
    db: AsyncSession = Depends(get_db)
) -> ChartDataResponse:
    """
    Get chart data with indicators.

    This endpoint generates OHLC data, applies technical indicators,
    and returns data ready for frontend chart libraries.

    Args:
        chart_id: Chart ID
        request: Chart data request parameters
        db: Database session

    Returns:
        Chart data with optional indicators

    Raises:
        HTTPException: If chart/dataset not found or data generation fails
    """
    try:
        # Get chart configuration
        chart_repo = ChartRepository(db)
        chart = await chart_repo.get(chart_id)

        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        # Get dataset
        dataset_repo = DatasetRepository(db)
        dataset = await dataset_repo.get(request.dataset_id or chart.dataset_id)

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {request.dataset_id or chart.dataset_id}"
            )

        # Load dataset file (simplified - in production would use proper file storage)
        # For now, create sample data
        import numpy as np

        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)

        sample_data = pd.DataFrame({
            "date": dates,
            "open": 100 + np.random.randn(100).cumsum(),
            "high": 102 + np.random.randn(100).cumsum(),
            "low": 98 + np.random.randn(100).cumsum(),
            "close": 100 + np.random.randn(100).cumsum(),
            "volume": np.random.randint(500000, 1500000, 100)
        })

        # Apply date filtering if requested
        chart_service = ChartService()

        if request.start_date or request.end_date:
            sample_data = chart_service.filter_by_date_range(
                sample_data,
                start_date=request.start_date,
                end_date=request.end_date
            )

        # Generate OHLC data
        ohlc_data = chart_service.generate_ohlc_data(
            sample_data,
            chart_format=request.chart_format
        )

        # Apply indicators if requested
        indicator_results = None
        if request.indicators:
            # Build indicator params
            params = {}
            if request.indicator_params:
                if request.indicator_params.macd_params and "MACD" in request.indicators:
                    params["MACD"] = request.indicator_params.macd_params.model_dump()
                if request.indicator_params.rsi_params and "RSI" in request.indicators:
                    params["RSI"] = request.indicator_params.rsi_params.model_dump()
                if request.indicator_params.kdj_params and "KDJ" in request.indicators:
                    params["KDJ"] = request.indicator_params.kdj_params.model_dump()
                if request.indicator_params.ma_params and "MA" in request.indicators:
                    params["MA"] = request.indicator_params.ma_params.model_dump()

            result_with_indicators = chart_service.apply_indicators(
                sample_data,
                indicators=request.indicators,
                params=params
            )
            indicator_results = result_with_indicators["indicators"]

        # Convert numpy types to native Python types for JSON serialization
        ohlc_data = prepare_chart_data_for_serialization(ohlc_data)
        if indicator_results:
            indicator_results = prepare_chart_data_for_serialization(indicator_results)

        return ChartDataResponse(
            dataset_id=dataset.id,
            data=ohlc_data,
            indicators=indicator_results,
            metadata={
                "chart_id": chart_id,
                "chart_type": chart.chart_type,
                "total_records": len(sample_data)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart data for {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chart data: {str(e)}"
        )


@router.post("/{chart_id}/export", response_model=ChartExportResponse)
async def export_chart_data(
    chart_id: str,
    request: ChartExportRequest,
    db: AsyncSession = Depends(get_db)
) -> ChartExportResponse:
    """
    Export chart data to CSV/JSON/Excel format.

    Args:
        chart_id: Chart ID
        request: Export request parameters
        db: Database session

    Returns:
        Exported chart data

    Raises:
        HTTPException: If chart not found or export fails
    """
    try:
        # Get chart configuration
        chart_repo = ChartRepository(db)
        chart = await chart_repo.get(chart_id)

        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        # Get dataset
        dataset_repo = DatasetRepository(db)
        dataset = await dataset_repo.get(chart.dataset_id)

        # Create sample data (in production, load from dataset.file_path)
        import numpy as np

        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)

        sample_data = pd.DataFrame({
            "date": dates,
            "open": 100 + np.random.randn(100).cumsum(),
            "high": 102 + np.random.randn(100).cumsum(),
            "low": 98 + np.random.randn(100).cumsum(),
            "close": 100 + np.random.randn(100).cumsum(),
            "volume": np.random.randint(500000, 1500000, 100)
        })

        # Export to requested format
        chart_service = ChartService()

        if request.format == "csv":
            export_data = chart_service.export_to_csv(
                sample_data,
                columns=request.columns
            )
            filename = f"chart_{chart_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export format '{request.format}' not yet implemented"
            )

        return ChartExportResponse(
            chart_id=chart_id,
            format=request.format,
            data=export_data,
            filename=filename,
            size_bytes=len(export_data.encode('utf-8'))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chart data for {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export chart data: {str(e)}"
        )


@router.post("/{chart_id}/annotations", response_model=SuccessResponse)
async def add_chart_annotation(
    chart_id: str,
    request: AnnotationRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Add annotation to chart configuration.

    Args:
        chart_id: Chart ID
        request: Annotation request
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If chart not found or annotation fails
    """
    try:
        # Get chart configuration
        chart_repo = ChartRepository(db)
        chart = await chart_repo.get(chart_id)

        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart not found: {chart_id}"
            )

        # Add annotation to chart config
        current_config = chart.config or {}
        if "annotations" not in current_config:
            current_config["annotations"] = []

        # Convert annotation to dict and serialize datetime fields
        annotation_dict = request.annotation.model_dump()
        annotation_dict = prepare_annotation_for_storage(annotation_dict)
        current_config["annotations"].append(annotation_dict)

        # Update chart
        await chart_repo.update(chart_id, {"config": current_config})

        logger.info(f"Added annotation to chart {chart_id}")

        return SuccessResponse(
            message=f"Annotation added to chart {chart_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding annotation to chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add annotation: {str(e)}"
        )
