"""
Test script to verify logging system implementation and demonstrate usage.

This script tests all major components of the logging system:
1. Basic logging configuration
2. Context management (correlation_id, user_id)
3. Formatters (JSON and development)
4. PII filtering
5. Decorators
6. Audit logging
7. Database logging integration
"""

import asyncio
import tempfile
import shutil
from pathlib import Path

# Import logging components
from app.modules.common.logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    set_user_id,
    clear_context,
    log_execution,
    log_async_execution,
    AuditLogger,
    AuditEventType,
    sanitize_log_data,
)
from app.modules.common.logging.audit import AuditSeverity


# Test functions
@log_execution(level="INFO", log_args=True, log_result=True)
def test_sync_function(data: dict, count: int = 10):
    """Test synchronous function with logging decorator."""
    return {"processed": True, "count": count}


@log_async_execution(level="INFO", log_args=True, log_result=True)
async def test_async_function(user_id: str, action: str):
    """Test asynchronous function with logging decorator."""
    await asyncio.sleep(0.1)  # Simulate async work
    return {"user_id": user_id, "action": action, "status": "completed"}


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "="*80)
    print("TEST 1: Basic Logging")
    print("="*80)

    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # With extra fields
    logger.info(
        "Message with extra fields",
        extra={
            "user_id": "user_123",
            "action": "test",
            "metadata": {"key": "value"}
        }
    )

    print("✅ Basic logging test completed")


def test_context_management():
    """Test context variables for correlation ID and user ID."""
    print("\n" + "="*80)
    print("TEST 2: Context Management")
    print("="*80)

    logger = get_logger(__name__)

    # Set context
    correlation_id = set_correlation_id()
    set_user_id("user_456")

    logger.info("Message with context", extra={
        "correlation_id": correlation_id,
        "operation": "context_test"
    })

    # Clear context
    clear_context()

    logger.info("Message after context cleared")

    print("✅ Context management test completed")


def test_pii_filtering():
    """Test PII and sensitive data filtering."""
    print("\n" + "="*80)
    print("TEST 3: PII Filtering")
    print("="*80)

    logger = get_logger(__name__)

    # Sensitive data
    sensitive_data = {
        "username": "john_doe",
        "password": "secret123456",
        "email": "john@example.com",
        "api_key": "sk-1234567890abcdef1234567890abcdef",
        "credit_card": "4532-1234-5678-9010",
        "normal_field": "this should not be filtered"
    }

    # Log with sanitization
    sanitized = sanitize_log_data(sensitive_data)
    logger.info("User data logged", extra={"data": sanitized})

    print("✅ PII filtering test completed")


def test_decorators():
    """Test logging decorators."""
    print("\n" + "="*80)
    print("TEST 4: Logging Decorators")
    print("="*80)

    # Test sync function
    result = test_sync_function({"key": "value"}, count=5)
    print(f"Sync function result: {result}")

    print("✅ Decorator test completed")


async def test_async_decorators():
    """Test async logging decorators."""
    print("\n" + "="*80)
    print("TEST 5: Async Logging Decorators")
    print("="*80)

    # Test async function
    result = await test_async_function("user_789", "data_processing")
    print(f"Async function result: {result}")

    print("✅ Async decorator test completed")


