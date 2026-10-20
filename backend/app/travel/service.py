import json
import datetime
from sqlalchemy.orm import Session
from backend.app.travel.models import Trip, TripActivity
from backend.app.travel.schemas import (
    TripCreate, TripUpdate, ItineraryGenerateRequest,
    TripBudgetEstimateOut, TripConflictCheckOut, ConflictItem
)
from backend.app.study.models import Task, StudyPlan

class TravelService:
    @staticmethod
    def create_trip(db: Session, user_id: int, data: TripCreate) -> Trip:
        if data.end_date < data.start_date:
            raise ValueError("Trip end date cannot be earlier than start date")

        trip = Trip(
            user_id=user_id,
            destination=data.destination,
            start_date=data.start_date,
            end_date=data.end_date,
            travelers=data.travelers or 1,
            budget=data.budget or 5000.0,
            status=(data.status or "PLANNING").upper(),
            itinerary_data="[]"
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def get_trips(db: Session, user_id: int) -> list[Trip]:
        return db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_date.asc()).all()

    @staticmethod
    def get_trip(db: Session, user_id: int, trip_id: int) -> Trip:
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ValueError("Trip not found")
        return trip

    @staticmethod
    def update_trip(db: Session, user_id: int, trip_id: int, data: TripUpdate) -> Trip:
        trip = TravelService.get_trip(db, user_id, trip_id)
        for key, val in data.dict(exclude_unset=True).items():
            if val is not None:
                if key == "status":
                    val = val.upper()
                setattr(trip, key, val)
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def delete_trip(db: Session, user_id: int, trip_id: int) -> bool:
        trip = TravelService.get_trip(db, user_id, trip_id)
        db.delete(trip)
        db.commit()
        return True

    @staticmethod
    def generate_itinerary(db: Session, user_id: int, trip_id: int, req: ItineraryGenerateRequest) -> Trip:
        trip = TravelService.get_trip(db, user_id, trip_id)
        duration_days = max(1, (trip.end_date - trip.start_date).days + 1)

        itinerary = []
        interests = req.interests or ["Sightseeing", "Local Food", "Relaxation"]

        for day in range(1, duration_days + 1):
            current_date = trip.start_date + datetime.timedelta(days=day - 1)
            activities = [
                {
                    "time": "09:30 AM",
                    "title": f"{interests[0 % len(interests)]} Tour in {trip.destination}",
                    "estimated_cost": 300,
                    "category": "Sightseeing"
                },
                {
                    "time": "01:00 PM",
                    "title": f"Student-friendly lunch at {trip.destination} Popular Market",
                    "estimated_cost": 250,
                    "category": "Food"
                },
                {
                    "time": "04:30 PM",
                    "title": f"{interests[1 % len(interests)]} Exploration & Photography",
                    "estimated_cost": 200,
                    "category": "Recreation"
                },
                {
                    "time": "08:00 PM",
                    "title": "Evening leisure & dinner",
                    "estimated_cost": 350,
                    "category": "Food"
                }
            ]
            itinerary.append({
                "day_number": day,
                "date": current_date.strftime("%Y-%m-%d"),
                "activities": activities
            })

        trip.itinerary_data = json.dumps(itinerary)
        trip.status = "CONFIRMED"
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def estimate_trip_budget(db: Session, user_id: int, trip_id: int) -> TripBudgetEstimateOut:
        trip = TravelService.get_trip(db, user_id, trip_id)
        duration_days = max(1, (trip.end_date - trip.start_date).days + 1)
        travelers = max(1, trip.travelers)

        transportation = round(1500.0 * travelers, 2)
        accommodation = round(800.0 * duration_days * travelers, 2)
        food = round(600.0 * duration_days * travelers, 2)
        activities = round(400.0 * duration_days * travelers, 2)
        miscellaneous = round(300.0 * duration_days, 2)

        estimated_total = round(transportation + accommodation + food + activities + miscellaneous, 2)
        difference = round(trip.budget - estimated_total, 2)
        feasibility = "WITHIN_BUDGET" if difference >= 0 else "BUDGET_DEFICIT"

        return TripBudgetEstimateOut(
            trip_id=trip.id,
            destination=trip.destination,
            duration_days=duration_days,
            transportation=transportation,
            accommodation=accommodation,
            food=food,
            activities=activities,
            miscellaneous=miscellaneous,
            estimated_total=estimated_total,
            user_budget=trip.budget,
            budget_feasibility=feasibility,
            difference=difference
        )

    @staticmethod
    def check_academic_conflicts(db: Session, user_id: int, trip_id: int) -> TripConflictCheckOut:
        trip = TravelService.get_trip(db, user_id, trip_id)
        t_start = datetime.datetime.combine(trip.start_date, datetime.time.min)
        t_end = datetime.datetime.combine(trip.end_date, datetime.time.max)

        # Cross-check Study Plans (Exams)
        exams = db.query(StudyPlan).filter(
            StudyPlan.user_id == user_id,
            StudyPlan.exam_date >= t_start,
            StudyPlan.exam_date <= t_end
        ).all()

        # Cross-check Tasks with deadlines during trip
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status != "COMPLETED",
            Task.due_date >= t_start,
            Task.due_date <= t_end
        ).all()

        conflicts = []
        for e in exams:
            conflicts.append(ConflictItem(
                type="EXAM",
                title=f"Upcoming Exam: {e.subject}",
                date=e.exam_date.strftime("%Y-%m-%d"),
                severity="HIGH"
            ))

        for t in tasks:
            conflicts.append(ConflictItem(
                type="ASSIGNMENT_DEADLINE",
                title=f"Assignment Due: {t.title} ({t.subject})",
                date=t.due_date.strftime("%Y-%m-%d") if t.due_date else "During Trip",
                severity="HIGH" if t.priority == "HIGH" else "MEDIUM"
            ))

        has_conflict = len(conflicts) > 0
        if has_conflict:
            rec = f"Warning: {len(conflicts)} academic commitment(s) clash with your trip to {trip.destination}. Reschedule or finish assignments ahead of time."
        else:
            rec = f"Clear schedule! No exams or major deadlines conflict with your trip to {trip.destination}."

        return TripConflictCheckOut(
            has_conflict=has_conflict,
            conflict_count=len(conflicts),
            conflicts=conflicts,
            recommendation=rec
        )
