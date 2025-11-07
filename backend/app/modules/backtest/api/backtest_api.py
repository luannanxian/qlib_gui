"""
Backtest API Endpoints

Handles backtest configuration and execution operations.
"""

from typing import Dict, Any
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repositories.backtest_repository import BacktestRepository
from app.modules.backtest.services.config_service import BacktestConfigService
from app.modules.backtest.services.execution_service import BacktestExecutionService
from app.modules.backtest.exceptions import (
    InvalidConfigError,
    InvalidDateRangeError,
    InvalidCapitalError,
    ResourceNotFoundError
)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


# Dependency to get services
async def get_config_service(session: AsyncSession = Depends(get_db)) -> BacktestConfigService:
    """Get BacktestConfigService instance."""
    repository = BacktestRepository(session)
    return BacktestConfigService(repository)


async def get_execution_service(session: AsyncSession = Depends(get_db)) -> BacktestExecutionService:
    """Get BacktestExecutionService instance."""
    repository = BacktestRepository(session)
    return BacktestExecutionService(repository)


@router.post(
    "/config",
    status_code=status.HTTP_201_CREATED,
    summary="Create backtest configuration"
)
async def create_config(
    config_data: Dict[str, Any],
    service: BacktestConfigService = Depends(get_config_service)
):
    """Create a new backtest configuration."""
    try:
        # Convert string dates to date objects
        if "start_date" in config_data and isinstance(config_data["start_date"], str):
            config_data["start_date"] = date.fromisoformat(config_data["start_date"])
        if "end_date" in config_data and isinstance(config_data["end_date"], str):
            config_data["end_date"] = date.fromisoformat(config_data["end_date"])

        # Convert string decimals to Decimal objects
        if "initial_capital" in config_data:
            config_data["initial_capital"] = Decimal(str(config_data["initial_capital"]))
        if "commission_rate" in config_data:
            config_data["commission_rate"] = Decimal(str(config_data["commission_rate"]))
        if "slippage" in config_data:
            config_data["slippage"] = Decimal(str(config_data["slippage"]))

        config = await service.create_config(config_data)

        # Convert to dict for response
        return {
            "id": config.id,
            "strategy_id": config.strategy_id,
            "dataset_id": config.dataset_id,
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "initial_capital": str(config.initial_capital),
            "commission_rate": str(config.commission_rate),
            "slippage": str(config.slippage)
        }
    except (InvalidConfigError, InvalidDateRangeError, InvalidCapitalError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/config/{config_id}",
    summary="Get backtest configuration"
)
async def get_config(
    config_id: str,
    service: BacktestConfigService = Depends(get_config_service)
):
    """Retrieve a backtest configuration by ID."""
    try:
        config = await service.get_config_by_id(config_id)
        return {
            "id": config.id,
            "strategy_id": config.strategy_id,
            "dataset_id": config.dataset_id,
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "initial_capital": str(config.initial_capital),
            "commission_rate": str(config.commission_rate),
            "slippage": str(config.slippage)
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/config/{config_id}",
    summary="Update backtest configuration"
)
async def update_config(
    config_id: str,
    update_data: Dict[str, Any],
    service: BacktestConfigService = Depends(get_config_service)
):
    """Update a backtest configuration."""
    try:
        # Convert string decimals to Decimal objects
        if "initial_capital" in update_data:
            update_data["initial_capital"] = Decimal(str(update_data["initial_capital"]))
        if "commission_rate" in update_data:
            update_data["commission_rate"] = Decimal(str(update_data["commission_rate"]))
        if "slippage" in update_data:
            update_data["slippage"] = Decimal(str(update_data["slippage"]))

        config = await service.update_config(config_id, update_data)
        return {
            "id": config.id,
            "strategy_id": config.strategy_id,
            "dataset_id": config.dataset_id,
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "initial_capital": str(config.initial_capital),
            "commission_rate": str(config.commission_rate),
            "slippage": str(config.slippage)
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidConfigError, InvalidDateRangeError, InvalidCapitalError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/config/{config_id}",
    summary="Delete backtest configuration"
)
async def delete_config(
    config_id: str,
    service: BacktestConfigService = Depends(get_config_service)
):
    """Delete a backtest configuration."""
    try:
        await service.delete_config(config_id)
        return {"message": "Configuration deleted successfully"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{config_id}/start",
    status_code=status.HTTP_201_CREATED,
    summary="Start backtest execution"
)
async def start_backtest(
    config_id: str,
    service: BacktestExecutionService = Depends(get_execution_service)
):
    """Start a backtest execution."""
    try:
        result = await service.start_backtest(config_id)
        return {
            "id": result.id,
            "config_id": result.config_id,
            "status": result.status,
            "total_return": str(result.total_return),
            "annual_return": str(result.annual_return),
            "sharpe_ratio": str(result.sharpe_ratio),
            "max_drawdown": str(result.max_drawdown),
            "win_rate": str(result.win_rate)
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{result_id}/status",
    summary="Get backtest status"
)
async def get_backtest_status(
    result_id: str,
    service: BacktestExecutionService = Depends(get_execution_service)
):
    """Get the current status of a backtest."""
    try:
        status_value = await service.get_backtest_status(result_id)
        return {"status": status_value}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
