from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.router import get_current_user_id
from backend.app.travel.schemas import (
    TripCreate, TripUpdate, TripOut,
    ItineraryGenerateRequest, TripBudgetEstimateOut, TripConflictCheckOut
)
from backend.app.travel.service import TravelService

router = APIRouter(prefix="/travel", tags=["Travel & Trip Planner"])

@router.post("/trips", response_model=TripOut)
def create_trip(
    data: TripCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.create_trip(db, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trips", response_model=list[TripOut])
def get_trips(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return TravelService.get_trips(db, user_id)

@router.get("/trips/{trip_id}", response_model=TripOut)
def get_trip(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.get_trip(db, user_id, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/trips/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: int,
    data: TripUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.update_trip(db, user_id, trip_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/trips/{trip_id}")
def delete_trip(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        TravelService.delete_trip(db, user_id, trip_id)
        return {"status": "success", "message": f"Trip {trip_id} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/trips/{trip_id}/itinerary/generate", response_model=TripOut)
def generate_itinerary(
    trip_id: int,
    req: ItineraryGenerateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.generate_itinerary(db, user_id, trip_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/trips/{trip_id}/budget", response_model=TripBudgetEstimateOut)
def get_trip_budget(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.estimate_trip_budget(db, user_id, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/trips/{trip_id}/conflicts", response_model=TripConflictCheckOut)
def check_trip_conflicts(
    trip_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return TravelService.check_academic_conflicts(db, user_id, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
