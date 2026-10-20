import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from backend.app.database import Base

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    record_date = Column(Date, default=datetime.date.today, index=True)
    mood = Column(Integer, default=3)            # 1: Very Low, 2: Low, 3: Neutral, 4: Good, 5: Very Good
    sleep_hours = Column(Float, default=7.0)
    study_hours = Column(Float, default=3.0)
    energy_level = Column(Integer, default=3)    # 1: Very Low, 2: Low, 3: Moderate, 4: High, 5: Very High
    stress_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH
    stress_score = Column(Float, default=0.2)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WellnessRecommendation(Base):
    __tablename__ = "wellness_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    rec_type = Column(String(50), default="GENERAL") # GENERAL, DIET, MINDFULNESS, RELAXATION
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
