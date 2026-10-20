"""
Unified tool interfaces for CampusLife AI.
These functions serve as the direct tool/function execution layer for:
- Module 7: AI Voice Assistant & Calling System (in-app voice agent, proactive call triggers)
- Module 8: AI/ML Infrastructure & LLM function calling
"""

import re
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.study.service import StudyService
from backend.app.study.schemas import TaskCreate
from backend.app.health.service import HealthService
from backend.app.expenses.service import ExpenseService
from backend.app.travel.service import TravelService
from backend.app.intelligence.service import IntelligenceService
from backend.app.core.service import CoreService

def get_tasks(user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve the student's tasks, optionally filtered by status (PENDING, COMPLETED, etc.)."""
    with SessionLocal() as db:
        tasks = StudyService.get_tasks(db, user_id, status)
        return [
            {
                "id": t.id,
                "title": t.title,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else None,
                "source": t.source
            }
            for t in tasks
        ]

def parse_flexible_due_date(due_str: Optional[Any]) -> Optional[datetime.datetime]:
    if not due_str:
        return None
    if isinstance(due_str, datetime.datetime):
        return due_str
    import re
    now = datetime.datetime.now()
    s = str(due_str).strip().lower()
    if s in ("today", "tonight"):
        return now.replace(hour=23, minute=59, second=0, microsecond=0)
    elif s in ("tomorrow", "tmrw"):
        t = now + datetime.timedelta(days=1)
        return t.replace(hour=23, minute=59, second=0, microsecond=0)
    elif "day" in s:
        m = re.search(r"(\d+)\s*days?", s)
        days = int(m.group(1)) if m else 1
        t = now + datetime.timedelta(days=days)
        return t.replace(hour=23, minute=59, second=0, microsecond=0)
    elif "hour" in s:
        m = re.search(r"(\d+)\s*hours?", s)
        hrs = int(m.group(1)) if m else 2
        return now + datetime.timedelta(hours=hrs)
    elif "minute" in s or "min" in s:
        m = re.search(r"(\d+)\s*(?:minutes?|mins?)", s)
        mins = int(m.group(1)) if m else 30
        return now + datetime.timedelta(minutes=mins)
    elif "week" in s:
        m = re.search(r"(\d+)\s*weeks?", s)
        wks = int(m.group(1)) if m else 1
        t = now + datetime.timedelta(weeks=wks)
        return t.replace(hour=23, minute=59, second=0, microsecond=0)

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(str(due_str).strip()[:19], fmt)
        except ValueError:
            pass
    return now + datetime.timedelta(days=1)

def create_task(
    user_id: int,
    title: str,
    priority: str = "MEDIUM",
    subject: str = "General",
    description: str = "",
    due_date: Optional[Any] = None
) -> Dict[str, Any]:
    """Create a new academic task for the student via voice or assistant interaction, directly in database."""
    parsed_due = parse_flexible_due_date(due_date)
    with SessionLocal() as db:
        task = StudyService.create_task(db, user_id, TaskCreate(
            title=title,
            priority=priority,
            subject=subject,
            description=description,
            due_date=parsed_due
        ))
        due_text = task.due_date.strftime("%Y-%m-%d %I:%M %p") if task.due_date else "No deadline"
        return {
            "status": "success",
            "action": "create_task",
            "task_id": task.id,
            "title": task.title,
            "subject": task.subject,
            "priority": task.priority,
            "due_date": due_text,
            "message": f"Task #{task.id} '{task.title}' has been directly logged into your database (Due: {due_text})."
        }

EXPENSE_TAXONOMY = {
    "Academic": [
        "electrical", "electronic", "electronics", "component", "components", "circuit", "circuits",
        "arduino", "raspberry", "sensor", "sensors", "breadboard", "resistor", "resistors",
        "capacitor", "capacitors", "multimeter", "hardware", "microcontroller", "soldering",
        "robotics", "iot", "wire", "wires", "diode", "diodes", "pcb", "ic", "motor", "motors",
        "servo", "servos", "project kit", "lab kit", "textbook", "textbooks", "book", "books",
        "notebook", "notebooks", "notes", "stationery", "pen", "pens", "pencil", "pencils",
        "calculator", "xerox", "photocopy", "print", "printing", "printout", "printouts",
        "binding", "tuition", "coaching", "course", "udemy", "coursera", "exam", "semester",
        "college fee", "library", "assignment", "study", "lab manual", "academic", "education"
    ],
    "Food": [
        "grocery shopping", "groceries", "grocery", "supermarket",
        "food", "lunch", "dinner", "breakfast", "brunch", "meal", "meals", "snack", "snacks",
        "tea", "chai", "coffee", "cappuccino", "latte", "cold coffee", "cafe", "cafeteria",
        "canteen", "mess", "dhaba", "zomato", "swiggy", "pizza", "burger", "biryani",
        "sandwich", "roll", "shawarma", "noodles", "maggi", "maggie", "pasta", "samosa",
        "dosa", "idli", "ice cream", "juice", "shake", "water", "biscuit",
        "chips", "starbucks", "dominos", "mcdonalds", "subway", "kfc", "restaurant",
        "eat", "eating", "zepto", "blinkit", "instamart"
    ],
    "Entertainment": [
        "movie ticket", "cricket match", "match ticket", "ipl ticket", "ipl match",
        "movie", "movies", "cinema", "theatre", "pvr", "inox", "film", "popcorn",
        "netflix", "spotify", "prime", "hotstar", "youtube", "game", "games", "gaming",
        "steam", "playstation", "ps5", "xbox", "arcade", "bowling", "party", "club",
        "concert", "fest", "outing", "ipl"
    ],
    "Transport": [
        "metro card recharge", "metro card", "metro recharge", "bus pass", "transit card",
        "cab", "taxi", "uber", "ola", "auto", "rickshaw", "rapido", "blusmart", "ride",
        "bus", "metro", "subway", "train", "railway", "flight", "petrol", "diesel",
        "fuel", "gas", "cng", "parking", "toll", "fastag", "ticket", "fare", "scooter",
        "bike", "commute", "travel"
    ],
    "Shopping": [
        "cloth", "clothes", "clothing", "shirt", "tshirt", "jeans", "pant", "pants",
        "trousers", "shoe", "shoes", "sneaker", "sneakers", "jacket", "hoodie", "sweater",
        "dress", "charger", "cable", "headphone", "headphones", "earphone", "earphones",
        "airpod", "airpods", "earbuds", "powerbank", "usb", "mouse", "keyboard", "case",
        "cover", "backpack", "bag", "wallet", "amazon", "flipkart", "myntra", "meesho",
        "shopping", "soap", "shampoo", "perfume", "deodorant"
    ],
    "Health": [
        "medicine", "medicines", "meds", "tablet", "tablets", "pill", "pills", "syrup",
        "paracetamol", "pharmacy", "chemist", "apollo", "doctor", "consultation", "clinic",
        "hospital", "dentist", "gym", "fitness", "protein", "supplement", "supplements",
        "health", "checkup", "bandage", "eye checkup"
    ],
    "Other": [
        "recharge", "phone bill", "wifi", "internet", "broadband", "electricity",
        "rent", "room rent", "pg rent", "hostel rent", "laundry", "haircut", "salon",
        "maintenance"
    ]
}

def classify_expense_category(description: str = "", category_hint: str = "") -> str:
    """Intelligently classifies student expenses into the best matching category.
    Uses maximum-length keyword matching strategy so compound phrases match before generic tokens."""
    text = f"{description} {category_hint}".lower().strip()
    
    # Priority 1: Match longest keyword first to disambiguate (e.g. 'grocery shopping' -> Food, 'movie ticket' -> Entertainment)
    all_kw = []
    for cat, kws in EXPENSE_TAXONOMY.items():
        for kw in kws:
            all_kw.append((kw, cat))
    all_kw.sort(key=lambda x: len(x[0]), reverse=True)

    for kw, cat in all_kw:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return cat
                
    # Priority 2: Use category hint if valid
    valid = ["Academic", "Food", "Transport", "Shopping", "Health", "Entertainment", "Other"]
    if category_hint:
        hint_clean = category_hint.strip().title()
        if hint_clean in valid:
            return hint_clean
        for v in valid:
            if v.lower() in category_hint.lower():
                return v

    return "Other"

def log_expense(
    user_id: int,
    amount: float,
    category: str = "",
    description: str = "",
    merchant: str = "Direct Entry",
    payment_method: str = "UPI"
) -> Dict[str, Any]:
    """Directly logs an expense transaction into the student's expenses database with intelligent category classification."""
    from backend.app.expenses.schemas import ExpenseCreate
    from backend.app.expenses.service import ExpenseService

    final_cat = classify_expense_category(description=description, category_hint=category)
    final_desc = description.strip().title() if description.strip() else f"{final_cat} Expense"
    
    clean_method = (payment_method or "UPI").upper()
    if clean_method not in ["UPI", "CASH", "CARD"]:
        clean_method = "CASH" if "cash" in str(payment_method).lower() else ("CARD" if "card" in str(payment_method).lower() else "UPI")

    with SessionLocal() as db:
        expense = ExpenseService.create_expense(
            db,
            user_id,
            ExpenseCreate(
                amount=float(amount),
                category=final_cat,
                description=final_desc,
                merchant=merchant or "Direct Entry",
                payment_method=clean_method,
                expense_date=datetime.date.today()
            ),
            source="AI_VOICE_AGENT"
        )
        return {
            "status": "success",
            "action": "log_expense",
            "expense_id": expense.id,
            "amount": expense.amount,
            "category": expense.category,
            "description": expense.description,
            "payment_method": expense.payment_method,
            "merchant": expense.merchant,
            "date": str(expense.expense_date),
            "message": f"Successfully logged ₹{expense.amount:.2f} for '{expense.description}' under category '{expense.category}' ({expense.payment_method}) directly into your database."
        }

def set_budget(
    user_id: int,
    amount: float,
    target_type: str = "budget",
    month: Optional[str] = None
) -> Dict[str, Any]:
    """Directly updates student monthly budget or remaining balance in the database."""
    from backend.app.expenses.models import Budget, Expense
    from sqlalchemy import func, extract

    if not month:
        month = datetime.date.today().strftime("%Y-%m")

    with SessionLocal() as db:
        year_int, month_int = map(int, month.split("-"))
        total_spent = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.expense_date) == year_int,
            extract('month', Expense.expense_date) == month_int
        ).scalar()
        total_spent = round(float(total_spent), 2)

        budget = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).first()
        if not budget:
            budget = Budget(user_id=user_id, month=month, currency="INR")
            db.add(budget)

        amt = float(amount)
        if target_type == "balance":
            budget.current_balance = amt
            budget.total_budget = round(amt + total_spent, 2)
            desc = f"remaining balance to ₹{amt:,.2f} (total monthly budget adjusted to ₹{budget.total_budget:,.2f} with ₹{total_spent:,.2f} already spent)"
        else:
            budget.total_budget = amt
            budget.current_balance = max(0.0, round(amt - total_spent, 2))
            desc = f"monthly budget limit to ₹{amt:,.2f} (remaining balance is ₹{budget.current_balance:,.2f} after ₹{total_spent:,.2f} spent)"

        db.commit()
        db.refresh(budget)

        return {
            "status": "success",
            "action": "set_budget",
            "month": budget.month,
            "total_budget": budget.total_budget,
            "current_balance": budget.current_balance,
            "total_spent": total_spent,
            "target_type": target_type,
            "message": f"Successfully updated your {desc} in your database."
        }

