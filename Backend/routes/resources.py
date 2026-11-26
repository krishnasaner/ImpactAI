"""
ImpactAI — Structured Wellness Resource Library.

Endpoints:
  GET    /resources               → List, search and filter wellness resources
  GET    /resources/categories    → List resource categories with item counts
  GET    /resources/bookmarks     → List current student's bookmarked resources
  GET    /resources/{id}          → Get single resource details (+ increment view count)
  POST   /resources/{id}/bookmark → Toggle bookmark on/off for current user
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import ResourceBookmarkRow, ResourceRow, UserRow, get_db
from routes.auth import _get_client_info, _resolve_current_user
from schemas import ResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])

DEFAULT_RESOURCES = [
    {
        "title": "Grounding in 5 Minutes: The 5-4-3-2-1 Technique",
        "description": "A sensory awareness method to halt acute anxiety and bring your mind back to the present.",
        "category": "stress",
        "content_type": "exercise",
        "read_time": "3 min",
        "language": "en",
        "tags": ["anxiety", "grounding", "quick_relief"],
        "content_body": (
            "When anxiety spikes, look around your environment:\n"
            "5. Acknowledge FIVE things you can see.\n"
            "4. Acknowledge FOUR things you can touch.\n"
            "3. Acknowledge THREE things you can hear.\n"
            "2. Acknowledge TWO things you can smell.\n"
            "1. Acknowledge ONE thing you can taste.\n"
            "Take a slow breath. This exercise pulls focus from runaway mental loops back to physical reality."
        ),
    },
    {
        "title": "Understanding Academic Burnout vs. Normal Fatigue",
        "description": "How to recognize chronic emotional exhaustion in college and take realistic restorative pauses.",
        "category": "stress",
        "content_type": "article",
        "read_time": "6 min",
        "language": "en",
        "tags": ["burnout", "academics", "exhaustion"],
        "content_body": (
            "Burnout is not laziness. It is the consequence of prolonged demands exceeding restorative capacity. "
            "Signs include detachment from coursework, feeling that no effort makes a difference, and chronic sleep disruption. "
            "Restorative recovery starts with micro-boundaries: set an absolute stopping hour for study every night."
        ),
    },
    {
        "title": "Sleep Hygiene for Exam Weeks",
        "description": "Evidence-backed strategies to safeguard restorative REM sleep even with a demanding exam schedule.",
        "category": "sleep",
        "content_type": "article",
        "read_time": "4 min",
        "language": "en",
        "tags": ["sleep", "exams", "health"],
        "content_body": (
            "All-nighters dramatically impair executive function and memory recall. Research consistently demonstrates "
            "that six hours of sleep yields higher exam test scores than staying up an extra three hours to cram. "
            "Avoid caffeine 6 hours before bed, dim screens, and maintain a consistent wake-up time."
        ),
    },
    {
        "title": "4-7-8 Parasympathetic Relaxation Breath",
        "description": "Guided breathing pattern that physically stimulates the vagus nerve to slow racing heart rates.",
        "category": "mindfulness",
        "content_type": "exercise",
        "read_time": "5 min",
        "language": "en",
        "tags": ["breathing", "mindfulness", "heart_rate"],
        "content_body": (
            "1. Inhale quietly through your nose for a count of 4.\n"
            "2. Hold your breath gently for a count of 7.\n"
            "3. Exhale completely through your mouth with a soft whoosh for a count of 8.\n"
            "Repeat this cycle four times. The prolonged exhalation signals the autonomic nervous system to downshift."
        ),
    },
    {
        "title": "Navigating Social Comparison on Campus",
        "description": "How to handle feelings of falling behind when comparing yourself to peers and social media highlights.",
        "category": "mindfulness",
        "content_type": "article",
        "read_time": "5 min",
        "language": "en",
        "tags": ["social", "self-esteem", "perspective"],
        "content_body": (
            "Students constantly compare their messy internal realities to everyone else's curated external highlights. "
            "Remember that accomplishments shared publicly omit the struggles, doubts, and setbacks preceding them."
        ),
    },
]


def _seed_resources_if_empty(db: Session) -> None:
    count = db.query(ResourceRow).count()
    if count == 0:
        for r in DEFAULT_RESOURCES:
            row = ResourceRow(
                title=r["title"],
                description=r["description"],
                category=r["category"],
                content_type=r["content_type"],
                read_time=r["read_time"],
                language=r["language"],
                content_body=r["content_body"],
                tags=json.dumps(r["tags"]),
                is_published=1,
                view_count=12,
                created_at=datetime.now(timezone.utc),
            )
            db.add(row)
        db.commit()


def _format_resource(resource: ResourceRow, is_bookmarked: bool = False) -> ResourceResponse:
    parsed_tags = []
    if resource.tags:
        try:
            parsed_tags = json.loads(resource.tags)
            if not isinstance(parsed_tags, list):
                parsed_tags = []
        except Exception:
            parsed_tags = [resource.tags]

    return ResourceResponse(
        id=resource.id,
        title=resource.title,
        description=resource.description,
        category=resource.category,
        content_type=resource.content_type or "article",
        read_time=resource.read_time or "5 min",
        language=resource.language or "en",
        content_url=resource.content_url,
        content_body=resource.content_body,
        tags=parsed_tags,
        view_count=resource.view_count or 0,
        is_bookmarked=is_bookmarked,
        created_at=resource.created_at,
    )


@router.get("", response_model=List[ResourceResponse])
def list_resources(
    category: Optional[str] = None,
    content_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    _seed_resources_if_empty(db)

    # Optional user for bookmarks
    user: Optional[UserRow] = None
    if http_request:
        try:
            user = _resolve_current_user(http_request, db)
        except Exception:
            user = None

    bookmarked_ids = set()
    if user:
        bms = db.query(ResourceBookmarkRow.resource_id).filter(ResourceBookmarkRow.user_id == user.id).all()
        bookmarked_ids = {b[0] for b in bms}

    query = db.query(ResourceRow).filter(ResourceRow.is_published == 1)

    if category and category != "all":
        query = query.filter(ResourceRow.category == category)
    if content_type:
        query = query.filter(ResourceRow.content_type == content_type)
    if search:
        st = f"%{search.strip()}%"
        query = query.filter(or_(ResourceRow.title.like(st), ResourceRow.description.like(st)))

    records = query.order_by(ResourceRow.view_count.desc(), ResourceRow.created_at.desc()).offset(offset).limit(limit).all()
    return [_format_resource(r, r.id in bookmarked_ids) for r in records]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    _seed_resources_if_empty(db)
    counts = (
        db.query(ResourceRow.category, func.count(ResourceRow.id))
        .filter(ResourceRow.is_published == 1)
        .group_by(ResourceRow.category)
        .all()
    )
    return {"categories": [{"category": c[0], "count": c[1]} for c in counts]}


@router.get("/bookmarks", response_model=List[ResourceResponse])
def list_bookmarks(
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    bookmarked_rows = (
        db.query(ResourceRow)
        .join(ResourceBookmarkRow, ResourceBookmarkRow.resource_id == ResourceRow.id)
        .filter(ResourceBookmarkRow.user_id == user.id)
        .order_by(ResourceBookmarkRow.created_at.desc())
        .all()
    )
    return [_format_resource(r, True) for r in bookmarked_rows]


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    _seed_resources_if_empty(db)
    resource = db.query(ResourceRow).filter(ResourceRow.id == resource_id, ResourceRow.is_published == 1).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    resource.view_count = (resource.view_count or 0) + 1
    db.commit()

    is_bookmarked = False
    if http_request:
        try:
            user = _resolve_current_user(http_request, db)
            bm = db.query(ResourceBookmarkRow).filter(
                ResourceBookmarkRow.user_id == user.id,
                ResourceBookmarkRow.resource_id == resource_id,
            ).first()
            is_bookmarked = bm is not None
        except Exception:
            pass

    return _format_resource(resource, is_bookmarked)


@router.post("/{resource_id}/bookmark")
def toggle_bookmark(
    resource_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    resource = db.query(ResourceRow).filter(ResourceRow.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    bm = db.query(ResourceBookmarkRow).filter(
        ResourceBookmarkRow.user_id == user.id,
        ResourceBookmarkRow.resource_id == resource_id,
    ).first()

    if bm:
        db.delete(bm)
        db.commit()
        return {"bookmarked": False, "message": "Bookmark removed."}
    else:
        db.add(ResourceBookmarkRow(
            user_id=user.id,
            resource_id=resource_id,
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()
        return {"bookmarked": True, "message": "Resource bookmarked."}
