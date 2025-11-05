"""
Strategy Template and Instance SQLAlchemy Models

This module defines the database models for the Strategy Template System:
- StrategyTemplate: Built-in and custom strategy templates
- StrategyInstance: User's strategies based on templates
- TemplateRating: User ratings for templates
"""

import enum
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, Enum, JSON, Index, CheckConstraint, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel


# Enums for Strategy System
class StrategyCategory(str, enum.Enum):
    """Strategy template categories"""
    TREND_FOLLOWING = "TREND_FOLLOWING"
    OSCILLATION = "OSCILLATION"
    MULTI_FACTOR = "MULTI_FACTOR"


class StrategyStatus(str, enum.Enum):
    """Strategy instance status"""
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class NodeType(str, enum.Enum):
    """Logic flow node types"""
    INDICATOR = "INDICATOR"
    CONDITION = "CONDITION"
    SIGNAL = "SIGNAL"
    POSITION = "POSITION"
    STOP_LOSS = "STOP_LOSS"
    STOP_PROFIT = "STOP_PROFIT"


class SignalType(str, enum.Enum):
    """Signal types for trading"""
    BUY = "BUY"
    SELL = "SELL"


class PositionType(str, enum.Enum):
    """Position management types"""
    FIXED = "FIXED"
    DYNAMIC = "DYNAMIC"


class StopLossType(str, enum.Enum):
    """Stop loss strategy types"""
    PERCENTAGE = "PERCENTAGE"
    MA_BASED = "MA_BASED"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class StrategyTemplate(BaseDBModel):
    """
    Strategy Template model for managing built-in and custom strategy templates

    Relationships:
    - One-to-Many with StrategyInstance (one template can have multiple instances)
    - One-to-Many with TemplateRating (one template can have multiple ratings)
    """

    __tablename__ = "strategy_templates"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Template name"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Template description"
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Strategy category (TREND_FOLLOWING, OSCILLATION, MULTI_FACTOR)"
    )

    # JSON fields for flexible storage
    logic_flow: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Visual flow diagram data (nodes and edges)"
    )

    parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Parameter definitions with defaults and ranges"
    )

    # Template metadata
    is_system_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
        comment="True for built-in templates, False for custom"
    )

    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User ID for custom templates (NULL for system templates)"
    )

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
        comment="Number of times template has been used"
    )

    rating_average: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.0,
        server_default="0.0",
        comment="Average rating (0-5)"
    )

    rating_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of ratings received"
    )

    # Backtest example data
    backtest_example: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Historical backtest results for demonstration"
    )

    # Relationships
    instances: Mapped[List["StrategyInstance"]] = relationship(
        "StrategyInstance",
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        foreign_keys="[StrategyInstance.template_id]"
    )

    ratings: Mapped[List["TemplateRating"]] = relationship(
        "TemplateRating",
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        foreign_keys="[TemplateRating.template_id]"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("usage_count >= 0", name="check_usage_count_non_negative"),
        CheckConstraint("rating_count >= 0", name="check_rating_count_non_negative"),
        CheckConstraint("rating_average >= 0 AND rating_average <= 5", name="check_rating_average_range"),
        # Composite indexes for common query patterns
        Index("ix_template_category_system", "category", "is_system_template"),
        Index("ix_template_usage_count_desc", "usage_count"),  # For popular templates
        Index("ix_template_user_category", "user_id", "category"),
        Index("ix_template_deleted_created", "is_deleted", "created_at"),
        {"comment": "Strategy template storage table", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<StrategyTemplate(id={self.id}, name={self.name}, category={self.category})>"


class StrategyInstance(BaseDBModel):
    """
    Strategy Instance model for user's strategies based on templates

    Relationships:
    - Many-to-One with StrategyTemplate (optional - can be custom)
    - Self-referential for version history
    """

    __tablename__ = "strategy_instances"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Strategy instance name"
    )

    template_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("strategy_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to template (NULL for custom strategies)"
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )

    # JSON fields for flexible storage
    logic_flow: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Modified logic flow from template or custom"
    )

    parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="User-configured parameter values"
    )

    # Status and version
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
        index=True,
        comment="Strategy status (DRAFT, TESTING, ACTIVE, ARCHIVED)"
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Version number for snapshots"
    )

    parent_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("strategy_instances.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to parent version (for version history)"
    )

    # Relationships
    template: Mapped["StrategyTemplate"] = relationship(
        "StrategyTemplate",
        back_populates="instances",
        lazy="selectin",
        foreign_keys=[template_id]
    )

    # Self-referential relationship for version history
    parent_version: Mapped["StrategyInstance"] = relationship(
        "StrategyInstance",
        remote_side="[StrategyInstance.id]",
        foreign_keys=[parent_version_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("version >= 1", name="check_version_positive"),
        # Composite indexes for common query patterns
        Index("ix_instance_user_status", "user_id", "status"),
        Index("ix_instance_template_user", "template_id", "user_id"),
        Index("ix_instance_deleted_created", "is_deleted", "created_at"),
        Index("ix_instance_parent_version", "parent_version_id"),
        {"comment": "Strategy instance storage table", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<StrategyInstance(id={self.id}, name={self.name}, status={self.status})>"


class TemplateRating(BaseDBModel):
    """
    Template Rating model for user ratings of strategy templates

    Relationships:
    - Many-to-One with StrategyTemplate
    """

    __tablename__ = "template_ratings"

    # Core fields
    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategy_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to rated template"
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID who rated the template"
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rating value (1-5)"
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional rating comment"
    )

    # Relationships
    template: Mapped["StrategyTemplate"] = relationship(
        "StrategyTemplate",
        back_populates="ratings",
        lazy="selectin",
        foreign_keys=[template_id]
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        # Unique constraint: one rating per user per template
        Index("ix_rating_unique_user_template", "user_id", "template_id", unique=True),
        Index("ix_rating_template_created", "template_id", "created_at"),
        {"comment": "Template rating storage table", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<TemplateRating(id={self.id}, template_id={self.template_id}, rating={self.rating})>"