def create_trip(
    user_id: int,
    destination: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    budget: float = 5000.0,
    travelers: int = 1
) -> Dict[str, Any]:
    """Directly creates a trip in the student's travel database and checks for academic conflicts."""
    from backend.app.travel.schemas import TripCreate
    from backend.app.travel.service import TravelService

    now = datetime.date.today()
    s_date = now + datetime.timedelta(days=7)
    e_date = s_date + datetime.timedelta(days=4)

    if start_date:
        try:
            s_date = datetime.datetime.strptime(str(start_date)[:10], "%Y-%m-%d").date()
        except Exception:
            pass
    if end_date:
        try:
            e_date = datetime.datetime.strptime(str(end_date)[:10], "%Y-%m-%d").date()
        except Exception:
            pass
    if e_date < s_date:
        e_date = s_date + datetime.timedelta(days=3)

    with SessionLocal() as db:
        trip = TravelService.create_trip(db, user_id, TripCreate(
            destination=destination,
            start_date=s_date,
            end_date=e_date,
            budget=float(budget),
            travelers=int(travelers),
            status="PLANNING"
        ))
        conflict = TravelService.check_academic_conflicts(db, user_id, trip.id)
        return {
            "status": "success",
            "action": "create_trip",
            "trip_id": trip.id,
            "destination": trip.destination,
            "start_date": str(trip.start_date),
            "end_date": str(trip.end_date),
            "budget": trip.budget,
            "has_conflict": conflict.has_conflict,
            "message": f"Trip #{trip.id} to '{trip.destination}' ({trip.start_date} to {trip.end_date}) directly created in database." + (" ⚠️ Warning: Academic conflict with your exam schedule detected!" if conflict.has_conflict else " No schedule conflicts.")
        }

