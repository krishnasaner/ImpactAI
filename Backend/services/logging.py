"""
ImpactAI — Audit & Security Structured Logging Service.

Ensures that all key authentication events, model predictions, crisis detections,
and database lifecycle logs are structured and recorded in both the file logs
and SQL database (for admin dashboard reporting), while preventing sensitive
data leaks (like passwords, keys, or cookies).
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from database import AuditLogRow, SecurityLogRow

# Setup basic audit and security loggers
logger_audit = logging.getLogger("impactai.audit")
logger_security = logging.getLogger("impactai.security")


def log_audit_event(
    db: Session,
    action: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log an event to standard logs and record in database audit logs.
    Actions: SIGNUP, LOGIN, FAILED_LOGIN, LOCKOUT, LOGOUT, PASSWORD_CHANGE, CRISIS_DETECTED, ROLE_CHANGE
    """
    safe_desc = description or ""
    # Filter out anything looking like password, credentials, secret, token, or cookie
    for sensitive_keyword in ["password", "token", "cookie", "secret", "gsk_", "jwt"]:
        if sensitive_keyword in safe_desc.lower():
            safe_desc = "[REDACTED SENSITIVE DATA]"

    logger_audit.info(
        "AUDIT: [%s] User %s, IP: %s, UA: %s | Description: %s",
        action,
        user_id or "Anonymous",
        ip_address or "N/A",
        user_agent or "N/A",
        safe_desc,
    )

    try:
        db_log = AuditLogRow(
            user_id=user_id,
            action=action,
            description=safe_desc,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(db_log)
        db.commit()
    except Exception as exc:
        logger_audit.error("Failed to write audit log to database: %s", exc)


def log_security_event(
    db: Session,
    event_type: str,
    severity: str = "medium",
    details: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log a security alert to standard logs and security logs database table.
    Event Types: JWT_REPLAY, CSRF_BLOCKED, EXPIRED_TOKEN, BRUTE_FORCE, PATH_TRAVERSAL, INJECTION_ATTEMPT
    """
    safe_details = details or ""
    # Sanitization filters
    for sensitive_keyword in ["password", "token", "cookie", "secret", "gsk_", "jwt"]:
        if sensitive_keyword in safe_details.lower():
            safe_details = "[REDACTED SENSITIVE DETAILS]"

    logger_security.warning(
        "SECURITY ALERT: [%s] [%s] User %s, IP: %s, UA: %s | Details: %s",
        severity.upper(),
        event_type,
        user_id or "Anonymous",
        ip_address or "N/A",
        user_agent or "N/A",
        safe_details,
    )

    try:
        db_log = SecurityLogRow(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            details=safe_details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(db_log)
        db.commit()
    except Exception as exc:
        logger_security.error("Failed to write security log to database: %s", exc)
