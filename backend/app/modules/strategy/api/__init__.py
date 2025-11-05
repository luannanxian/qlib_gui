"""
Strategy API Module

Exports the FastAPI router for strategy-related endpoints.
"""

from app.modules.strategy.api.strategy_api import router

__all__ = ["router"]
