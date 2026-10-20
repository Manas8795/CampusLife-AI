from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    subject: Optional[str] = "General"
    priority: Optional[str] = "MEDIUM"
    status: Optional[str] = "PENDING"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    source: str
    completed_at: Optional[datetime] = None
    created_at: datetime

class StudyMaterialCreate(BaseModel):
    title: str
    subject: Optional[str] = "General"
    content_summary: Optional[str] = ""
    file_path: Optional[str] = None

class StudyMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    subject: str
    content_summary: str
    uploaded_at: datetime

class StudyPlanGenerateRequest(BaseModel):
    subject: str
    exam_date: datetime
    available_hours_per_day: Optional[float] = 3.0
    topics: Optional[List[str]] = []
    auto_create_tasks: Optional[bool] = True

class StudyPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    subject: str
    exam_date: datetime
    start_date: datetime
    end_date: Optional[datetime] = None
    plan_data: str
    created_at: datetime

class ProductivityRiskOut(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_score: float
    total_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completed_tasks: int
    completion_rate: float
    reason_codes: List[str]
    explanation: str