def log_note(user_id: int, note_text: str, category: str = "Notes", priority: str = "MEDIUM") -> Dict[str, Any]:
    """Logs arbitrary student information, reminders, memories, or notes directly into the database."""
    with SessionLocal() as db:
        clean_title = (note_text or "General Note").strip()
        task = StudyService.create_task(db, user_id, TaskCreate(
            title=clean_title[:80],
            description=clean_title,
            subject=category or "Notes",
            priority=priority,
            due_date=None
        ))
        return {
            "status": "success",
            "action": "log_note",
            "note_id": task.id,
            "title": task.title,
            "category": task.subject,
            "message": f"Successfully locked note #{task.id} '{task.title}' into your database."
        }

def complete_task(user_id: int, task_id: int) -> Dict[str, Any]:
    """Mark a task as completed."""
    with SessionLocal() as db:
        try:
            task = StudyService.complete_task(db, user_id, task_id)
            return {"status": "success", "message": f"Completed task: '{task.title}'"}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

def complete_task_flexible(user_id: int, query_text: str) -> Dict[str, Any]:
    """
    Completes a task by numeric ID or by using the Local LLM (Llama 3.2)
    to semantically identify the task based on conceptual meaning, synonyms, and subject context.
    """
    import re
    from backend.app.study.models import Task
    from backend.app.voice.llm_engine import local_student_llm

    with SessionLocal() as db:
        # 1. Numeric ID match (e.g. "complete task 3", "#3")
        id_match = re.search(r"\b(\d+)\b", query_text)
        if id_match:
            task_id = int(id_match.group(1))
            task = db.query(Task).filter(Task.user_id == user_id, Task.id == task_id).first()
            if task:
                task.status = "COMPLETED"
                task.completed_at = datetime.datetime.utcnow()
                db.commit()
                return {
                    "status": "success",
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"Successfully completed task #{task.id}: '{task.title}'."
                }

        # 2. Get pending candidate tasks
        pending_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").all()
        if not pending_tasks:
            return {"status": "error", "message": "You currently have no pending tasks on your schedule!"}

        candidates = [{"id": t.id, "title": t.title, "subject": t.subject} for t in pending_tasks]

        # 3. Semantic resolution via Local Neural LLM
        matched_id = local_student_llm.match_task_semantically(query_text, candidates)
        if matched_id:
            matched_task = db.query(Task).filter(Task.user_id == user_id, Task.id == matched_id).first()
            if matched_task:
                matched_task.status = "COMPLETED"
                matched_task.completed_at = datetime.datetime.utcnow()
                db.commit()
                return {
                    "status": "success",
                    "task_id": matched_task.id,
                    "title": matched_task.title,
                    "message": f"Identified task #{matched_task.id} '{matched_task.title}' via semantic matching and marked it completed."
                }

        # If generic completion utterance (e.g. "i finished it", "it is done", "done"), pick the most urgent/overdue pending task
        generic_tokens = {"it", "this", "done", "finished", "completed", "assignment", "task", ""}
        cleaned = re.sub(r"\b(i|have|finished|the|task|mark|it|as|complete|completed|done|with|please)\b", "", query_text, flags=re.I).strip()
        if not cleaned or cleaned.lower() in generic_tokens:
            urgent_task = sorted(pending_tasks, key=lambda x: (x.due_date or datetime.datetime.max))[0]
            urgent_task.status = "COMPLETED"
            urgent_task.completed_at = datetime.datetime.utcnow()
            db.commit()
            return {
                "status": "success",
                "task_id": urgent_task.id,
                "title": urgent_task.title,
                "message": f"Marked '{urgent_task.title}' as completed."
            }

        # If no conceptual match found, list pending tasks
        pending_titles = [f"'{t.title}'" for t in pending_tasks[:3]]
        return {
            "status": "not_found",
            "message": f"Could not find a task matching '{query_text}'. Your pending tasks are: {', '.join(pending_titles) if pending_titles else 'None'}."
        }

