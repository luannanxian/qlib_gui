"""
User Preferences SQLAlchemy Model
"""

import enum

from sqlalchemy import String, JSON, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseDBModel


class UserMode(str, enum.Enum):
    """User experience mode"""
    BEGINNER = "beginner"
    EXPERT = "expert"


class UserPreferences(BaseDBModel):
    """
    User preferences model for storing user-specific settings and customizations

    This model stores per-user preferences including:
    - UI mode (beginner/expert)
    - Language preference
    - Theme settings
    - Tooltip preferences
    - Completed onboarding guides
    - Additional custom settings
    """

    __tablename__ = "user_preferences"

    # Core fields
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique user identifier"
    )

    mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="beginner",
        server_default="beginner",
        index=True,
        comment="User experience mode (beginner/expert)"
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="UI language preference (ISO 639-1 code)"
    )

    theme: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="light",
        server_default="light",
        comment="UI theme preference"
    )

    show_tooltips: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",  # MySQL uses 1 for true
        comment="Whether to show UI tooltips"
    )

    # JSON fields for flexible storage
    completed_guides: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="List of completed onboarding guide IDs (JSON array)"
    )

    settings: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Additional user-specific settings (JSON object)"
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_user_prefs_user_mode", "user_id", "mode"),
        Index("ix_user_prefs_deleted_created", "is_deleted", "created_at"),  # For soft-delete queries
        {
            "comment": "User preferences and settings storage table",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4"
        }
    )

    def __repr__(self) -> str:
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, mode={self.mode})>"
