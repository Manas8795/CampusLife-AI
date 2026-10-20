"""
Seed data script to populate CampusLife AI with a realistic student scenario:
- Student: Alex Sharma (alex@campuslife.ai)
- Approaching Operating Systems Exam in 3 days
- 5 pending/overdue high-priority tasks
- Sleep dropped from 7.5h baseline to 5.2h, high stress
- Monthly budget at 82% utilization
- Upcoming Goa trip conflicting with exam period
- Resulting in a Compound High Risk state ready for testing Module 7 & 8!
"""

import datetime
from backend.app.database import engine, Base, SessionLocal
from backend.app.core.models import User, Profile, UserPreference, Notification
from backend.app.core.service import hash_password
from backend.app.study.models import Task, StudyPlan
from backend.app.health.models import HealthRecord
from backend.app.expenses.models import Expense, Budget
from backend.app.travel.models import Trip
from backend.app.intelligence.service import IntelligenceService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        user = db.query(User).filter(User.email == "alex@campuslife.ai").first()
        if user:
            print("Database already contains seed user 'alex@campuslife.ai'. Clearing and reseeding...")
            # Clean up old records for a fresh state
            db.query(Notification).filter(Notification.user_id == user.id).delete()
            db.query(Task).filter(Task.user_id == user.id).delete()
            db.query(StudyPlan).filter(StudyPlan.user_id == user.id).delete()
            db.query(HealthRecord).filter(HealthRecord.user_id == user.id).delete()
            db.query(Expense).filter(Expense.user_id == user.id).delete()
            db.query(Budget).filter(Budget.user_id == user.id).delete()
            db.query(Trip).filter(Trip.user_id == user.id).delete()
            db.query(UserPreference).filter(UserPreference.user_id == user.id).delete()
            db.query(Profile).filter(Profile.user_id == user.id).delete()
            db.query(User).filter(User.id == user.id).delete()
            db.commit()

        # 1. Create User
        user = User(
            email="alex@campuslife.ai",
            hashed_password=hash_password("campuslife123"),
            full_name="Alex Sharma"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Profile & Preferences (Module 1)
        profile = Profile(
            user_id=user.id,
            college="National Institute of Technology",
            major="Computer Science & Engineering",
            graduation_year=2027,
            phone_number="+919876543210",
            bio="Pre-final year CS student preparing for semester finals."
        )
        prefs = UserPreference(
            user_id=user.id,
            notifications_enabled=True,
            voice_calls_enabled=True,
            calling_consent_status="OPTED_IN",
            quiet_hours_start="23:00",
            quiet_hours_end="07:30",
            preferred_call_time="EVENING",
            currency="INR"
        )
        db.add_all([profile, prefs])

        # 3. Tasks & Study Plan (Module 2)
        now = datetime.datetime.utcnow()
        exam_date = now + datetime.timedelta(days=3)
        study_plan = StudyPlan(
            user_id=user.id,
            subject="Operating Systems",
            exam_date=exam_date,
            start_date=now - datetime.timedelta(days=4),
            end_date=exam_date,
            plan_data='[{"day": 1, "topic": "Process Synchronization & Semaphores"}, {"day": 2, "topic": "Virtual Memory & Page Replacement"}]'
        )
        db.add(study_plan)

        tasks = [
            Task(
                user_id=user.id,
                title="OS Lab: Implement Dining Philosophers Problem",
                subject="Operating Systems",
                priority="HIGH",
                status="OVERDUE",
                due_date=now - datetime.timedelta(hours=12),
                source="AI_STUDY_PLAN"
            ),
            Task(
                user_id=user.id,
                title="Review Memory Management & Page Tables",
                subject="Operating Systems",
                priority="HIGH",
                status="PENDING",
                due_date=now + datetime.timedelta(days=1),
                source="AI_STUDY_PLAN"
            ),
            Task(
                user_id=user.id,
                title="Solve 2024 OS Past Exam Papers",
                subject="Operating Systems",
                priority="HIGH",
                status="PENDING",
                due_date=now + datetime.timedelta(days=2),
                source="MANUAL"
            ),
            Task(
                user_id=user.id,
                title="Submit Computer Networks Assignment 3",
                subject="Computer Networks",
                priority="MEDIUM",
                status="PENDING",
                due_date=now + datetime.timedelta(days=2, hours=4),
                source="MANUAL"
            ),
            Task(
                user_id=user.id,
                title="Submit Weekly Attendance Log",
                subject="General",
                priority="LOW",
                status="COMPLETED",
                due_date=now - datetime.timedelta(days=2),
                completed_at=now - datetime.timedelta(days=2),
                source="MANUAL"
            )
        ]
        db.add_all(tasks)

        # 4. Health Logs (Module 3)
        today = datetime.date.today()
        health_logs = [
            HealthRecord(
                user_id=user.id,
                record_date=today - datetime.timedelta(days=3),
                mood=4, sleep_hours=7.2, study_hours=4.0, energy_level=4, stress_level="LOW", stress_score=0.25
            ),
            HealthRecord(
                user_id=user.id,
                record_date=today - datetime.timedelta(days=2),
                mood=3, sleep_hours=6.1, study_hours=5.5, energy_level=3, stress_level="MEDIUM", stress_score=0.45
            ),
            HealthRecord(
                user_id=user.id,
                record_date=today - datetime.timedelta(days=1),
                mood=2, sleep_hours=5.3, study_hours=7.5, energy_level=2, stress_level="HIGH", stress_score=0.75,
                notes="Studied late night for OS exam, feeling fatigued."
            ),
            HealthRecord(
                user_id=user.id,
                record_date=today,
                mood=2, sleep_hours=5.1, study_hours=8.0, energy_level=2, stress_level="HIGH", stress_score=0.82,
                notes="High stress from pending lab assignment."
            )
        ]
        db.add_all(health_logs)

        # 5. Expenses & Budget (Module 4)
        current_month = today.strftime("%Y-%m")
        budget = Budget(
            user_id=user.id,
            month=current_month,
            total_budget=12000.0,
            current_balance=2200.0,
            currency="INR"
        )
        db.add(budget)

        expenses = [
            Expense(user_id=user.id, amount=4500.0, category="Food", merchant="Hostel Mess & Canteen", expense_date=today - datetime.timedelta(days=10)),
            Expense(user_id=user.id, amount=2200.0, category="Education", merchant="University Book Store", expense_date=today - datetime.timedelta(days=8)),
            Expense(user_id=user.id, amount=1600.0, category="Transport", merchant="Uber & Metro Pass", expense_date=today - datetime.timedelta(days=5)),
            Expense(user_id=user.id, amount=1500.0, category="Food", merchant="Campus Cafeteria & Late Night Snacks", expense_date=today - datetime.timedelta(days=1)),
        ]
        db.add_all(expenses)

        # 6. Travel Plans (Module 5)
        trip = Trip(
            user_id=user.id,
            destination="Goa Beach Retreat",
            start_date=today + datetime.timedelta(days=2),
            end_date=today + datetime.timedelta(days=5),
            travelers=2,
            budget=9000.0,
            status="PLANNING"
        )
        db.add(trip)
        db.commit()

        # 7. Evaluate Student Intelligence (Module 6)
        state = IntelligenceService.evaluate_student_state(db, user.id)

        print("Successfully seeded database with realistic test student:")
        print(f"- User: {user.full_name} ({user.email}), ID: {user.id}")
        print(f"- Tasks count: {len(tasks)}")
        print(f"- Health logs: {len(health_logs)}")
        print(f"- Budget: INR {budget.total_budget} (Balance: INR {budget.current_balance})")
        print(f"- Trip: {trip.destination} ({trip.start_date} to {trip.end_date})")
        print(f"- Compound Risk Level: {state.compound_risk_level} (Score: {state.compound_risk_score})")
        print(f"- Proactive Call Trigger: {state.proactive_intervention_recommended}")
        print(f"- Reason: {state.proactive_intervention_reason}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