def extend_task_deadline(user_id: int, query_text: str = "", minutes: int = 60) -> Dict[str, Any]:
    """
    Extends the deadline of a task in real-time by a specified number of minutes.
    """
    import re
    from backend.app.study.models import Task
    from backend.app.voice.llm_engine import local_student_llm

    with SessionLocal() as db:
        pending_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").all()
        if not pending_tasks:
            return {"status": "error", "message": "You currently have no pending tasks to extend."}

        target_task = None
        id_match = re.search(r"\b(\d+)\b", query_text)
        if id_match:
            t_id = int(id_match.group(1))
            target_task = db.query(Task).filter(Task.user_id == user_id, Task.id == t_id).first()

        if not target_task and query_text:
            candidates = [{"id": t.id, "title": t.title, "subject": t.subject} for t in pending_tasks]
            matched_id = local_student_llm.match_task_semantically(query_text, candidates)
            if matched_id:
                target_task = db.query(Task).filter(Task.user_id == user_id, Task.id == matched_id).first()

        if not target_task:
            target_task = sorted(pending_tasks, key=lambda x: (x.due_date or datetime.datetime.max))[0]

        now = datetime.datetime.now()
        base_time = target_task.due_date if (target_task.due_date and target_task.due_date > now) else now
        new_due = base_time + datetime.timedelta(minutes=minutes)

        target_task.due_date = new_due
        target_task.status = "PENDING"
        db.commit()

        new_time_str = new_due.strftime("%I:%M %p").lstrip("0")
        return {
            "status": "success",
            "task_id": target_task.id,
            "title": target_task.title,
            "minutes_added": minutes,
            "new_due_date": new_time_str,
            "message": f"Extended deadline for '{target_task.title}' by {minutes} minutes to {new_time_str}."
        }

