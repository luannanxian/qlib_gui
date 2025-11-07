"""
Backtest SQLAlchemy Models

This module defines the database models for the Backtest System:
- BacktestConfig: Configuration for backtest runs
- BacktestResult: Results and metrics from backtest execution
- BacktestStatus: Enum for backtest execution status
"""

import enum
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Date, Numeric, JSON, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel


class BacktestStatus(str, enum.Enum):
    """Backtest execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BacktestConfig(BaseDBModel):
    """
    Backtest Configuration model for managing backtest parameters

    Stores all configuration needed to run a backtest including:
    - Strategy and dataset references
    - Date range
    - Capital and trading costs
    - Custom parameters

    Relationships:
    - Many-to-One with StrategyInstance (via strategy_id)
    - Many-to-One with Dataset (via dataset_id)
    - One-to-Many with BacktestResult (one config can have multiple results)
    """

    __tablename__ = "backtest_configs"

    # Foreign Keys
    strategy_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Reference to strategy instance"
    )

    dataset_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Reference to dataset"
    )

    # Date Range
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Backtest start date"
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Backtest end date"
    )

    # Capital and Costs
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=2),
        nullable=False,
        comment="Initial capital for backtest"
    )

    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        comment="Commission rate (0-1)"
    )

    slippage: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        comment="Slippage rate (0-1)"
    )

    # Configuration Parameters (JSON)
    config_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional configuration parameters (benchmark, freq, etc.)"
    )

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_backtest_config_strategy', 'strategy_id'),
        Index('idx_backtest_config_dataset', 'dataset_id'),
        Index('idx_backtest_config_dates', 'start_date', 'end_date'),
        CheckConstraint('initial_capital > 0', name='check_positive_capital'),
        CheckConstraint('commission_rate >= 0 AND commission_rate <= 1', name='check_commission_range'),
        CheckConstraint('slippage >= 0 AND slippage <= 1', name='check_slippage_range'),
        CheckConstraint('start_date <= end_date', name='check_date_range'),
    )


class BacktestResult(BaseDBModel):
    """
    Backtest Result model for storing backtest execution results

    Stores:
    - Execution status
    - Performance metrics (returns, sharpe, drawdown, etc.)
    - Trade statistics
    - Detailed metrics in JSON format

    Relationships:
    - Many-to-One with BacktestConfig (via config_id)
    """

    __tablename__ = "backtest_results"

    # Foreign Key
    config_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Reference to backtest configuration"
    )

    # Execution Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Backtest execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"
    )

    # Performance Metrics
    total_return: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        default=Decimal("0.0"),
        comment="Total return (e.g., 0.25 = 25%)"
    )

    annual_return: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        default=Decimal("0.0"),
        comment="Annualized return"
    )

    sharpe_ratio: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=False,
        default=Decimal("0.0"),
        comment="Sharpe ratio"
    )

    max_drawdown: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        default=Decimal("0.0"),
        comment="Maximum drawdown (e.g., 0.15 = 15%)"
    )

    win_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        default=Decimal("0.0"),
        comment="Win rate (0-1)"
    )

    # Detailed Metrics (JSON)
    metrics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Detailed performance metrics (volatility, sortino, calmar, etc.)"
    )

    # Trade Statistics (JSON)
    trades: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Trade statistics (total_trades, winning_trades, avg_win, etc.)"
    )

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_backtest_result_config', 'config_id'),
        Index('idx_backtest_result_status', 'status'),
        Index('idx_backtest_result_performance', 'total_return', 'sharpe_ratio'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 1', name='check_win_rate_range'),
    )
