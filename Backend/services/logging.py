"""Audit and security logging helpers."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import AuditLogRow, SecurityLogRow

logger_audit = logging.getLogger("impactai.audit")
logger_security = logging.getLogger("impactai.security")
_SENSITIVE_KEYWORDS = ["password", "token", "cookie", "secret", "gsk_", "jwt"]


def _sanitize(value: Optional[str], fallback: str) -> str:
    sanitized = value or fallback
    lowered = sanitized.lower()
    if any(keyword in lowered for keyword in _SENSITIVE_KEYWORDS):
        return "[REDACTED SENSITIVE DATA]"
    return sanitized


def log_audit_event(
    db: Session,
    action: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    safe_desc = _sanitize(description, "")
    logger_audit.info(
        "AUDIT [%s] user=%s ip=%s ua=%s desc=%s",
        action,
        user_id or "Anonymous",
        ip_address or "N/A",
        user_agent or "N/A",
        safe_desc,
    )
    try:
        db.add(
            AuditLogRow(
                user_id=user_id,
                action=action,
                description=safe_desc,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.flush()
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
    safe_details = _sanitize(details, "")
    logger_security.warning(
        "SECURITY [%s] event=%s user=%s ip=%s ua=%s details=%s",
        severity.upper(),
        event_type,
        user_id or "Anonymous",
        ip_address or "N/A",
        user_agent or "N/A",
        safe_details,
    )
    try:
        db.add(
            SecurityLogRow(
                user_id=user_id,
                event_type=event_type,
                severity=severity,
                details=safe_details,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.flush()
    except Exception as exc:
        logger_security.error("Failed to write security log to database: %s", exc)
