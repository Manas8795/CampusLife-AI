import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    destination = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    travelers: int = Column(Integer, default=1)
    budget = Column(Float, default=5000.0)
    status = Column(String(50), default="PLANNING") # PLANNING, CONFIRMED, UPCOMING, ONGOING, COMPLETED, CANCELLED
    itinerary_data = Column(Text, default="[]")     # JSON day-wise schedule
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    activities = relationship("TripActivity", back_populates="trip", cascade="all, delete-orphan")

class TripActivity(Base):
    __tablename__ = "trip_activities"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), index=True, nullable=False)
    day_number = Column(Integer, default=1)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    start_time = Column(String(10), default="10:00")
    end_time = Column(String(10), default="12:00")
    estimated_cost = Column(Float, default=0.0)
    category = Column(String(50), default="Sightseeing")

    trip = relationship("Trip", back_populates="activities")
