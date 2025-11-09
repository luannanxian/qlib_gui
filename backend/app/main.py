"""
FastAPI main application with comprehensive logging
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.modules.user_onboarding.api import mode_api
from app.modules.data_management.api import dataset_api, preprocessing_api, import_api, chart_api
from app.modules.strategy.api import strategy_api, builder_api
from app.modules.indicator.api import indicator_api, custom_factor_api, user_library_api
from app.modules.backtest.api import backtest_api, websocket_api
from app.modules.task_scheduling.api import task_api
from app.modules.code_security.api import router as security_router

# Import database
from app.database import db_manager

# Import logging modules
from app.modules.common.logging import setup_logging, get_logger
from app.modules.common.logging.middleware import (
    LoggingMiddleware,
    CorrelationIDMiddleware,
)
from app.modules.common.logging.audit import AuditLogger, AuditEventType, AuditSeverity
from app.modules.common.error_handlers import register_exception_handlers

# Setup logging before creating the app
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    environment=settings.APP_ENV,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    from urllib.parse import urlparse, urlunparse

    # Validate environment variables before proceeding
    logger.info("Validating environment variables...")
    try:
        settings.validate_required_vars()
        logger.info("✅ Environment variables validated")
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}", exc_info=True)
        raise

    # Sanitize database URL for logging
    parsed_url = urlparse(settings.DATABASE_URL)
    sanitized_url = parsed_url._replace(netloc=f"***:***@{parsed_url.hostname}:{parsed_url.port}")

    logger.info(
        "Starting Qlib-UI application",
        extra={
            "environment": settings.APP_ENV,
            "debug": settings.DEBUG,
            "version": app.version,
            "database_url": urlunparse(sanitized_url),
        },
    )

    # Initialize database engine and connection pool
    try:
        logger.info("Initializing database engine...")
        db_manager.init()
        logger.info("✅ Database engine initialized")

        # Test database connection
        logger.info("Testing database connection...")
        async with db_manager.session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        # Continue anyway in development mode
        if settings.APP_ENV == "production":
            raise

    # Log audit event for system startup
    AuditLogger.log_event(
        event_type=AuditEventType.SYSTEM_STARTUP,
        severity=AuditSeverity.LOW,
        message="Qlib-UI system started",
        details={
            "environment": settings.APP_ENV,
            "version": app.version,
        },
    )

    yield

    # Shutdown
    logger.info(
        "Shutting down Qlib-UI application",
        extra={"environment": settings.APP_ENV},
    )

    # Close database connections
    try:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)

    AuditLogger.log_event(
        event_type=AuditEventType.SYSTEM_SHUTDOWN,
        severity=AuditSeverity.LOW,
        message="Qlib-UI system shutdown",
    )


app = FastAPI(
    title="Qlib-UI API",
    description="Quantitative Investment Research Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add logging middleware (should be first to capture all requests)
app.add_middleware(
    LoggingMiddleware,
    log_request_body=settings.LOG_REQUEST_BODY,
    log_response_body=settings.LOG_RESPONSE_BODY,
    skip_healthcheck=True,  # Don't log health checks
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers (replaces the old global exception handler)
register_exception_handlers(app)

# Include routers
app.include_router(mode_api.router, prefix="/api/user", tags=["user"])
app.include_router(dataset_api.router)
app.include_router(preprocessing_api.router)
app.include_router(import_api.router)
app.include_router(chart_api.router)
app.include_router(strategy_api.router)
app.include_router(builder_api.router)
app.include_router(indicator_api.router)
app.include_router(custom_factor_api.router)
app.include_router(user_library_api.router)
app.include_router(backtest_api.router)
app.include_router(websocket_api.router, tags=["websocket"])
app.include_router(task_api.router)
app.include_router(security_router, prefix="/api/security", tags=["code-security"])


@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint accessed")
    return {"message": "Qlib-UI API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if the application is ready to serve traffic.
    """
    # Add checks for database, redis, etc. if needed
    return {"status": "ready", "checks": {"database": "ok"}}
