import json
import datetime
from sqlalchemy.orm import Session
from backend.app.study.models import Task, StudyMaterial, StudyPlan, ProductivityRecord
from backend.app.study.schemas import TaskCreate, TaskUpdate, StudyMaterialCreate, StudyPlanGenerateRequest, ProductivityRiskOut

class StudyService:
    @staticmethod
    def get_tasks(db: Session, user_id: int, status: str = None) -> list[Task]:
        query = db.query(Task).filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status.upper())
        return query.order_by(Task.due_date.asc().nullslast(), Task.id.desc()).all()

    @staticmethod
    def get_task(db: Session, user_id: int, task_id: int) -> Task:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise ValueError("Task not found")
        return task

    @staticmethod
    def create_task(db: Session, user_id: int, data: TaskCreate, source: str = "MANUAL") -> Task:
        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description or "",
            subject=data.subject or "General",
            priority=(data.priority or "MEDIUM").upper(),
            status=(data.status or "PENDING").upper(),
            due_date=data.due_date,
            source=source
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, user_id: int, task_id: int, data: TaskUpdate) -> Task:
        task = StudyService.get_task(db, user_id, task_id)
        for key, val in data.dict(exclude_unset=True).items():
            if val is None and key != "due_date":
                continue
            if val is not None and key in ["priority", "status"]:
                val = val.upper()
            setattr(task, key, val)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def complete_task(db: Session, user_id: int, task_id: int) -> Task:
        task = StudyService.get_task(db, user_id, task_id)
        task.status = "COMPLETED"
        task.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, user_id: int, task_id: int) -> bool:
        task = StudyService.get_task(db, user_id, task_id)
        db.delete(task)
        db.commit()
        return True

    @staticmethod
    def add_study_material(db: Session, user_id: int, data: StudyMaterialCreate) -> StudyMaterial:
        mat = StudyMaterial(
            user_id=user_id,
            title=data.title,
            subject=data.subject or "General",
            content_summary=data.content_summary or "",
            file_path=data.file_path
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        return mat

    @staticmethod
    def generate_study_plan(db: Session, user_id: int, req: StudyPlanGenerateRequest) -> StudyPlan:
        now = datetime.datetime.now()
        days_remaining = max(1, (req.exam_date - now).days)
        topics = req.topics or ["Core Concepts & Syllabus Overview", "Problem Solving & Practice", "Mock Revision & Self-Assessment"]

        plan_days = []
        for i, topic in enumerate(topics):
            day_offset = int((i / max(1, len(topics))) * days_remaining)
            scheduled_date = (now + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            plan_days.append({
                "day_number": i + 1,
                "date": scheduled_date,
                "topic": topic,
                "estimated_minutes": int(req.available_hours_per_day * 60)
            })

            if req.auto_create_tasks:
                task = Task(
                    user_id=user_id,
                    title=f"Study {req.subject}: {topic}",
                    description=f"Automated study session for upcoming exam on {req.exam_date.strftime('%Y-%m-%d')}",
                    subject=req.subject,
                    priority="HIGH" if days_remaining <= 3 else "MEDIUM",
                    status="PENDING",
                    due_date=now + datetime.timedelta(days=day_offset),
                    source="AI_STUDY_PLAN"
                )
                db.add(task)

        study_plan = StudyPlan(
            user_id=user_id,
            subject=req.subject,
            exam_date=req.exam_date,
            start_date=now,
            end_date=req.exam_date,
            plan_data=json.dumps(plan_days)
        )
        db.add(study_plan)
        db.commit()
        db.refresh(study_plan)
        return study_plan

    @staticmethod
    def get_study_plans(db: Session, user_id: int) -> list[StudyPlan]:
        return db.query(StudyPlan).filter(StudyPlan.user_id == user_id).order_by(StudyPlan.exam_date.asc()).all()

    @staticmethod
    def calculate_productivity_risk(db: Session, user_id: int) -> ProductivityRiskOut:
        now = datetime.datetime.now()
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        total_tasks = len(tasks)
        pending_tasks = 0
        overdue_tasks = 0
        completed_tasks = 0

        for t in tasks:
            if t.status == "COMPLETED":
                completed_tasks += 1
            else:
                if t.due_date and t.due_date < now:
                    overdue_tasks += 1
                    t.status = "OVERDUE"
                else:
                    pending_tasks += 1

        db.commit()

        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 1.0
        reason_codes = []
        risk_score = 0.1

        if overdue_tasks > 0:
            risk_score += min(0.4, overdue_tasks * 0.15)
            reason_codes.append("OVERDUE_TASKS_EXIST")
        if pending_tasks >= 5:
            risk_score += 0.25
            reason_codes.append("HIGH_PENDING_TASK_BACKLOG")
        if completion_rate < 0.5 and total_tasks >= 3:
            risk_score += 0.2
            reason_codes.append("LOW_HISTORICAL_COMPLETION_RATE")

        risk_score = min(1.0, round(risk_score, 2))
        if risk_score >= 0.7:
            risk_level = "HIGH"
            explanation = "Your academic productivity is at high risk due to multiple overdue deadlines and a heavy pending task backlog."
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
            explanation = "Moderate delay risk detected. You have pending items approaching their due dates."
        else:
            risk_level = "LOW"
            explanation = "Your task completion rate is healthy and tasks are on track."

        record = ProductivityRecord(
            user_id=user_id,
            risk_level=risk_level,
            risk_score=risk_score,
            reason_codes=json.dumps(reason_codes),
            explanation=explanation
        )
        db.add(record)
        db.commit()

        return ProductivityRiskOut(
            risk_level=risk_level,
            risk_score=risk_score,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            overdue_tasks=overdue_tasks,
            completed_tasks=completed_tasks,
            completion_rate=round(completion_rate, 2),
            reason_codes=reason_codes,
            explanation=explanation
        )
