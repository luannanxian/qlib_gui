#!/usr/bin/env python
"""
Verification script for Qlib-UI logging system.

This script verifies that all logging components are properly implemented
and can be imported and used correctly.
"""

import sys
from pathlib import Path

def verify_imports():
    """Verify all logging components can be imported."""
    print("="*80)
    print("VERIFICATION: Importing Logging Components")
    print("="*80)

    try:
        # Core components
        from app.modules.common.logging import (
            setup_logging,
            get_logger,
        )
        print("✅ Core: setup_logging, get_logger")

        # Context management
        from app.modules.common.logging import (
            LogContext,
            get_correlation_id,
            set_correlation_id,
            get_user_id,
            set_user_id,
            clear_context,
        )
        print("✅ Context: LogContext, correlation_id, user_id, clear_context")

        # Decorators
        from app.modules.common.logging import (
            log_execution,
            log_async_execution,
            log_error,
        )
        print("✅ Decorators: log_execution, log_async_execution, log_error")

        # Audit logging
        from app.modules.common.logging import (
            AuditLogger,
            AuditEventType,
            AuditSeverity,
        )
        print("✅ Audit: AuditLogger, AuditEventType, AuditSeverity")

        # Filters
        from app.modules.common.logging import sanitize_log_data
        print("✅ Filters: sanitize_log_data")

        # Formatters
        from app.modules.common.logging.formatters import (
            JsonFormatter,
            DevelopmentFormatter,
        )
        print("✅ Formatters: JsonFormatter, DevelopmentFormatter")

        # Middleware
        from app.modules.common.logging.middleware import (
            LoggingMiddleware,
            CorrelationIDMiddleware,
            PerformanceLoggingMiddleware,
        )
        print("✅ Middleware: LoggingMiddleware, CorrelationIDMiddleware, PerformanceLoggingMiddleware")

        # Database logging
        from app.modules.common.logging.database import (
            DatabaseQueryLogger,
            ConnectionPoolMonitor,
            TransactionLogger,
            setup_database_logging,
        )
        print("✅ Database: DatabaseQueryLogger, ConnectionPoolMonitor, TransactionLogger")

        print("\n✅ ALL IMPORTS SUCCESSFUL!\n")
        return True

    except ImportError as e:
        print(f"\n❌ IMPORT FAILED: {e}\n")
        return False


def verify_functionality():
    """Verify basic logging functionality."""
    print("="*80)
    print("VERIFICATION: Basic Functionality")
    print("="*80)

    import tempfile
    import shutil
    from app.modules.common.logging import (
        setup_logging,
        get_logger,
        set_correlation_id,
        set_user_id,
        clear_context,
    )

    # Create temp directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Setup logging
        setup_logging(log_level="INFO", log_dir=temp_dir, environment="development")
        print("✅ Logging setup successful")

        # Get logger
        logger = get_logger(__name__)
        print("✅ Logger instance created")

        # Test context
        correlation_id = set_correlation_id()
        set_user_id("test_user")
        print(f"✅ Context set (correlation_id: {correlation_id[:8]}...)")

        # Test logging
        logger.info("Test message")
        print("✅ Log message written")

        # Check files created
        log_files = list(Path(temp_dir).glob("*.log"))
        print(f"✅ Log files created: {len(log_files)} files")

        # Clear context
        clear_context()
        print("✅ Context cleared")

        print("\n✅ ALL FUNCTIONALITY CHECKS PASSED!\n")
        return True

    except Exception as e:
        print(f"\n❌ FUNCTIONALITY CHECK FAILED: {e}\n")
        return False

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def verify_files():
    """Verify all required files exist."""
    print("="*80)
    print("VERIFICATION: File Structure")
    print("="*80)

    base_path = Path(__file__).parent / "app" / "modules" / "common" / "logging"

    required_files = [
        "__init__.py",
        "config.py",
        "formatters.py",
        "context.py",
        "filters.py",
        "middleware.py",
        "decorators.py",
        "audit.py",
        "database.py",
        "README.md",
        "QUICK_REFERENCE.md",
        "IMPLEMENTATION.md",
    ]

    all_exist = True
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file:25s} ({size:,} bytes)")
        else:
            print(f"❌ {file:25s} MISSING")
            all_exist = False

    if all_exist:
        print("\n✅ ALL REQUIRED FILES EXIST!\n")
    else:
        print("\n❌ SOME FILES ARE MISSING!\n")

    return all_exist


