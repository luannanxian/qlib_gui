"""
Celery Application Configuration

Configures Celery for async task processing with Redis broker.
"""

import os
from logging.handlers import RotatingFileHandler

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, worker_ready

from app.config import settings

# Create Celery app
celery_app = Celery(
    "qlib_ui",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Import signal handlers (must be after celery_app creation)
from app import celery_signals  # noqa: F401

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Retry settings with exponential backoff and jitter
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_autoretry_for=(Exception,),  # Auto-retry for any exception
    task_retry_backoff=True,  # Enable exponential backoff
    task_retry_backoff_max=600,  # Max retry delay: 10 minutes
    task_retry_jitter=True,  # Add random jitter to prevent thundering herd

    # Task routing
    task_routes={
        "app.modules.data_management.tasks.*": {"queue": "data_import"},
        "app.modules.backtest.tasks.*": {"queue": "backtest"},
        "app.modules.strategy.tasks.*": {"queue": "strategy"},
    },
)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(
    [
        "app.modules.data_management.tasks",
        "app.modules.backtest.tasks",
        "app.modules.strategy.tasks",
    ],
    force=True,
)


@worker_ready.connect
def setup_log_rotation(sender=None, **kwargs):
    """
    Configure log rotation for Celery worker.

    This prevents log files from consuming excessive disk space
    by rotating logs when they reach 10MB and keeping 5 backup files.
    """
    import logging

    # Get Celery logger
    celery_logger = logging.getLogger("celery")

    # Ensure log directory exists
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    # Create rotating file handler
    log_file = os.path.join(log_dir, "celery.log")
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )

    # Set formatter
    formatter = logging.Formatter(
        "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to Celery logger
    celery_logger.addHandler(handler)
    celery_logger.setLevel(logging.INFO)

    celery_logger.info("Log rotation configured: max 10MB per file, 5 backups")


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log task start."""
    from app.utils.logger import logger

    logger.info(
        "Task started",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": args,
            "kwargs": kwargs,
        },
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra
):
    """Log task completion."""
    from app.utils.logger import logger

    logger.info(
        "Task completed",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "result": str(retval)[:200] if retval else None,
        },
    )


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **extra
):
    """Log task failure."""
    from app.utils.logger import logger

    logger.error(
        "Task failed",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "args": args,
            "kwargs": kwargs,
        },
        exc_info=exception,
    )