def test_audit_logging():
    """Test audit logging system."""
    print("\n" + "="*80)
    print("TEST 6: Audit Logging")
    print("="*80)

    set_correlation_id()
    set_user_id("admin_user_123")

    # Test authentication event
    AuditLogger.log_authentication(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id="user_123",
        username="john_doe",
        ip_address="192.168.1.100",
        success=True
    )

    # Test authorization event
    AuditLogger.log_authorization(
        event_type=AuditEventType.ACCESS_GRANTED,
        user_id="user_123",
        resource_type="dataset",
        resource_id="dataset_456",
        action="read",
        granted=True
    )

    # Test data access event
    AuditLogger.log_data_access(
        event_type=AuditEventType.DATA_UPDATED,
        user_id="user_123",
        resource_type="model",
        resource_id="model_789",
        action="update",
        records_affected=10
    )

    # Test security violation
    AuditLogger.log_security_violation(
        event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
        user_id="user_123",
        ip_address="192.168.1.100",
        violation_type="api_rate_limit",
        details={"limit": 100, "actual": 150, "window": "1m"}
    )

    # Test admin action
    AuditLogger.log_admin_action(
        event_type=AuditEventType.USER_DEACTIVATED,
        admin_user_id="admin_123",
        target_user_id="user_456",
        action="deactivate",
        changes={"active": {"before": True, "after": False}}
    )

    # Test system event
    AuditLogger.log_event(
        event_type=AuditEventType.SYSTEM_STARTUP,
        severity=AuditSeverity.LOW,
        message="System started successfully",
        details={"version": "1.0.0", "environment": "test"}
    )

    clear_context()

    print("✅ Audit logging test completed")


def test_error_logging():
    """Test error logging with exceptions."""
    print("\n" + "="*80)
    print("TEST 7: Error Logging")
    print("="*80)

    logger = get_logger(__name__)

    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception(
            "Error occurred during calculation",
            extra={
                "operation": "division",
                "values": {"numerator": 10, "denominator": 0}
            }
        )

    print("✅ Error logging test completed")


def test_performance_logging():
    """Test performance and slow operation logging."""
    print("\n" + "="*80)
    print("TEST 8: Performance Logging")
    print("="*80)

    logger = get_logger(__name__)

    import time

    # Simulate slow operation
    start_time = time.perf_counter()
    time.sleep(0.15)  # Simulate 150ms operation
    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.warning(
        "Slow operation detected",
        extra={
            "operation": "data_processing",
            "execution_time_ms": round(duration_ms, 2),
            "threshold_ms": 100,
            "slow_operation": True
        }
    )

    print("✅ Performance logging test completed")


def main():
    """Run all logging tests."""
    print("\n" + "="*80)
    print("QLIB-UI LOGGING SYSTEM TEST")
    print("="*80)

    # Create temporary log directory for testing
    temp_log_dir = tempfile.mkdtemp()
    print(f"\nLog directory: {temp_log_dir}")

    try:
        # Setup logging
        setup_logging(
            log_level="DEBUG",
            log_dir=temp_log_dir,
            environment="development"
        )

        print("\n✅ Logging system configured successfully")

        # Run tests
        test_basic_logging()
        test_context_management()
        test_pii_filtering()
        test_decorators()

        # Run async tests
        asyncio.run(test_async_decorators())

        test_audit_logging()
        test_error_logging()
        test_performance_logging()

        # Show log files created
        print("\n" + "="*80)
        print("LOG FILES CREATED")
        print("="*80)

        log_path = Path(temp_log_dir)
        for log_file in sorted(log_path.glob("*.log")):
            size = log_file.stat().st_size
            print(f"  {log_file.name}: {size} bytes")

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
        print("="*80)

        # Show sample log content
        print("\n" + "="*80)
        print("SAMPLE LOG CONTENT (from app log)")
        print("="*80)

        app_logs = list(log_path.glob("app_*.log"))
        if app_logs:
            with open(app_logs[0], 'r') as f:
                lines = f.readlines()
                # Show first 5 and last 5 lines
                print("\nFirst 5 log entries:")
                for line in lines[:5]:
                    print(f"  {line.strip()}")

                if len(lines) > 10:
                    print("\n  ... (more logs) ...\n")
                    print("Last 5 log entries:")
                    for line in lines[-5:]:
                        print(f"  {line.strip()}")

    finally:
        # Cleanup temporary directory
        print(f"\n\nCleaning up temporary log directory: {temp_log_dir}")
        shutil.rmtree(temp_log_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
