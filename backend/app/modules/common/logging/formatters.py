"""
Log Formatters Module

Provides custom formatters for structured logging:
- JsonFormatter: Machine-readable JSON format for production
- DevelopmentFormatter: Human-readable format for development
"""

import json
from datetime import datetime
from typing import Dict, Any
from loguru import logger


class JsonFormatter:
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format suitable for log aggregation tools
    like ELK, Splunk, DataDog, CloudWatch, etc.
    """

    @staticmethod
    def serialize(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize log record to dictionary for JSON output.

        Args:
            record: Loguru record dictionary

        Returns:
            Dictionary to be serialized as JSON
        """
        # Extract core fields
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
        }

        # Add file information
        if record.get("file"):
            log_entry["file"] = {
                "name": record["file"].name,
                "path": record["file"].path,
            }

        # Add process/thread information
        if record.get("process"):
            log_entry["process"] = {
                "id": record["process"].id,
                "name": record["process"].name,
            }

        if record.get("thread"):
            log_entry["thread"] = {
                "id": record["thread"].id,
                "name": record["thread"].name,
            }

        # Add exception information if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
            }

        # Add custom extra fields (correlation_id, user_id, etc.)
        if record.get("extra"):
            # Filter out internal loguru fields
            extra = {
                k: v
                for k, v in record["extra"].items()
                if k not in ["module"]  # Exclude internal fields
            }
            if extra:
                log_entry.update(extra)

        # Add elapsed time if available
        if record.get("elapsed"):
            log_entry["elapsed_ms"] = record["elapsed"].total_seconds() * 1000

        return log_entry

    @staticmethod
    def format(record: Dict[str, Any]) -> str:
        """
        Format log record as JSON string.

        Args:
            record: Loguru record dictionary

        Returns:
            JSON-formatted log string
        """
        return json.dumps(JsonFormatter.serialize(record), default=str) + "\n"


class DevelopmentFormatter:
    """
    Human-readable formatter for development environments.

    Provides colorized, easy-to-read log output with contextual information.
    """

    # ANSI color codes
    COLORS = {
        "TRACE": "\033[36m",  # Cyan
        "DEBUG": "\033[34m",  # Blue
        "INFO": "\033[32m",  # Green
        "SUCCESS": "\033[92m",  # Bright Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[91m",  # Bright Red
        "RESET": "\033[0m",  # Reset
    }

    @staticmethod
    def format(record: Dict[str, Any]) -> str:
        """
        Format log record for human readability.

        Args:
            record: Loguru record dictionary

        Returns:
            Formatted log string with colors and structure
        """
        # Base format
        timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record["level"].name
        module = record["name"]
        function = record["function"]
        line = record["line"]
        message = record["message"]

        # Build base log line
        log_line = (
            f"<green>{timestamp}</green> | "
            f"<level>{level:8}</level> | "
            f"<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            f"<level>{message}</level>"
        )

        # Add correlation ID if present
        if record["extra"].get("correlation_id"):
            log_line += f" | <yellow>correlation_id={record['extra']['correlation_id']}</yellow>"

        # Add user ID if present
        if record["extra"].get("user_id"):
            log_line += f" | <magenta>user_id={record['extra']['user_id']}</magenta>"

        # Add request ID if present
        if record["extra"].get("request_id"):
            log_line += f" | <blue>request_id={record['extra']['request_id']}</blue>"

        # Add execution time if present
        if record["extra"].get("execution_time_ms"):
            exec_time = record["extra"]["execution_time_ms"]
            log_line += f" | <yellow>⏱ {exec_time:.2f}ms</yellow>"

        # Add database query info if present
        if record["extra"].get("database"):
            if record["extra"].get("query_time_ms"):
                query_time = record["extra"]["query_time_ms"]
                log_line += f" | <yellow>DB: {query_time:.2f}ms</yellow>"

        # Add exception if present
        if record["exception"]:
            log_line += "\n<red>{exception}</red>"

        return log_line + "\n"


class CompactJsonFormatter:
    """
    Compact JSON formatter for high-throughput scenarios.

    Minimizes log size while maintaining essential information.
    """

    @staticmethod
    def format(record: Dict[str, Any]) -> str:
        """
        Format log record as compact JSON.

        Args:
            record: Loguru record dictionary

        Returns:
            Compact JSON-formatted log string
        """
        log_entry = {
            "ts": record["time"].isoformat(),
            "lvl": record["level"].name[0],  # First letter only
            "msg": record["message"],
            "mod": record["module"],
            "fn": record["function"],
            "ln": record["line"],
        }

        # Add correlation ID if present (most important for tracing)
        if record["extra"].get("correlation_id"):
            log_entry["cid"] = record["extra"]["correlation_id"]

        # Add user ID if present
        if record["extra"].get("user_id"):
            log_entry["uid"] = record["extra"]["user_id"]

        # Add exception type if present
        if record["exception"]:
            log_entry["exc"] = record["exception"].type.__name__

        return json.dumps(log_entry, separators=(",", ":")) + "\n"


class StructuredFormatter:
    """
    Advanced structured formatter with custom field mapping.

    Allows customization of field names and structure to match
    specific log aggregation platform requirements.
    """

    def __init__(self, field_mapping: Dict[str, str] = None):
        """
        Initialize formatter with custom field mapping.

        Args:
            field_mapping: Dictionary mapping standard fields to custom names
                Example: {"timestamp": "@timestamp", "level": "severity"}
        """
        self.field_mapping = field_mapping or {}

    def format(self, record: Dict[str, Any]) -> str:
        """
        Format log record with custom field mapping.

        Args:
            record: Loguru record dictionary

        Returns:
            JSON-formatted log string with custom fields
        """
        # Start with standard format
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "logger": record["name"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
        }

        # Apply custom field mapping
        if self.field_mapping:
            log_entry = {
                self.field_mapping.get(k, k): v for k, v in log_entry.items()
            }

        # Add extra fields
        if record.get("extra"):
            extra = {
                k: v
                for k, v in record["extra"].items()
                if k not in ["module"]
            }
            if extra:
                log_entry.update(extra)

        # Add exception if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "message": str(record["exception"].value),
            }

        return json.dumps(log_entry, default=str) + "\n"
