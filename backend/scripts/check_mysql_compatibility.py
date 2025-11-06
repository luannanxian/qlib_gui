"""
Model Compatibility Check for MySQL

This script verifies that all SQLAlchemy models are compatible with MySQL.
Run this before switching to MySQL testing to catch potential issues.
"""

import sys
from typing import List, Tuple

from sqlalchemy import inspect, Column
from sqlalchemy.sql import sqltypes

from app.database.base import Base
from app.database.models import (
    IndicatorComponent, CustomFactor, UserFactorLibrary, FactorValidationResult,
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask,
    StrategyTemplate, StrategyInstance, TemplateRating
)


def check_model_compatibility() -> List[Tuple[str, str, str]]:
    """
    Check all models for MySQL compatibility issues.

    Returns:
        List of (model_name, issue_type, issue_description) tuples
    """
    issues = []

    for mapper in Base.registry.mappers:
        model = mapper.class_
        model_name = model.__tablename__

        # Check table-level configurations
        if hasattr(model, "__table_args__"):
            table_args = model.__table_args__
            if isinstance(table_args, tuple) and len(table_args) > 0:
                if isinstance(table_args[-1], dict):
                    config = table_args[-1]
                    if "mysql_engine" not in config:
                        issues.append((
                            model_name,
                            "WARNING",
                            "Missing mysql_engine specification (recommend InnoDB)"
                        ))
                    if "mysql_charset" not in config:
                        issues.append((
                            model_name,
                            "WARNING",
                            "Missing mysql_charset specification (recommend utf8mb4)"
                        ))

        # Check column types
        for column in inspect(model).columns:
            column_name = column.name
            column_type = column.type

            # Check String columns without length
            if isinstance(column_type, sqltypes.String):
                if column_type.length is None:
                    issues.append((
                        f"{model_name}.{column_name}",
                        "ERROR",
                        "String column without length - MySQL requires explicit length"
                    ))

            # Check Text columns with length (not needed in MySQL)
            if isinstance(column_type, sqltypes.Text):
                if hasattr(column_type, 'length') and column_type.length is not None:
                    issues.append((
                        f"{model_name}.{column_name}",
                        "INFO",
                        f"Text column with explicit length {column_type.length} - MySQL uses LONGTEXT automatically"
                    ))

            # Check JSON server_default compatibility
            if isinstance(column_type, sqltypes.JSON):
                if hasattr(column, 'server_default') and column.server_default is not None:
                    default_val = str(column.server_default.arg)
                    if default_val in ("'[]'", "'{}'"):
                        # This is OK - MySQL 8.0+ supports JSON defaults
                        pass
                    else:
                        issues.append((
                            f"{model_name}.{column_name}",
                            "WARNING",
                            f"JSON column with server_default={default_val} - verify MySQL 8.0+ compatibility"
                        ))

            # Check Boolean server_default
            if isinstance(column_type, sqltypes.Boolean):
                if hasattr(column, 'server_default') and column.server_default is not None:
                    default_val = str(column.server_default.arg)
                    if default_val not in ("'0'", "'1'", "0", "1", "true", "false"):
                        issues.append((
                            f"{model_name}.{column_name}",
                            "WARNING",
                            f"Boolean column with non-standard server_default={default_val}"
                        ))

    return issues


def print_compatibility_report(issues: List[Tuple[str, str, str]]) -> None:
    """Print a formatted compatibility report."""
    print("=" * 80)
    print("MySQL Model Compatibility Check Report")
    print("=" * 80)
    print()

    if not issues:
        print("✅ All models are MySQL compatible!")
        print()
        return

    # Group issues by severity
    errors = [i for i in issues if i[1] == "ERROR"]
    warnings = [i for i in issues if i[1] == "WARNING"]
    infos = [i for i in issues if i[1] == "INFO"]

    if errors:
        print("❌ ERRORS (must fix before using MySQL):")
        print("-" * 80)
        for model, severity, description in errors:
            print(f"  • {model}")
            print(f"    {description}")
        print()

    if warnings:
        print("⚠️  WARNINGS (recommended to fix):")
        print("-" * 80)
        for model, severity, description in warnings:
            print(f"  • {model}")
            print(f"    {description}")
        print()

    if infos:
        print("ℹ️  INFORMATIONAL (optional improvements):")
        print("-" * 80)
        for model, severity, description in infos:
            print(f"  • {model}")
            print(f"    {description}")
        print()

    print("=" * 80)
    print(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} infos")
    print("=" * 80)


def main():
    """Run compatibility check and exit with appropriate status code."""
    try:
        issues = check_model_compatibility()
        print_compatibility_report(issues)

        # Exit with error code if there are any ERROR-level issues
        errors = [i for i in issues if i[1] == "ERROR"]
        if errors:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error during compatibility check: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
