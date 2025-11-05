"""
Security Audit Logging Module

Provides specialized logging for security and compliance events:
- Authentication events
- Authorization events
- Data access events
- Configuration changes
- Admin actions
- Security violations
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from .context import get_current_context, get_user_id, get_correlation_id
from .filters import sanitize_log_data


class AuditEventType(str, Enum):
    """Audit event types for security logging"""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    TOKEN_CREATED = "auth.token.created"
    TOKEN_REFRESHED = "auth.token.refreshed"
    TOKEN_REVOKED = "auth.token.revoked"
    PASSWORD_CHANGED = "auth.password.changed"
    PASSWORD_RESET_REQUEST = "auth.password.reset_requested"
    PASSWORD_RESET_COMPLETED = "auth.password.reset_completed"

    # Authorization events
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PERMISSION_CHANGED = "authz.permission.changed"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REVOKED = "authz.role.revoked"

    # Data access events
    DATA_READ = "data.read"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    DATA_IMPORTED = "data.imported"

    # Configuration events
    CONFIG_CHANGED = "config.changed"
    SETTINGS_UPDATED = "config.settings.updated"

    # Admin events
    USER_CREATED = "admin.user.created"
    USER_UPDATED = "admin.user.updated"
    USER_DELETED = "admin.user.deleted"
    USER_ACTIVATED = "admin.user.activated"
    USER_DEACTIVATED = "admin.user.deactivated"

    # Security events
    SECURITY_VIOLATION = "security.violation"
    RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    INVALID_INPUT = "security.invalid_input"
    SQL_INJECTION_ATTEMPT = "security.sql_injection.attempt"
    XSS_ATTEMPT = "security.xss.attempt"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    MIGRATION_STARTED = "system.migration.started"
    MIGRATION_COMPLETED = "system.migration.completed"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogger:
    """
    Specialized logger for audit events.

    Provides structured logging for security and compliance.
    """

    @staticmethod
    def log_event(
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.LOW,
        message: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of audit event
            severity: Event severity
            message: Human-readable message
            user_id: User who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            result: Result of action (success, failure, denied)
            details: Additional event details
            ip_address: IP address of the client

        Example:
            >>> AuditLogger.log_event(
            >>>     AuditEventType.LOGIN_SUCCESS,
            >>>     severity=AuditSeverity.LOW,
            >>>     user_id="user_123",
            >>>     ip_address="192.168.1.1",
            >>>     details={"method": "password"}
            >>> )
        """
        # Get context
        context = get_current_context().to_dict()

        # Use context user_id if not provided
        if user_id is None:
            user_id = get_user_id()

        # Build audit log entry
        audit_entry = {
            "audit": True,  # Flag for audit log routing
            "event_type": event_type.value,
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "correlation_id": get_correlation_id(),
            "result": result,
        }

        # Add resource information
        if resource_type:
            audit_entry["resource_type"] = resource_type
        if resource_id:
            audit_entry["resource_id"] = resource_id

        # Add action
        if action:
            audit_entry["action"] = action

        # Add IP address
        if ip_address:
            audit_entry["ip_address"] = ip_address

        # Add details
        if details:
            # Sanitize sensitive data in details
            audit_entry["details"] = sanitize_log_data(details)

        # Add context
        audit_entry.update(context)

        # Determine log level based on severity
        log_level_map = {
            AuditSeverity.LOW: "INFO",
            AuditSeverity.MEDIUM: "WARNING",
            AuditSeverity.HIGH: "ERROR",
            AuditSeverity.CRITICAL: "CRITICAL",
        }
        log_level = log_level_map.get(severity, "INFO")

        # Create message if not provided
        if message is None:
            message = f"Audit event: {event_type.value}"

        # Log the audit event
        logger.log(log_level, message, extra=audit_entry)

    @staticmethod
    def log_authentication(
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        reason: Optional[str] = None,
        **extra_details,
    ) -> None:
        """
        Log authentication events.

        Args:
            event_type: Authentication event type
            user_id: User ID
            username: Username
            ip_address: Client IP address
            success: Whether authentication succeeded
            reason: Failure reason if unsuccessful
            **extra_details: Additional details

        Example:
            >>> AuditLogger.log_authentication(
            >>>     AuditEventType.LOGIN_SUCCESS,
            >>>     user_id="user_123",
            >>>     username="john.doe",
            >>>     ip_address="192.168.1.1"
            >>> )
        """
        details = {
            "username": username,
            **extra_details,
        }

        if not success and reason:
            details["failure_reason"] = reason

        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM

        AuditLogger.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            resource_type="authentication",
            result="success" if success else "failure",
            details=details,
            ip_address=ip_address,
        )

    @staticmethod
    def log_authorization(
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        granted: bool = True,
        required_permission: Optional[str] = None,
        **extra_details,
    ) -> None:
        """
        Log authorization events.

        Args:
            event_type: Authorization event type
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action attempted
            granted: Whether access was granted
            required_permission: Permission that was required
            **extra_details: Additional details

        Example:
            >>> AuditLogger.log_authorization(
            >>>     AuditEventType.ACCESS_DENIED,
            >>>     user_id="user_123",
            >>>     resource_type="dataset",
            >>>     resource_id="dataset_456",
            >>>     action="delete",
            >>>     granted=False,
            >>>     required_permission="dataset:delete"
            >>> )
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        details.update(extra_details)

        severity = AuditSeverity.LOW if granted else AuditSeverity.MEDIUM

        AuditLogger.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="granted" if granted else "denied",
            details=details,
        )

    @staticmethod
    def log_data_access(
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        records_affected: Optional[int] = None,
        **extra_details,
    ) -> None:
        """
        Log data access events.

        Args:
            event_type: Data access event type
            user_id: User ID
            resource_type: Type of data
            resource_id: Data ID
            action: Action performed
            records_affected: Number of records affected
            **extra_details: Additional details

        Example:
            >>> AuditLogger.log_data_access(
            >>>     AuditEventType.DATA_DELETED,
            >>>     user_id="user_123",
            >>>     resource_type="dataset",
            >>>     resource_id="dataset_456",
            >>>     action="delete",
            >>>     records_affected=100
            >>> )
        """
        details = {}
        if records_affected is not None:
            details["records_affected"] = records_affected
        details.update(extra_details)

        # Deletion and export are higher severity
        severity = (
            AuditSeverity.MEDIUM
            if event_type in [AuditEventType.DATA_DELETED, AuditEventType.DATA_EXPORTED]
            else AuditSeverity.LOW
        )

        AuditLogger.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details,
        )

    @staticmethod
    def log_admin_action(
        event_type: AuditEventType,
        admin_user_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        action: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        **extra_details,
    ) -> None:
        """
        Log administrative actions.

        Args:
            event_type: Admin event type
            admin_user_id: Admin performing the action
            target_user_id: User being affected
            action: Action performed
            changes: Changes made (before/after)
            **extra_details: Additional details

        Example:
            >>> AuditLogger.log_admin_action(
            >>>     AuditEventType.USER_DEACTIVATED,
            >>>     admin_user_id="admin_123",
            >>>     target_user_id="user_456",
            >>>     action="deactivate",
            >>>     changes={"active": {"before": True, "after": False}}
            >>> )
        """
        details = {}
        if changes:
            details["changes"] = sanitize_log_data(changes)
        details.update(extra_details)

        AuditLogger.log_event(
            event_type=event_type,
            severity=AuditSeverity.MEDIUM,
            user_id=admin_user_id,
            resource_type="user",
            resource_id=target_user_id,
            action=action,
            details=details,
        )

    @staticmethod
    def log_security_violation(
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        violation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log security violations.

        Args:
            event_type: Security event type
            user_id: User ID (if known)
            ip_address: Client IP address
            violation_type: Type of violation
            details: Violation details

        Example:
            >>> AuditLogger.log_security_violation(
            >>>     AuditEventType.RATE_LIMIT_EXCEEDED,
            >>>     user_id="user_123",
            >>>     ip_address="192.168.1.1",
            >>>     violation_type="api_rate_limit",
            >>>     details={"limit": 100, "actual": 150}
            >>> )
        """
        log_details = {"violation_type": violation_type}
        if details:
            log_details.update(details)

        # Determine severity based on event type
        severity_map = {
            AuditEventType.RATE_LIMIT_EXCEEDED: AuditSeverity.MEDIUM,
            AuditEventType.SUSPICIOUS_ACTIVITY: AuditSeverity.HIGH,
            AuditEventType.SQL_INJECTION_ATTEMPT: AuditSeverity.CRITICAL,
            AuditEventType.XSS_ATTEMPT: AuditSeverity.CRITICAL,
        }
        severity = severity_map.get(event_type, AuditSeverity.HIGH)

        AuditLogger.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            resource_type="security",
            result="violation",
            details=log_details,
            ip_address=ip_address,
        )


