from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# Auth
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    college: Optional[str] = None
    major: Optional[str] = None
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    email: str

# Profile
class ProfileBase(BaseModel):
    college: Optional[str] = ""
    major: Optional[str] = ""
    graduation_year: Optional[int] = None
    year_of_study: Optional[int] = 3
    sleep_target: Optional[float] = 7.5
    weekly_budget_target: Optional[float] = 3000.0
    vocal_persona: Optional[str] = "EMPATHETIC_MENTOR"
    morning_briefing_time: Optional[str] = "08:00"
    morning_briefing_enabled: Optional[bool] = True
    nightly_wind_down_time: Optional[str] = "22:30"
    nightly_wind_down_enabled: Optional[bool] = True
    phone_number: Optional[str] = ""
    timezone: Optional[str] = "Asia/Kolkata"
    bio: Optional[str] = ""

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

# Preferences
class UserPreferenceBase(BaseModel):
    notifications_enabled: bool = True
    voice_calls_enabled: bool = True
    calling_consent_status: str = "OPTED_IN"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    preferred_call_time: str = "EVENING"
    currency: str = "INR"

class UserPreferenceUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    voice_calls_enabled: Optional[bool] = None
    calling_consent_status: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    preferred_call_time: Optional[str] = None
    currency: Optional[str] = None

class UserPreferenceOut(UserPreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

# User Out
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    profile: Optional[ProfileOut] = None
    preferences: Optional[UserPreferenceOut] = None

# Notifications
class NotificationCreate(BaseModel):
    title: str
    message: str
    category: str = "SYSTEM"
    priority: str = "MEDIUM"

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    message: str
    category: str
    priority: str
    is_read: bool
    created_at: datetime

# Dashboard Response
class DashboardSummary(BaseModel):
    student_name: str
    current_time: str
    study: dict
    health: dict
    expenses: dict
    travel: dict
    intelligence: dict
    recent_notifications: List[NotificationOut]

# Quick Add
class QuickAddTask(BaseModel):
    title: str
    due_date: Optional[str] = None
    priority: str = "MEDIUM"

class QuickAddExpense(BaseModel):
    amount: float
    category: str = "Food"
    merchant: Optional[str] = "Quick Expense"

class QuickAddMood(BaseModel):
    mood: int  # 1 to 5
    note: Optional[str] = ""
