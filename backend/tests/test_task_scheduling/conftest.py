"""
Pytest configuration for Task Scheduling module tests.

Provides fixtures and environment setup for task scheduling tests.
"""

import os
import pytest
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test")

# Set default environment variables if not already set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.getenv(
        "DATABASE_URL_TEST",
        "sqlite:///:memory:"
    )

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "9f5c8e2b7a1d4c6e3b9f5c8e2b7a1d4c6e3b9f5c8e2b7a1d4c6e3b9f5c8e2b"

if not os.getenv("LOG_LEVEL"):
    os.environ["LOG_LEVEL"] = "INFO"
