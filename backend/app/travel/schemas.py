from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class TripActivityCreate(BaseModel):
    day_number: int = 1
    name: str
    description: Optional[str] = ""
    start_time: Optional[str] = "10:00"
    end_time: Optional[str] = "12:00"
    estimated_cost: Optional[float] = 0.0
    category: Optional[str] = "Sightseeing"

class TripActivityOut(TripActivityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_id: int

class TripCreate(BaseModel):
    destination: str
    start_date: date
    end_date: date
    travelers: Optional[int] = 1
    budget: Optional[float] = 5000.0
    status: Optional[str] = "PLANNING"

class TripUpdate(BaseModel):
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    travelers: Optional[int] = None
    budget: Optional[float] = None
    status: Optional[str] = None

class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    destination: str
    start_date: date
    end_date: date
    travelers: int
    budget: float
    status: str
    itinerary_data: str
    created_at: datetime

class ItineraryGenerateRequest(BaseModel):
    preferred_pace: Optional[str] = "MODERATE" # RELAXED, MODERATE, INTENSIVE
    interests: Optional[List[str]] = ["Sightseeing", "Food & Cafes", "Nature"]

class TripBudgetEstimateOut(BaseModel):
    trip_id: int
    destination: str
    duration_days: int
    transportation: float
    accommodation: float
    food: float
    activities: float
    miscellaneous: float
    estimated_total: float
    user_budget: float
    budget_feasibility: str # WITHIN_BUDGET, BUDGET_DEFICIT
    difference: float

class ConflictItem(BaseModel):
    type: str # EXAM, ASSIGNMENT_DEADLINE, TASK_OVERDUE
    title: str
    date: str
    severity: str # HIGH, MEDIUM

class TripConflictCheckOut(BaseModel):
    has_conflict: bool
    conflict_count: int
    conflicts: List[ConflictItem]
    recommendation: str
