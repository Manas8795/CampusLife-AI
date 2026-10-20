import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from backend.app.database import Base

class StudentState(Base):
    __tablename__ = "student_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    academic_summary = Column(Text, default="{}")
    wellness_summary = Column(Text, default="{}")
    financial_summary = Column(Text, default="{}")
    travel_summary = Column(Text, default="{}")
    compound_risk_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    compound_risk_score = Column(Float, default=0.1)        # 0.0 to 1.0
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class IntelligenceRisk(Base):
    __tablename__ = "intelligence_risks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    risk_type = Column(String(100), nullable=False) # e.g. ACADEMIC_WELLNESS_OVERLOAD, TRAVEL_ACADEMIC_CONFLICT, BUDGET_DEFICIT
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, URGENT
    score = Column(Float, default=0.5)
    confidence = Column(Float, default=0.85)
    supporting_signals = Column(Text, default="[]") # JSON list of strings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IntelligenceInsight(Base):
    __tablename__ = "intelligence_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    insight_type = Column(String(50), default="CROSS_DOMAIN")
    severity = Column(String(20), default="MEDIUM")
    title = Column(String(255), nullable=False)
    evidence_signals = Column(Text, default="[]") # JSON list
    recommendation = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