def update_task_priority(user_id: int, query_text: str = "", priority: str = "HIGH") -> Dict[str, Any]:
    """
    Changes the priority level (LOW, MEDIUM, HIGH) of a task based on student's voice command.
    """
    import re
    from backend.app.study.models import Task
    from backend.app.voice.llm_engine import local_student_llm

    priority = priority.upper()
    if priority not in ("LOW", "MEDIUM", "HIGH"):
        priority = "HIGH"

    with SessionLocal() as db:
        pending_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").all()
        if not pending_tasks:
            return {"status": "error", "message": "You currently have no pending tasks to update."}

        target_task = None
        id_match = re.search(r"\b(\d+)\b", query_text)
        if id_match:
            t_id = int(id_match.group(1))
            target_task = db.query(Task).filter(Task.user_id == user_id, Task.id == t_id).first()

        if not target_task and query_text:
            candidates = [{"id": t.id, "title": t.title, "subject": t.subject} for t in pending_tasks]
            matched_id = local_student_llm.match_task_semantically(query_text, candidates)
            if matched_id:
                target_task = db.query(Task).filter(Task.user_id == user_id, Task.id == matched_id).first()

        if not target_task:
            target_task = sorted(pending_tasks, key=lambda x: (x.due_date or datetime.datetime.max))[0]

        target_task.priority = priority
        db.commit()

        return {
            "status": "success",
            "task_id": target_task.id,
            "title": target_task.title,
            "priority": priority,
            "message": f"Updated priority of '{target_task.title}' to {priority}."
        }

