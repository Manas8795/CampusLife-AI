import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.schemas import (
    UserRegister, UserLogin, TokenResponse, UserOut,
    ProfileUpdate, ProfileOut, UserPreferenceUpdate, UserPreferenceOut,
    NotificationOut, NotificationCreate, DashboardSummary,
    QuickAddTask, QuickAddExpense, QuickAddMood
)
from backend.app.core.service import CoreService
from backend.app.study.service import StudyService
from backend.app.study.schemas import TaskCreate
from backend.app.health.service import HealthService
from backend.app.health.schemas import HealthLogCreate
from backend.app.expenses.service import ExpenseService
from backend.app.expenses.schemas import ExpenseCreate
from backend.app.travel.service import TravelService
from backend.app.intelligence.service import IntelligenceService

router = APIRouter()

# Simple dependency to retrieve user_id from Authorization header or default to 1 for easy testing
def get_current_user_id(authorization: str = Header(None)) -> int:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            # For this lightweight skeleton, token contains user_id: e.g. "token_user_1"
            if token.startswith("user_"):
                return int(token.replace("user_", ""))
            return int(token)
        except ValueError:
            pass
    return 1 # Default test user id

@router.post("/auth/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = CoreService.register_user(db, data)
        return TokenResponse(
            access_token=f"user_{user.id}",
            user_id=user.id,
            full_name=user.full_name,
            email=user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = CoreService.authenticate_user(db, data.email, data.password)
        return TokenResponse(
            access_token=f"user_{user.id}",
            user_id=user.id,
            full_name=user.full_name,
            email=user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/auth/me", response_model=UserOut)
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        return CoreService.get_user_by_id(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/users/me/profile", response_model=ProfileOut)
def get_my_profile(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/users/me/profile", response_model=ProfileOut)
def update_my_profile(data: ProfileUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return CoreService.update_profile(db, user_id, data)

@router.get("/users/profiles")
def list_student_profiles(db: Session = Depends(get_db)):
    """
    Returns all registered students with profile summaries for the multi-student switcher.
    """
    from backend.app.core.models import User
    users = db.query(User).all()
    results = []
    for u in users:
        p = u.profile
        results.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "major": p.major if p else "Computer Science",
            "year_of_study": p.year_of_study if p else 3,
            "sleep_target": p.sleep_target if p else 7.5,
            "weekly_budget_target": p.weekly_budget_target if p else 3000.0,
            "vocal_persona": p.vocal_persona if p else "EMPATHETIC_MENTOR"
        })
    return results

@router.post("/users/profiles/switch")
def switch_student_profile(target_user_id: int, db: Session = Depends(get_db)):
    """
    Switches active student session and returns bearer authentication credentials.
    """
    from backend.app.core.models import User
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return {
        "status": "success",
        "active_user_id": user.id,
        "full_name": user.full_name,
        "token": f"user_{user.id}",
        "auth_header": f"Bearer user_{user.id}"
    }

@router.get("/users/me/preferences", response_model=UserPreferenceOut)
def get_preferences(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return CoreService.get_preferences(db, user_id)

@router.patch("/users/me/preferences", response_model=UserPreferenceOut)
def update_preferences(data: UserPreferenceUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return CoreService.update_preferences(db, user_id, data)

@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return CoreService.get_notifications(db, user_id)

@router.patch("/notifications/{notif_id}/read")
def mark_read(notif_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    success = CoreService.mark_notification_read(db, user_id, notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "message": "Notification marked as read"}

@router.patch("/notifications/read-all")
def mark_all_read(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    count = CoreService.mark_all_notifications_read(db, user_id)
    return {"status": "success", "marked_read": count}

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        user = CoreService.get_user_by_id(db, user_id)
    except ValueError:
        user = None

    name = user.full_name if user else "Student"
    tasks = StudyService.get_tasks(db, user_id)
    pending_tasks = [t for t in tasks if t.status != "COMPLETED"]
    productivity = StudyService.calculate_productivity_risk(db, user_id)
    wellness = HealthService.get_wellness_summary(db, user_id)
    current_month = datetime.date.today().strftime("%Y-%m")
    expense_summary = ExpenseService.get_expense_summary(db, user_id, current_month)
    trips = TravelService.get_trips(db, user_id)
    intel = IntelligenceService.evaluate_student_state(db, user_id)
    notifs = CoreService.get_notifications(db, user_id, limit=5)

    return DashboardSummary(
        student_name=name,
        current_time=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        study={
            "pending_tasks_count": len(pending_tasks),
            "productivity_risk": productivity.risk_level,
            "completion_rate": productivity.completion_rate
        },
        health={
            "avg_sleep_7d": wellness.average_sleep_7d,
            "stress_level": wellness.current_stress_level,
            "sleep_status": wellness.sleep_status
        },
        expenses={
            "monthly_spending": expense_summary.total_spent,
            "budget_remaining": expense_summary.remaining,
            "utilization_percent": expense_summary.utilization_percent
        },
        travel={
            "upcoming_trips_count": len([t for t in trips if t.status in ["PLANNING", "CONFIRMED", "UPCOMING"]])
        },
        intelligence={
            "compound_risk_level": intel.compound_risk_level,
            "proactive_intervention_recommended": intel.proactive_intervention_recommended,
            "top_insight": intel.priority_insights[0].title if intel.priority_insights else "Everything is normal"
        },
        recent_notifications=[NotificationOut.from_orm(n) for n in notifs]
    )

# Quick Add endpoints
@router.post("/quick-add/task")
def quick_add_task(data: QuickAddTask, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    due = datetime.datetime.fromisoformat(data.due_date) if data.due_date else None
    task = StudyService.create_task(db, user_id, TaskCreate(
        title=data.title,
        priority=data.priority,
        due_date=due
    ))
    return {"status": "success", "task_id": task.id, "title": task.title}

@router.post("/quick-add/expense")
def quick_add_expense(data: QuickAddExpense, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    expense = ExpenseService.create_expense(db, user_id, ExpenseCreate(
        amount=data.amount,
        category=data.category,
        merchant=data.merchant or "Quick Expense"
    ))
    return {"status": "success", "expense_id": expense.id, "amount": expense.amount}

@router.post("/quick-add/mood")
def quick_add_mood(data: QuickAddMood, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    log = HealthService.log_wellness(db, user_id, HealthLogCreate(
        mood=data.mood,
        notes=data.note or "Quick mood log"
    ))
    return {"status": "success", "log_id": log.id, "mood": log.mood}