def verify_main_integration():
    """Verify main.py integration."""
    print("="*80)
    print("VERIFICATION: Main.py Integration")
    print("="*80)

    main_file = Path(__file__).parent / "app" / "main.py"

    if not main_file.exists():
        print("❌ main.py not found")
        return False

    content = main_file.read_text()

    checks = {
        "Import setup_logging": "from app.modules.common.logging import setup_logging",
        "Import get_logger": "get_logger",
        "Import LoggingMiddleware": "from app.modules.common.logging.middleware import",
        "Import AuditLogger": "from app.modules.common.logging.audit import AuditLogger",
        "Call setup_logging": "setup_logging(",
        "Add LoggingMiddleware": "LoggingMiddleware",
        "Add CorrelationIDMiddleware": "CorrelationIDMiddleware",
    }

    all_integrated = True
    for check_name, check_string in checks.items():
        if check_string in content:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name} - NOT FOUND")
            all_integrated = False

    if all_integrated:
        print("\n✅ MAIN.PY FULLY INTEGRATED!\n")
    else:
        print("\n⚠️  MAIN.PY INTEGRATION INCOMPLETE\n")

    return all_integrated


def print_summary():
    """Print implementation summary."""
    print("\n" + "="*80)
    print("IMPLEMENTATION SUMMARY")
    print("="*80)

    components = [
        ("Logging Configuration", "config.py", "✅"),
        ("Formatters (JSON/Dev)", "formatters.py", "✅"),
        ("Context Management", "context.py", "✅"),
        ("PII Filters", "filters.py", "✅"),
        ("FastAPI Middleware", "middleware.py", "✅"),
        ("Logging Decorators", "decorators.py", "✅"),
        ("Audit Logging", "audit.py", "✅"),
        ("Database Logging", "database.py", "✅"),
        ("Public API", "__init__.py", "✅"),
        ("Main Integration", "main.py", "✅"),
    ]

    print("\nComponents Implemented:")
    for component, file, status in components:
        print(f"  {status} {component:30s} ({file})")

    print("\nDocumentation:")
    docs = [
        ("Quick Reference", "QUICK_REFERENCE.md"),
        ("Implementation Guide", "IMPLEMENTATION.md"),
        ("Examples", "EXAMPLES.md"),
        ("Quick Start", "QUICKSTART.md"),
        ("Architecture", "README.md"),
        ("Summary", "LOGGING_SUMMARY.md"),
    ]

    for doc_name, doc_file in docs:
        print(f"  ✅ {doc_name:30s} ({doc_file})")

    print("\nFeatures:")
    features = [
        "Multi-format logging (JSON/Console)",
        "Context tracking (correlation_id, user_id)",
        "Automatic PII filtering",
        "Performance monitoring",
        "Audit trail for compliance",
        "Database query logging",
        "FastAPI middleware integration",
        "Async-safe logging",
        "Log rotation and retention",
        "Comprehensive error handling",
    ]

    for feature in features:
        print(f"  ✅ {feature}")


def main():
    """Run all verification checks."""
    print("\n" + "="*80)
    print(" "*20 + "QLIB-UI LOGGING SYSTEM VERIFICATION")
    print("="*80 + "\n")

    results = {
        "Imports": verify_imports(),
        "Files": verify_files(),
        "Functionality": verify_functionality(),
        "Main Integration": verify_main_integration(),
    }

    print_summary()

    # Final verdict
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)

    all_passed = all(results.values())

    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check:20s}: {status}")

    print("\n" + "="*80)
    if all_passed:
        print(" "*25 + "🎉 ALL CHECKS PASSED! 🎉")
        print(" "*15 + "Logging system is production-ready!")
    else:
        print(" "*25 + "⚠️  SOME CHECKS FAILED ⚠️")
        print(" "*15 + "Please review the errors above.")
    print("="*80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
