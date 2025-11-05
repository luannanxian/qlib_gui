"""
Celery Worker 优雅关闭处理
添加 worker shutdown 信号处理
"""

from celery.signals import worker_shutdown
from app.celery_app import celery_app


@worker_shutdown.connect
def handle_worker_shutdown(sender, **kwargs):
    """在 Worker 关闭前保存状态并清理资源"""
    from app.utils.logger import logger

    logger.warning(
        "Worker shutting down, cleaning up resources...",
        extra={"worker": sender}
    )

    # 这里可以添加清理逻辑
    # 例如：保存未完成任务的状态、关闭数据库连接等
    try:
        # 执行清理操作
        pass
    except Exception as e:
        logger.error(f"Error during worker shutdown: {e}", exc_info=True)
