"""
Strategy Tasks Module

Celery tasks for asynchronous strategy operations.
TODO: Implement strategy tasks when strategy module is ready.
"""

from app.celery_app import celery_app


@celery_app.task(name="app.modules.strategy.tasks.placeholder")
def placeholder_task():
    """Placeholder task for strategy module."""
    return {"message": "Strategy tasks not yet implemented"}
