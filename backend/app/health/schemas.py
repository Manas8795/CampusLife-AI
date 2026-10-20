from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class HealthLogCreate(BaseModel):
    record_date: Optional[date] = None
    mood: int = Field(default=3, ge=1, le=5)           # 1 (Very Low) to 5 (Very Good)
    sleep_hours: float = Field(default=7.0, ge=0, le=24)
    study_hours: float = Field(default=3.0, ge=0, le=24)
    energy_level: int = Field(default=3, ge=1, le=5)  # 1 (Very Low) to 5 (Very High)
    notes: Optional[str] = ""

class HealthLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    record_date: date
    mood: int
    sleep_hours: float
    study_hours: float
    energy_level: int
    stress_level: str
    stress_score: float
    notes: str
    created_at: datetime

class StressPredictionOut(BaseModel):
    stress_level: str  # LOW, MEDIUM, HIGH
    confidence: float
    signals: List[str]
    sleep_hours: float
    sleep_baseline_deviation: float
    recommendation: str

class WellnessSummaryOut(BaseModel):
    average_sleep_7d: float
    average_study_7d: float
    average_mood_7d: float
    average_energy_7d: float
    current_stress_level: str
    sleep_baseline: float
    sleep_status: str
    logs_count: int

class RecommendationRequest(BaseModel):
    type: Optional[str] = "GENERAL"  # GENERAL, DIET, MINDFULNESS

class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    rec_type: str
    title: str
    content: str
    created_at: datetime