def audit_decorator(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    get_resource_id: Optional[callable] = None,
):
    """
    Decorator to automatically log audit events for functions.

    Args:
        event_type: Type of audit event
        resource_type: Type of resource
        get_resource_id: Function to extract resource ID from args/kwargs

    Example:
        >>> @audit_decorator(
        >>>     AuditEventType.DATA_DELETED,
        >>>     resource_type="dataset",
        >>>     get_resource_id=lambda args, kwargs: kwargs.get("dataset_id")
        >>> )
        >>> async def delete_dataset(dataset_id: str):
        >>>     # Function implementation
        >>>     pass
    """

    def decorator(func):
        import functools
        import inspect

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get resource ID if extractor provided
            resource_id = None
            if get_resource_id:
                resource_id = get_resource_id(args, kwargs)

            # Execute function
            try:
                result = await func(*args, **kwargs)

                # Log successful audit event
                AuditLogger.log_event(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="success",
                )

                return result
            except Exception as e:
                # Log failed audit event
                AuditLogger.log_event(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="failure",
                    severity=AuditSeverity.MEDIUM,
                    details={"error": str(e)},
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            resource_id = None
            if get_resource_id:
                resource_id = get_resource_id(args, kwargs)

            try:
                result = func(*args, **kwargs)

                AuditLogger.log_event(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="success",
                )

                return result
            except Exception as e:
                AuditLogger.log_event(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="failure",
                    severity=AuditSeverity.MEDIUM,
                    details={"error": str(e)},
                )
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