def log_sleep(user_id: int, sleep_hours: float, mood: int = 4, energy: int = 4, notes: str = "Logged via AI Voice Assistant") -> Dict[str, Any]:
    """Logs or updates the student's sleep and wellness record in real-time."""
    from backend.app.health.schemas import HealthLogCreate
    with SessionLocal() as db:
        record = HealthService.log_wellness(db, user_id, HealthLogCreate(
            sleep_hours=sleep_hours,
            mood=mood,
            energy_level=energy,
            notes=notes
        ))
        return {
            "status": "success",
            "action": "log_sleep",
            "sleep_hours": record.sleep_hours,
            "mood": record.mood,
            "energy_level": record.energy_level,
            "stress_level": record.stress_level,
            "stress_score": record.stress_score,
            "record_date": str(record.record_date),
            "notes": record.notes,
            "message": f"Successfully logged {record.sleep_hours}h sleep, mood {record.mood}/5 ({record.stress_level} stress) for today ({record.record_date}) into your health & vitals database."
        }

def get_wellness_state(user_id: int) -> Dict[str, Any]:
    """Retrieve recent wellness statistics, sleep baseline status, and stress levels."""
    with SessionLocal() as db:
        summary = HealthService.get_wellness_summary(db, user_id)
        stress = HealthService.predict_stress(db, user_id)
        return {
            "average_sleep_7d": summary.average_sleep_7d,
            "sleep_baseline": summary.sleep_baseline,
            "sleep_status": summary.sleep_status,
            "current_stress_level": stress.stress_level,
            "stress_signals": stress.signals,
            "wellness_advice": stress.recommendation
        }

def get_expenses_summary(user_id: int) -> Dict[str, Any]:
    """Retrieve the current month's spending, budget status, and category breakdown."""
    with SessionLocal() as db:
        summary = ExpenseService.get_expense_summary(db, user_id)
        forecast = ExpenseService.forecast_out_of_cash(db, user_id)
        return {
            "month": summary.month,
            "total_spent": summary.total_spent,
            "budget_limit": summary.budget_limit,
            "remaining": summary.remaining,
            "utilization_percent": summary.utilization_percent,
            "estimated_days_runway": forecast.estimated_days_remaining,
            "financial_risk_level": forecast.financial_risk_level,
            "category_breakdown": summary.category_breakdown
        }

