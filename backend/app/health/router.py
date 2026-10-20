from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.router import get_current_user_id
from backend.app.health.schemas import (
    HealthLogCreate, HealthLogOut, StressPredictionOut,
    WellnessSummaryOut, RecommendationRequest, RecommendationOut
)
from backend.app.health.service import HealthService

router = APIRouter(prefix="/health", tags=["Health & Wellness"])

@router.post("/logs", response_model=HealthLogOut)
def log_wellness(
    data: HealthLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.log_wellness(db, user_id, data)

@router.get("/logs", response_model=list[HealthLogOut])
def get_health_logs(
    limit: int = Query(14, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.get_logs(db, user_id, limit=limit)

@router.get("/summary", response_model=WellnessSummaryOut)
def get_wellness_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.get_wellness_summary(db, user_id)

@router.get("/stress/predict", response_model=StressPredictionOut)
@router.post("/stress/predict", response_model=StressPredictionOut)
def predict_stress(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.predict_stress(db, user_id)

@router.post("/recommendations", response_model=RecommendationOut)
def get_recommendation(
    req: RecommendationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.generate_recommendation(db, user_id, req.type)

@router.get("/dashboard")
def get_health_dashboard(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return HealthService.get_dashboard(db, user_id)

