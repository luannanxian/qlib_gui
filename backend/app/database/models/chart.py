"""
Chart Configuration SQLAlchemy Model
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, JSON, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset


class ChartType(str, enum.Enum):
    """Chart visualization types"""
    KLINE = "kline"
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class ChartConfig(BaseDBModel):
    """
    Chart configuration model for storing visualization settings

    Relationships:
    - Many-to-One with Dataset (many charts can belong to one dataset)
    """

    __tablename__ = "chart_configs"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Chart name/title"
    )

    chart_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Chart visualization type"
    )

    # Foreign key to Dataset
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent dataset"
    )

    # JSON configuration for chart-specific settings
    config: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Chart configuration (JSON object)"
    )

    # Optional description
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Chart description"
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="charts",
        lazy="selectin"  # Eager loading for async performance
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_chart_dataset_type", "dataset_id", "chart_type"),
        Index("ix_chart_type_name", "chart_type", "name"),
        Index("ix_chart_deleted_created", "is_deleted", "created_at"),  # For soft-delete queries
        Index("ix_chart_deleted_updated", "is_deleted", "updated_at"),  # For recently updated queries
        Index("ix_chart_dataset_deleted", "dataset_id", "is_deleted"),  # For filtering charts by dataset
        {
            "comment": "Chart configuration storage table",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4"
        }
    )

    def __repr__(self) -> str:
        return f"<ChartConfig(id={self.id}, name={self.name}, type={self.chart_type})>"