def get_upcoming_trips(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve upcoming travel plans and check for academic schedule conflicts."""
    with SessionLocal() as db:
        trips = TravelService.get_trips(db, user_id)
        result = []
        for t in trips:
            conflict = TravelService.check_academic_conflicts(db, user_id, t.id)
            result.append({
                "trip_id": t.id,
                "destination": t.destination,
                "start_date": t.start_date.strftime("%Y-%m-%d"),
                "end_date": t.end_date.strftime("%Y-%m-%d"),
                "budget": t.budget,
                "status": t.status,
                "has_academic_conflict": conflict.has_conflict,
                "conflicts": [c.model_dump() for c in conflict.conflicts]
            })
        return result

def get_student_intelligence(user_id: int) -> Dict[str, Any]:
    """
    Retrieve unified cross-domain intelligence, compound risk level, 
    and check if a proactive phone call / notification is recommended.
    """
    with SessionLocal() as db:
        state = IntelligenceService.evaluate_student_state(db, user_id)
        prefs = CoreService.get_preferences(db, user_id)

        # Calling policy check
        should_call = (
            state.proactive_intervention_recommended
            and prefs.voice_calls_enabled
            and prefs.calling_consent_status == "OPTED_IN"
        )

        return {
            "user_id": user_id,
            "compound_risk_level": state.compound_risk_level,
            "compound_risk_score": state.compound_risk_score,
            "proactive_intervention_recommended": state.proactive_intervention_recommended,
            "proactive_call_permitted": should_call,
            "proactive_intervention_reason": state.proactive_intervention_reason,
            "detected_risks": [r.model_dump() for r in state.detected_risks],
            "priority_insights": [i.model_dump() for i in state.priority_insights]
        }


def get_student_schedule(user_id: int) -> Dict[str, Any]:
    """Retrieve full daily academic schedule, lectures, labs, and pending deliverables."""
    now_dt = datetime.datetime.now()
    day_name = now_dt.strftime("%A")
    timetable = {
        "Monday": [
            {"time": "08:00 AM - 09:30 AM", "course": "CS301 Operating Systems", "room": "Lecture Hall 204", "type": "Lecture"},
            {"time": "10:00 AM - 11:30 AM", "course": "CS303 Database Management Systems", "room": "Hall 102", "type": "Lecture"},
            {"time": "02:00 PM - 04:00 PM", "course": "CS305 Computer Networks Lab", "room": "Systems Lab 3", "type": "Lab"}
        ],
        "Tuesday": [
            {"time": "08:30 AM - 10:00 AM", "course": "CS302 Computer Networks", "room": "Hall 105", "type": "Lecture"},
            {"time": "10:30 AM - 12:00 PM", "course": "CS304 Software Engineering", "room": "Hall 201", "type": "Lecture"},
            {"time": "02:30 PM - 04:30 PM", "course": "CS306 OS Kernel Lab", "room": "Systems Lab 1", "type": "Lab"}
        ],
        "Wednesday": [
            {"time": "08:00 AM - 09:30 AM", "course": "CS301 Operating Systems", "room": "Lecture Hall 204", "type": "Lecture"},
            {"time": "10:00 AM - 11:30 AM", "course": "CS303 Database Systems", "room": "Hall 102", "type": "Lecture"},
            {"time": "01:30 PM - 03:30 PM", "course": "CS307 Cloud Computing Elective", "room": "Seminar Room", "type": "Seminar"}
        ],
        "Thursday": [
            {"time": "08:00 AM - 09:30 AM", "course": "CS302 Computer Networks", "room": "Hall 105", "type": "Lecture"},
            {"time": "10:00 AM - 11:30 AM", "course": "CS304 Software Engineering", "room": "Hall 201", "type": "Lecture"},
            {"time": "02:00 PM - 04:00 PM", "course": "CS308 DBMS Lab", "room": "Database Lab 2", "type": "Lab"}
        ],
        "Friday": [
            {"time": "09:00 AM - 10:30 AM", "course": "CS309 Design & Analysis of Algorithms", "room": "Hall 303", "type": "Lecture"},
            {"time": "11:00 AM - 12:30 PM", "course": "CS310 Web Technologies", "room": "Hall 202", "type": "Lecture"},
            {"time": "02:00 PM - 03:30 PM", "course": "CS311 Capstone Mentorship", "room": "Conference Room", "type": "Mentorship"}
        ],
        "Saturday": [
            {"time": "10:00 AM - 01:00 PM", "course": "Software Engineering Project Sprint", "room": "Innovation Hub", "type": "Sprint"},
            {"time": "03:00 PM - 05:00 PM", "course": "Library Study & Review Block", "room": "Central Library", "type": "Self-Study"}
        ],
        "Sunday": [
            {"time": "10:00 AM - 12:00 PM", "course": "Weekly Goal Review & Prep", "room": "Hostel Study Desk", "type": "Review"},
            {"time": "05:00 PM - 08:00 PM", "course": "Recreation & Sleep Recovery Block", "room": "Campus / Dorm", "type": "Wellness"}
        ]
    }
    today_sessions = timetable.get(day_name, timetable["Thursday"])
    tasks = get_tasks(user_id, status="PENDING")
    return {
        "day": day_name,
        "date": now_dt.strftime("%A, %B %d, %Y"),
        "time": now_dt.strftime("%I:%M %p").lstrip("0"),
        "classes": today_sessions,
        "pending_tasks_count": len(tasks),
        "priority_tasks": tasks[:3],
        "summary": f"On {day_name}, you have {len(today_sessions)} scheduled academic blocks and {len(tasks)} pending assignment deliverables."
    }

