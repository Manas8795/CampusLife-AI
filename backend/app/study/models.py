import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    subject = Column(String(100), default="General")
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    status = Column(String(20), default="PENDING")    # PENDING, IN_PROGRESS, COMPLETED, OVERDUE
    due_date = Column(DateTime, nullable=True)
    source = Column(String(50), default="MANUAL")     # MANUAL, AI_STUDY_PLAN
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), default="General")
    content_summary = Column(Text, default="")
    file_path = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    subject = Column(String(100), nullable=False)
    exam_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    plan_data = Column(Text, default="{}")  # JSON structure containing day-wise breakdown
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ProductivityRecord(Base):
    __tablename__ = "productivity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    risk_score = Column(Float, default=0.0)         # 0.0 - 1.0
    reason_codes = Column(Text, default="[]")       # JSON list of reason codes
    explanation = Column(Text, default="")
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
