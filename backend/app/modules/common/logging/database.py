"""
Database Query Logging Module

Provides comprehensive database query logging:
- SQL query logging with parameters
- Query execution time tracking
- Slow query detection
- Connection pool monitoring
- Transaction logging
- Error logging
"""

import time
from typing import Optional, Any
from sqlalchemy import event
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.pool import Pool
from loguru import logger

from .context import get_correlation_id, get_user_id


class DatabaseQueryLogger:
    """
    SQLAlchemy event listener for query logging.

    Monitors database operations and logs:
    - Query execution with timing
    - Slow queries
    - Query errors
    - Connection pool usage
    """

    def __init__(
        self,
        slow_query_threshold_ms: float = 100.0,
        log_all_queries: bool = False,
        log_parameters: bool = True,
        sanitize_parameters: bool = True,
    ):
        """
        Initialize database query logger.

        Args:
            slow_query_threshold_ms: Threshold for slow query logging (ms)
            log_all_queries: Log all queries (not just slow ones)
            log_parameters: Include query parameters in logs
            sanitize_parameters: Sanitize sensitive parameter values
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.log_all_queries = log_all_queries
        self.log_parameters = log_parameters
        self.sanitize_parameters = sanitize_parameters

        # Track query execution times
        self._query_start_times = {}

    def setup_listeners(self, engine: Engine) -> None:
        """
        Setup SQLAlchemy event listeners on engine.

        Args:
            engine: SQLAlchemy engine instance

        Example:
            >>> from sqlalchemy import create_engine
            >>> engine = create_engine("postgresql://...")
            >>> query_logger = DatabaseQueryLogger()
            >>> query_logger.setup_listeners(engine)
        """
        # Query execution events
        event.listen(engine, "before_cursor_execute", self.before_cursor_execute)
        event.listen(engine, "after_cursor_execute", self.after_cursor_execute)

        # Error handling
        event.listen(engine, "handle_error", self.handle_error)

        # Connection pool events
        event.listen(engine.pool, "connect", self.on_connect)
        event.listen(engine.pool, "checkout", self.on_checkout)
        event.listen(engine.pool, "checkin", self.on_checkin)

        logger.info(
            "Database query logging configured",
            extra={
                "database": True,
                "slow_query_threshold_ms": self.slow_query_threshold_ms,
                "log_all_queries": self.log_all_queries,
            },
        )

    def before_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """
        Called before query execution.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: Whether executing multiple statements
        """
        # Store start time for this connection
        conn_id = id(conn)
        self._query_start_times[conn_id] = time.perf_counter()

    def after_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """
        Called after query execution.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: Whether executing multiple statements
        """
        # Calculate execution time
        conn_id = id(conn)
        start_time = self._query_start_times.pop(conn_id, None)

        if start_time is None:
            return

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Determine if we should log this query
        should_log = (
            self.log_all_queries or execution_time_ms > self.slow_query_threshold_ms
        )

        if not should_log:
            return

        # Prepare log data
        log_data = {
            "database": True,
            "query_time_ms": round(execution_time_ms, 2),
            "statement": self._truncate_statement(statement),
            "executemany": executemany,
            "correlation_id": get_correlation_id(),
            "user_id": get_user_id(),
        }

        # Add parameters if enabled
        if self.log_parameters and parameters:
            log_data["parameters"] = (
                self._sanitize_parameters(parameters)
                if self.sanitize_parameters
                else parameters
            )

        # Add slow query flag
        if execution_time_ms > self.slow_query_threshold_ms:
            log_data["slow_query"] = True

        # Determine log level
        if execution_time_ms > self.slow_query_threshold_ms * 10:
            log_level = "ERROR"
        elif execution_time_ms > self.slow_query_threshold_ms:
            log_level = "WARNING"
        else:
            log_level = "DEBUG"

        # Log the query
        logger.log(
            log_level,
            f"Database query executed in {execution_time_ms:.2f}ms",
            extra=log_data,
        )

    def handle_error(self, context: Any) -> None:
        """
        Called when a database error occurs.

        Args:
            context: Error context from SQLAlchemy
        """
        # Extract error information
        exception = context.original_exception
        statement = context.statement if hasattr(context, "statement") else None
        parameters = context.parameters if hasattr(context, "parameters") else None

        # Log the error
        logger.error(
            f"Database error: {type(exception).__name__}",
            extra={
                "database": True,
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "statement": self._truncate_statement(statement) if statement else None,
                "parameters": (
                    self._sanitize_parameters(parameters)
                    if parameters and self.sanitize_parameters
                    else parameters
                ),
                "correlation_id": get_correlation_id(),
                "user_id": get_user_id(),
            },
        )

    def on_connect(self, dbapi_conn: Any, connection_record: Any) -> None:
        """
        Called when a new database connection is created.

        Args:
            dbapi_conn: Database API connection
            connection_record: Connection record
        """
        logger.debug(
            "New database connection created",
            extra={
                "database": True,
                "event": "connection_created",
                "connection_id": id(dbapi_conn),
            },
        )

    def on_checkout(self, dbapi_conn: Any, connection_record: Any, connection_proxy: Any) -> None:
        """
        Called when a connection is checked out from the pool.

        Args:
            dbapi_conn: Database API connection
            connection_record: Connection record
            connection_proxy: Connection proxy
        """
        logger.trace(
            "Connection checked out from pool",
            extra={
                "database": True,
                "event": "connection_checkout",
                "connection_id": id(dbapi_conn),
            },
        )

    def on_checkin(self, dbapi_conn: Any, connection_record: Any) -> None:
        """
        Called when a connection is returned to the pool.

        Args:
            dbapi_conn: Database API connection
            connection_record: Connection record
        """
        logger.trace(
            "Connection returned to pool",
            extra={
                "database": True,
                "event": "connection_checkin",
                "connection_id": id(dbapi_conn),
            },
        )

    def _truncate_statement(self, statement: Optional[str], max_length: int = 500) -> Optional[str]:
        """
        Truncate long SQL statements for logging.

        Args:
            statement: SQL statement
            max_length: Maximum length

        Returns:
            Truncated statement
        """
        if statement is None:
            return None

        # Normalize whitespace
        normalized = " ".join(statement.split())

        if len(normalized) > max_length:
            return normalized[:max_length] + "..."

        return normalized

    def _sanitize_parameters(self, parameters: Any) -> Any:
        """
        Sanitize sensitive parameter values.

        Args:
            parameters: Query parameters

        Returns:
            Sanitized parameters
        """
        from .filters import sanitize_log_data

        return sanitize_log_data(parameters)


class ConnectionPoolMonitor:
    """
    Monitor SQLAlchemy connection pool metrics.

    Logs pool usage statistics for monitoring and optimization.
    """

    def __init__(self, log_interval_seconds: int = 60):
        """
        Initialize connection pool monitor.

        Args:
            log_interval_seconds: How often to log pool metrics
        """
        self.log_interval_seconds = log_interval_seconds

    def setup_monitoring(self, engine: Engine) -> None:
        """
        Setup connection pool monitoring.

        Args:
            engine: SQLAlchemy engine instance
        """
        pool = engine.pool

        # Log pool configuration
        logger.info(
            "Connection pool configured",
            extra={
                "database": True,
                "pool_size": pool.size() if hasattr(pool, "size") else "N/A",
                "max_overflow": pool._max_overflow if hasattr(pool, "_max_overflow") else "N/A",
                "timeout": pool._timeout if hasattr(pool, "_timeout") else "N/A",
            },
        )

        # Could set up periodic logging here using a background task

    def log_pool_status(self, pool: Pool) -> None:
        """
        Log current pool status.

        Args:
            pool: SQLAlchemy connection pool
        """
        try:
            # Get pool statistics
            pool_status = {
                "checked_in": pool.checkedin() if hasattr(pool, "checkedin") else "N/A",
                "checked_out": pool.checkedout() if hasattr(pool, "checkedout") else "N/A",
                "overflow": pool.overflow() if hasattr(pool, "overflow") else "N/A",
                "size": pool.size() if hasattr(pool, "size") else "N/A",
            }

            # Calculate utilization
            if isinstance(pool_status["checked_out"], int) and isinstance(
                pool_status["size"], int
            ):
                utilization = (
                    pool_status["checked_out"] / pool_status["size"] * 100
                    if pool_status["size"] > 0
                    else 0
                )
                pool_status["utilization_percent"] = round(utilization, 2)

            logger.info(
                "Connection pool status",
                extra={
                    "database": True,
                    "pool_status": pool_status,
                },
            )

        except Exception as e:
            logger.warning(
                f"Failed to get pool status: {e}",
                extra={"database": True},
            )


class TransactionLogger:
    """
    Log database transactions.

    Tracks transaction lifecycle and helps identify transaction issues.
    """

    def __init__(self):
        """Initialize transaction logger."""
        self._transaction_start_times = {}

    def setup_listeners(self, engine: Engine) -> None:
        """
        Setup transaction event listeners.

        Args:
            engine: SQLAlchemy engine instance
        """
        event.listen(engine, "begin", self.on_begin)
        event.listen(engine, "commit", self.on_commit)
        event.listen(engine, "rollback", self.on_rollback)

        logger.info(
            "Transaction logging configured",
            extra={"database": True},
        )

    def on_begin(self, conn: Connection) -> None:
        """
        Called when a transaction begins.

        Args:
            conn: Database connection
        """
        conn_id = id(conn)
        self._transaction_start_times[conn_id] = time.perf_counter()

        logger.debug(
            "Transaction started",
            extra={
                "database": True,
                "event": "transaction_begin",
                "connection_id": conn_id,
                "correlation_id": get_correlation_id(),
            },
        )

    def on_commit(self, conn: Connection) -> None:
        """
        Called when a transaction is committed.

        Args:
            conn: Database connection
        """
        conn_id = id(conn)
        start_time = self._transaction_start_times.pop(conn_id, None)

        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000

        logger.debug(
            "Transaction committed",
            extra={
                "database": True,
                "event": "transaction_commit",
                "connection_id": conn_id,
                "duration_ms": round(duration_ms, 2) if duration_ms else None,
                "correlation_id": get_correlation_id(),
            },
        )

    def on_rollback(self, conn: Connection) -> None:
        """
        Called when a transaction is rolled back.

        Args:
            conn: Database connection
        """
        conn_id = id(conn)
        start_time = self._transaction_start_times.pop(conn_id, None)

        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000

        logger.warning(
            "Transaction rolled back",
            extra={
                "database": True,
                "event": "transaction_rollback",
                "connection_id": conn_id,
                "duration_ms": round(duration_ms, 2) if duration_ms else None,
                "correlation_id": get_correlation_id(),
            },
        )


def setup_database_logging(
    engine: Engine,
    slow_query_threshold_ms: float = 100.0,
    log_all_queries: bool = False,
    enable_transaction_logging: bool = True,
    enable_pool_monitoring: bool = True,
) -> None:
    """
    Setup comprehensive database logging.

    Args:
        engine: SQLAlchemy engine instance
        slow_query_threshold_ms: Threshold for slow query logging (ms)
        log_all_queries: Log all queries (not just slow ones)
        enable_transaction_logging: Enable transaction lifecycle logging
        enable_pool_monitoring: Enable connection pool monitoring

    Example:
        >>> from sqlalchemy import create_engine
        >>> from app.modules.common.logging.database import setup_database_logging
        >>>
        >>> engine = create_engine("postgresql://...")
        >>> setup_database_logging(engine, slow_query_threshold_ms=100)
    """
    # Setup query logging
    query_logger = DatabaseQueryLogger(
        slow_query_threshold_ms=slow_query_threshold_ms,
        log_all_queries=log_all_queries,
    )
    query_logger.setup_listeners(engine)

    # Setup transaction logging
    if enable_transaction_logging:
        transaction_logger = TransactionLogger()
        transaction_logger.setup_listeners(engine)

    # Setup pool monitoring
    if enable_pool_monitoring:
        pool_monitor = ConnectionPoolMonitor()
        pool_monitor.setup_monitoring(engine)

    logger.info(
        "Database logging fully configured",
        extra={
            "database": True,
            "query_logging": True,
            "transaction_logging": enable_transaction_logging,
            "pool_monitoring": enable_pool_monitoring,
        },
    )
