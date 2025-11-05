"""
Technical Indicator Component Library Models

This module contains all database models for the technical indicator system:
- IndicatorComponent: Technical indicator definitions
- CustomFactor: User-defined custom factors
- FactorValidationResult: Factor validation results
- UserFactorLibrary: User's factor library
- FactorParameter: Factor parameter definitions
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, JSON,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel


# ===================== Enums =====================

class IndicatorCategory(str, PyEnum):
    """Indicator category classification"""
    TREND = "trend"  # 趋势类指标
    MOMENTUM = "momentum"  # 动量类指标
    VOLATILITY = "volatility"  # 波动率指标
    VOLUME = "volume"  # 成交量指标
    SUPPORT_RESISTANCE = "support_resistance"  # 支撑阻力
    CYCLE = "cycle"  # 周期类指标
    FINANCIAL = "financial"  # 财务指标
    CUSTOM = "custom"  # 自定义指标


class IndicatorSource(str, PyEnum):
    """Indicator source type"""
    TALIB = "talib"  # TA-Lib技术指标
    QLIB = "qlib"  # Qlib内置指标
    FINANCIAL = "financial"  # 财务指标
    CUSTOM = "custom"  # 用户自定义


class ParameterType(str, PyEnum):
    """Parameter data type"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"
    ARRAY = "array"


class FactorStatus(str, PyEnum):
    """Custom factor status"""
    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布到个人库
    SHARED = "shared"  # 已分享到社区


class ValidationStatus(str, PyEnum):
    """Validation execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationType(str, PyEnum):
    """Validation type"""
    IC_ANALYSIS = "ic_analysis"  # IC值分析
    IC_RANK_ANALYSIS = "ic_rank_analysis"  # IC Rank分析
    LAYERED_BACKTEST = "layered_backtest"  # 分层回测
    SHARPE_RATIO = "sharpe_ratio"  # 夏普比率
    FACTOR_DISTRIBUTION = "factor_distribution"  # 因子分布


class FormulaLanguage(str, PyEnum):
    """Formula expression language"""
    PYTHON = "python"  # Python表达式
    QLIB_ALPHA = "qlib_alpha"  # Qlib Alpha表达式


class LibraryItemStatus(str, PyEnum):
    """Library item status"""
    ACTIVE = "active"  # 激活
    ARCHIVED = "archived"  # 归档


# ===================== Models =====================

class IndicatorComponent(BaseDBModel):
    """
    Technical Indicator Component

    Stores technical indicator definitions including TA-Lib indicators,
    Qlib built-in indicators, and financial indicators.
    """
    __tablename__ = "indicator_components"

    # Basic Information
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Indicator code (e.g., 'SMA', 'EMA')"
    )
    name_zh: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Chinese name"
    )
    name_en: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="English name"
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Indicator category"
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Indicator source"
    )

    # Description
    description_zh: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Chinese description"
    )
    description_en: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="English description"
    )

    # Formula & Parameters
    formula: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Indicator calculation formula"
    )
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Parameter definitions (JSON)"
    )
    default_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Default parameter values (JSON)"
    )

    # Usage & Configuration
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="System built-in indicator"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        index=True,
        comment="Enabled for use"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Usage count"
    )

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tags for search (JSON array)"
    )
    example_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Example usage code"
    )

    # Relationships
    custom_factors: Mapped[list["CustomFactor"]] = relationship(
        "CustomFactor",
        back_populates="base_indicator",
        foreign_keys="CustomFactor.base_indicator_id"
    )

    __table_args__ = (
        Index("idx_indicator_category_source", "category", "source"),
        Index("idx_indicator_enabled_system", "is_enabled", "is_system"),
    )


class CustomFactor(BaseDBModel):
    """
    Custom Factor Definition

    User-defined custom factors with formulas, validation results,
    and sharing capabilities.
    """
    __tablename__ = "custom_factors"

    # Basic Information
    factor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Factor name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Factor description"
    )

    # Formula Definition
    formula: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Factor formula expression"
    )
    formula_language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FormulaLanguage.QLIB_ALPHA.value,
        comment="Formula language type"
    )

    # Base Indicator (Optional)
    base_indicator_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("indicator_components.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Base indicator ID (if derived from one)"
    )

    # Status & Ownership
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FactorStatus.DRAFT.value,
        index=True,
        comment="Factor status"
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )

    # Publishing & Sharing
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
        comment="Shared to community"
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Publishing timestamp"
    )
    shared_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Community sharing timestamp"
    )

    # Usage Statistics
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Usage count"
    )
    clone_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Clone count"
    )

    # Cloning Information
    cloned_from_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("custom_factors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source factor ID (if cloned)"
    )

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tags for search (JSON array)"
    )

    # Relationships
    base_indicator: Mapped[Optional["IndicatorComponent"]] = relationship(
        "IndicatorComponent",
        back_populates="custom_factors",
        foreign_keys=[base_indicator_id]
    )
    validation_results: Mapped[list["FactorValidationResult"]] = relationship(
        "FactorValidationResult",
        back_populates="factor",
        cascade="all, delete-orphan"
    )
    library_items: Mapped[list["UserFactorLibrary"]] = relationship(
        "UserFactorLibrary",
        back_populates="factor",
        cascade="all, delete-orphan"
    )

    # Self-referential relationship for cloning
    cloned_from: Mapped[Optional["CustomFactor"]] = relationship(
        "CustomFactor",
        remote_side="CustomFactor.id",
        foreign_keys=[cloned_from_id],
        backref="clones"
    )

    __table_args__ = (
        Index("idx_factor_user_status", "user_id", "status"),
        Index("idx_factor_public", "is_public", "status"),
    )


class FactorValidationResult(BaseDBModel):
    """
    Factor Validation Result

    Stores validation results for custom factors including IC analysis,
    backtesting results, and performance metrics.
    """
    __tablename__ = "factor_validation_results"

    # Factor Reference
    factor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("custom_factors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Custom factor ID"
    )

    # Validation Configuration
    validation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Validation type"
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="Dataset ID used for validation"
    )

    # Execution Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ValidationStatus.PENDING.value,
        index=True,
        comment="Validation status"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Validation start time"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Validation completion time"
    )

    # Results
    metrics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Validation metrics (JSON)"
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Detailed results (JSON)"
    )

    # Error Information
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message (if failed)"
    )

    # Relationships
    factor: Mapped["CustomFactor"] = relationship(
        "CustomFactor",
        back_populates="validation_results"
    )

    __table_args__ = (
        Index("idx_validation_factor_type", "factor_id", "validation_type"),
        Index("idx_validation_status", "status", "created_at"),
    )


class UserFactorLibrary(BaseDBModel):
    """
    User Factor Library

    Manages users' personal factor libraries with favorites and usage tracking.
    """
    __tablename__ = "user_factor_library"

    # User & Factor
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID"
    )
    factor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("custom_factors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Custom factor ID"
    )

    # Library Management
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=LibraryItemStatus.ACTIVE.value,
        index=True,
        comment="Item status in library"
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
        comment="Marked as favorite"
    )

    # Usage Tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Usage count"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last usage timestamp"
    )

    # Custom Settings
    custom_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="User's custom name for this factor"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User's notes about this factor"
    )

    # Relationships
    factor: Mapped["CustomFactor"] = relationship(
        "CustomFactor",
        back_populates="library_items"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "factor_id", name="uq_user_factor"),
        Index("idx_library_user_status", "user_id", "status"),
        Index("idx_library_favorite", "user_id", "is_favorite"),
    )
