"""
Database Repositories Export

This module exports all repository classes for easy import throughout the application.
"""

from app.database.repositories.base import BaseRepository
from app.database.repositories.dataset import DatasetRepository
from app.database.repositories.chart import ChartRepository
from app.database.repositories.user_preferences import UserPreferencesRepository
from app.database.repositories.import_task import ImportTaskRepository
from app.database.repositories.preprocessing import (
    PreprocessingRuleRepository,
    PreprocessingTaskRepository,
)
from app.database.repositories.strategy_template import StrategyTemplateRepository
from app.database.repositories.strategy_instance import StrategyInstanceRepository
from app.database.repositories.template_rating import TemplateRatingRepository

__all__ = [
    "BaseRepository",
    "DatasetRepository",
    "ChartRepository",
    "UserPreferencesRepository",
    "ImportTaskRepository",
    "PreprocessingRuleRepository",
    "PreprocessingTaskRepository",
    "StrategyTemplateRepository",
    "StrategyInstanceRepository",
    "TemplateRatingRepository",
]
