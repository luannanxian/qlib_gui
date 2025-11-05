"""
Database Module Export

This module provides a centralized export of all database components:
- Base models and mixins
- Session management
- Database models
- Repository classes
"""

from app.database.base import Base, BaseDBModel, TimestampMixin, SoftDeleteMixin, AuditMixin, UUIDMixin
from app.database.session import db_manager, get_db

# Import models to ensure they are registered with SQLAlchemy
from app.database.models import (
    Dataset,
    DataSource,
    DatasetStatus,
    ChartConfig,
    ChartType,
    UserPreferences,
    UserMode,
)

__all__ = [
    # Base classes
    "Base",
    "BaseDBModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "UUIDMixin",
    # Session management
    "db_manager",
    "get_db",
    # Models
    "Dataset",
    "ChartConfig",
    "UserPreferences",
    # Enums
    "DataSource",
    "DatasetStatus",
    "ChartType",
    "UserMode",
]
