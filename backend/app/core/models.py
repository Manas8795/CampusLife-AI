import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    college = Column(String(255), default="")
    major = Column(String(255), default="")
    graduation_year = Column(Integer, nullable=True)
    year_of_study = Column(Integer, default=3)
    sleep_target = Column(Float, default=7.5)
    weekly_budget_target = Column(Float, default=3000.0)
    vocal_persona = Column(String(50), default="EMPATHETIC_MENTOR")  # EMPATHETIC_MENTOR, PRODUCTIVITY_COACH, CAMPUS_PEER
    morning_briefing_time = Column(String(10), default="08:00")
    morning_briefing_enabled = Column(Boolean, default=True)
    nightly_wind_down_time = Column(String(10), default="22:30")
    nightly_wind_down_enabled = Column(Boolean, default=True)
    phone_number = Column(String(50), default="")
    timezone = Column(String(50), default="Asia/Kolkata")
    bio = Column(Text, default="")

    user = relationship("User", back_populates="profile")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notifications_enabled = Column(Boolean, default=True)
    voice_calls_enabled = Column(Boolean, default=True)
    calling_consent_status = Column(String(50), default="OPTED_IN")  # OPTED_IN, OPTED_OUT
    quiet_hours_start = Column(String(10), default="22:00")
    quiet_hours_end = Column(String(10), default="08:00")
    preferred_call_time = Column(String(50), default="EVENING")
    currency = Column(String(10), default="INR")

    user = relationship("User", back_populates="preferences")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="SYSTEM")  # STUDY, HEALTH, EXPENSE, TRAVEL, INTELLIGENCE, SYSTEM
    priority = Column(String(20), default="MEDIUM")   # LOW, MEDIUM, HIGH, URGENT
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")
