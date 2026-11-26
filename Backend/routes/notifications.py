"""
ImpactAI — Student Notifications & In-App Alerts.

Endpoints:
  GET   /notifications               → List user's notifications (newest first)
  PATCH /notifications/{id}/read      → Mark single notification as read
  POST  /notifications/mark-all-read  → Mark all unread notifications as read
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from database import NotificationRow, get_db
from routes.auth import _resolve_current_user
from schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _format_notification(n: NotificationRow) -> NotificationResponse:
    return NotificationResponse(
        id=n.id,
        user_id=n.user_id,
        title=n.title,
        message=n.message,
        type=n.type or "reminder",
        link=n.link,
        is_read=bool(n.is_read),
        created_at=n.created_at,
    )


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    limit: int = Query(20, ge=1, le=50),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    notifs = (
        db.query(NotificationRow)
        .filter(NotificationRow.user_id == user.id)
        .order_by(NotificationRow.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_format_notification(n) for n in notifs]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    n = db.query(NotificationRow).filter(NotificationRow.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if n.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    n.is_read = 1
    db.commit()
    db.refresh(n)
    return _format_notification(n)


@router.post("/mark-all-read")
def mark_all_notifications_read(
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    db.query(NotificationRow).filter(NotificationRow.user_id == user.id, NotificationRow.is_read == 0).update({"is_read": 1})
    db.commit()
    return {"success": True, "message": "All notifications marked as read."}
