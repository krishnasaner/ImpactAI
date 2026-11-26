"""
ImpactAI — Personal Wellness Plans and Goal Tracking.

Endpoints:
  POST   /wellness/plans                  → Create a new personal wellness plan
  GET    /wellness/plans                  → List user's wellness plans
  GET    /wellness/plans/{id}             → Retrieve single plan with activities
  PUT    /wellness/plans/{id}             → Update plan status/meta
  DELETE /wellness/plans/{id}             → Delete wellness plan
  POST   /wellness/plans/{id}/activities  → Add activity to an existing plan
  PATCH  /wellness/activities/{id}/progress → Update activity completion/progress
  POST   /wellness/generate-plan          → Suggest structured wellness habit plan
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import (
    WellnessActivityRow,
    WellnessPlanRow,
    get_db,
)
from routes.auth import _resolve_current_user
from schemas import (
    WellnessActivityCreateRequest,
    WellnessActivityResponse,
    WellnessActivityUpdateRequest,
    WellnessPlanCreateRequest,
    WellnessPlanResponse,
    WellnessPlanUpdateRequest,
)
from services.rate_limit import rate_limiter

router = APIRouter(prefix="/wellness", tags=["wellness"])


class GeneratePlanRequest(BaseModel):
    category: str = Field("wellness", description="wellness, academic, social, personal")
    current_challenge: Optional[str] = None


def _format_activity(act: WellnessActivityRow) -> WellnessActivityResponse:
    return WellnessActivityResponse(
        id=act.id,
        plan_id=act.plan_id,
        title=act.title,
        description=act.description,
        frequency=act.frequency or "daily",
        progress=act.progress or 0,
        completed=bool(act.completed),
        completed_at=act.completed_at,
        created_at=act.created_at,
    )


def _format_plan(plan: WellnessPlanRow, db: Session) -> WellnessPlanResponse:
    activities = (
        db.query(WellnessActivityRow)
        .filter(WellnessActivityRow.plan_id == plan.id)
        .order_by(WellnessActivityRow.id.asc())
        .all()
    )
    return WellnessPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        title=plan.title,
        description=plan.description,
        category=plan.category or "wellness",
        status=plan.status or "active",
        target_date=plan.target_date,
        activities=[_format_activity(a) for a in activities],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post("/plans", response_model=WellnessPlanResponse, status_code=status.HTTP_201_CREATED)
def create_wellness_plan(
    request: WellnessPlanCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("wellness_create", f"user_{user.id}", 20, 60)

    plan = WellnessPlanRow(
        user_id=user.id,
        title=request.title.strip(),
        description=request.description.strip() if request.description else None,
        category=request.category or "wellness",
        status="active",
        target_date=request.target_date,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    db.flush()

    if request.activities:
        for act in request.activities:
            db_act = WellnessActivityRow(
                plan_id=plan.id,
                user_id=user.id,
                title=act.title.strip(),
                description=act.description.strip() if act.description else None,
                frequency=act.frequency or "daily",
                progress=0,
                completed=0,
                created_at=datetime.now(timezone.utc),
            )
            db.add(db_act)

    db.commit()
    db.refresh(plan)
    return _format_plan(plan, db)


@router.get("/plans", response_model=List[WellnessPlanResponse])
def list_wellness_plans(
    status_filter: Optional[str] = Query(None, alias="status"),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    query = db.query(WellnessPlanRow).filter(WellnessPlanRow.user_id == user.id)

    if status_filter:
        query = query.filter(WellnessPlanRow.status == status_filter)

    plans = query.order_by(WellnessPlanRow.created_at.desc()).all()
    return [_format_plan(p, db) for p in plans]


@router.get("/plans/{plan_id}", response_model=WellnessPlanResponse)
def get_wellness_plan(
    plan_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    plan = db.query(WellnessPlanRow).filter(WellnessPlanRow.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wellness plan not found.")

    if plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return _format_plan(plan, db)


@router.put("/plans/{plan_id}", response_model=WellnessPlanResponse)
def update_wellness_plan(
    plan_id: int,
    request: WellnessPlanUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    plan = db.query(WellnessPlanRow).filter(WellnessPlanRow.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wellness plan not found.")

    if plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if request.title is not None:
        plan.title = request.title.strip()
    if request.description is not None:
        plan.description = request.description.strip()
    if request.category is not None:
        plan.category = request.category
    if request.status is not None:
        plan.status = request.status
    if request.target_date is not None:
        plan.target_date = request.target_date

    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)

    return _format_plan(plan, db)


@router.delete("/plans/{plan_id}")
def delete_wellness_plan(
    plan_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    plan = db.query(WellnessPlanRow).filter(WellnessPlanRow.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wellness plan not found.")

    if plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.query(WellnessActivityRow).filter(WellnessActivityRow.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()

    return {"success": True, "message": "Wellness plan deleted successfully."}


@router.post("/plans/{plan_id}/activities", response_model=WellnessActivityResponse)
def add_plan_activity(
    plan_id: int,
    request: WellnessActivityCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    plan = db.query(WellnessPlanRow).filter(WellnessPlanRow.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wellness plan not found.")

    if plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    act = WellnessActivityRow(
        plan_id=plan.id,
        user_id=user.id,
        title=request.title.strip(),
        description=request.description.strip() if request.description else None,
        frequency=request.frequency or "daily",
        progress=0,
        completed=0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    return _format_activity(act)


@router.patch("/activities/{activity_id}/progress", response_model=WellnessActivityResponse)
def update_activity_progress(
    activity_id: int,
    request: WellnessActivityUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    act = db.query(WellnessActivityRow).filter(WellnessActivityRow.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found.")

    if act.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if request.title is not None:
        act.title = request.title.strip()
    if request.description is not None:
        act.description = request.description.strip()
    if request.progress is not None:
        act.progress = request.progress
        if act.progress >= 100:
            act.completed = 1
            act.completed_at = datetime.now(timezone.utc)
    if request.completed is not None:
        act.completed = 1 if request.completed else 0
        if request.completed:
            act.progress = 100
            act.completed_at = datetime.now(timezone.utc)
        else:
            act.completed_at = None

    db.commit()
    db.refresh(act)
    return _format_activity(act)


@router.post("/generate-plan", response_model=WellnessPlanCreateRequest)
def generate_wellness_plan(
    request: GeneratePlanRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Generate an evidence-informed, actionable student wellness plan proposal.
    Provides practical routines tailored to academic life.
    """
    _ = _resolve_current_user(http_request, db)
    cat = (request.category or "wellness").lower()

    plans_library = {
        "academic": {
            "title": "Study Calm & Focus Routine",
            "description": "Structured daily framework to reduce exam anxiety and avoid burnout.",
            "category": "academic",
            "activities": [
                {"title": "25-minute Pomodoro study sprint with zero notifications", "frequency": "daily"},
                {"title": "Write down top 3 achievable tasks for the day", "frequency": "daily"},
                {"title": "Review lecture notes with a 5-minute break in between", "frequency": "daily"},
                {"title": "Weekly academic retrospective without harsh self-criticism", "frequency": "weekly"},
            ],
        },
        "social": {
            "title": "Healthy Social Connection",
            "description": "Nurturing genuine friendships and setting healthy boundaries in college.",
            "category": "social",
            "activities": [
                {"title": "Reach out to one friend or classmate for a quick check-in", "frequency": "daily"},
                {"title": "Engage in one low-pressure campus activity or club meeting", "frequency": "weekly"},
                {"title": "Practice a gentle 'no' to commitments that drain your energy", "frequency": "weekly"},
            ],
        },
        "personal": {
            "title": "Sleep & Physical Grounding",
            "description": "Restoring consistent sleep hygiene and gentle body grounding.",
            "category": "personal",
            "activities": [
                {"title": "Screen-free winding down 30 minutes before bed", "frequency": "daily"},
                {"title": "15-minute gentle evening walk or light stretching", "frequency": "daily"},
                {"title": "Drink a glass of water upon waking up", "frequency": "daily"},
                {"title": "Keep bedroom cool and dark for sleep consistency", "frequency": "daily"},
            ],
        },
        "wellness": {
            "title": "Mindful Resilience & Stress Balance",
            "description": "Daily grounding habits to build emotional regulation and calm.",
            "category": "wellness",
            "activities": [
                {"title": "4-7-8 Breathing exercise for 3 minutes during study transitions", "frequency": "daily"},
                {"title": "Quick 1-minute daily mood check-in on ImpactAI", "frequency": "daily"},
                {"title": "Reflect on one small thing you appreciated today in your private journal", "frequency": "daily"},
                {"title": "Take a 20-minute digital-detox break outdoors", "frequency": "weekly"},
            ],
        },
    }

    selected = plans_library.get(cat, plans_library["wellness"])
    return WellnessPlanCreateRequest(
        title=selected["title"],
        description=selected["description"],
        category=selected["category"],
        activities=[WellnessActivityCreateRequest(**a) for a in selected["activities"]],
    )
