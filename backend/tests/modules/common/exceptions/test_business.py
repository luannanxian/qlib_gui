"""Tests for business exception classes.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest


class TestDataImportException:
    """Test DataImportException."""

    def test_data_import_exception_creation(self):
        """Test DataImportException creation."""
        from app.modules.common.exceptions.business import DataImportException

        exc = DataImportException("Failed to import CSV")
        assert exc.message == "Failed to import CSV"
        assert exc.code == "DATA_IMPORT_FAILED"

    def test_data_import_exception_with_custom_code(self):
        """Test DataImportException with custom error code."""
        from app.modules.common.exceptions.business import DataImportException

        exc = DataImportException("Import error", code="CSV_PARSE_ERROR")
        assert exc.code == "CSV_PARSE_ERROR"

    def test_data_import_exception_with_details(self):
        """Test DataImportException with details."""
        from app.modules.common.exceptions.business import DataImportException

        details = {"file": "data.csv", "line": 42}
        exc = DataImportException("Parse error", details=details)
        assert exc.details == details

    def test_data_import_exception_inherits_from_qlib_ui_exception(self):
        """Test DataImportException inheritance."""
        from app.modules.common.exceptions.business import DataImportException
        from app.modules.common.exceptions.base import QlibUIException

        exc = DataImportException("Test")
        assert isinstance(exc, QlibUIException)


class TestBacktestException:
    """Test BacktestException."""

    def test_backtest_exception_creation(self):
        """Test BacktestException creation."""
        from app.modules.common.exceptions.business import BacktestException

        exc = BacktestException("Backtest failed")
        assert exc.message == "Backtest failed"
        assert exc.code == "BACKTEST_FAILED"

    def test_backtest_exception_with_custom_code(self):
        """Test BacktestException with custom code."""
        from app.modules.common.exceptions.business import BacktestException

        exc = BacktestException("Timeout", code="BACKTEST_TIMEOUT")
        assert exc.code == "BACKTEST_TIMEOUT"

    def test_backtest_exception_with_details(self):
        """Test BacktestException with details."""
        from app.modules.common.exceptions.business import BacktestException

        details = {"strategy_id": "123", "reason": "insufficient data"}
        exc = BacktestException("Failed", details=details)
        assert exc.details == details

    def test_backtest_exception_inherits_from_qlib_ui_exception(self):
        """Test BacktestException inheritance."""
        from app.modules.common.exceptions.business import BacktestException
        from app.modules.common.exceptions.base import QlibUIException

        exc = BacktestException("Test")
        assert isinstance(exc, QlibUIException)


class TestCodeExecutionException:
    """Test CodeExecutionException."""

    def test_code_execution_exception_creation(self):
        """Test CodeExecutionException creation."""
        from app.modules.common.exceptions.business import CodeExecutionException

        exc = CodeExecutionException("Code execution failed")
        assert exc.message == "Code execution failed"
        assert exc.code == "CODE_EXECUTION_FAILED"

    def test_code_execution_exception_with_custom_code(self):
        """Test CodeExecutionException with custom code."""
        from app.modules.common.exceptions.business import CodeExecutionException

        exc = CodeExecutionException("Security violation", code="CODE_SECURITY_VIOLATION")
        assert exc.code == "CODE_SECURITY_VIOLATION"

    def test_code_execution_exception_with_details(self):
        """Test CodeExecutionException with details."""
        from app.modules.common.exceptions.business import CodeExecutionException

        details = {"line": 10, "error": "NameError"}
        exc = CodeExecutionException("Runtime error", details=details)
        assert exc.details == details

    def test_code_execution_exception_inherits_from_qlib_ui_exception(self):
        """Test CodeExecutionException inheritance."""
        from app.modules.common.exceptions.business import CodeExecutionException
        from app.modules.common.exceptions.base import QlibUIException

        exc = CodeExecutionException("Test")
        assert isinstance(exc, QlibUIException)


class TestStrategyException:
    """Test StrategyException."""

    def test_strategy_exception_creation(self):
        """Test StrategyException creation."""
        from app.modules.common.exceptions.business import StrategyException

        exc = StrategyException("Strategy validation failed")
        assert exc.message == "Strategy validation failed"
        assert exc.code == "STRATEGY_ERROR"

    def test_strategy_exception_with_custom_code(self):
        """Test StrategyException with custom code."""
        from app.modules.common.exceptions.business import StrategyException

        exc = StrategyException("Not found", code="STRATEGY_NOT_FOUND")
        assert exc.code == "STRATEGY_NOT_FOUND"

    def test_strategy_exception_inherits_from_qlib_ui_exception(self):
        """Test StrategyException inheritance."""
        from app.modules.common.exceptions.business import StrategyException
        from app.modules.common.exceptions.base import QlibUIException

        exc = StrategyException("Test")
        assert isinstance(exc, QlibUIException)
