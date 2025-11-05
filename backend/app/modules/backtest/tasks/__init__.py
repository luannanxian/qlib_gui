"""
Backtest Tasks Module

Celery tasks for asynchronous backtesting operations.
TODO: Implement backtest tasks when backtest module is ready.
"""

from app.celery_app import celery_app


@celery_app.task(name="app.modules.backtest.tasks.placeholder")
def placeholder_task():
    """Placeholder task for backtest module."""
    return {"message": "Backtest tasks not yet implemented"}
