from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.router import get_current_user_id
from backend.app.study.schemas import (
    TaskCreate, TaskUpdate, TaskOut,
    StudyMaterialCreate, StudyMaterialOut,
    StudyPlanGenerateRequest, StudyPlanOut,
    ProductivityRiskOut
)
from backend.app.study.service import StudyService

router = APIRouter(prefix="/study", tags=["Study & Tasks"])

@router.get("/tasks", response_model=list[TaskOut])
def get_tasks(
    status: str = Query(None, description="Filter by PENDING, IN_PROGRESS, COMPLETED, OVERDUE"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.get_tasks(db, user_id, status)

@router.post("/tasks", response_model=TaskOut)
def create_task(
    data: TaskCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.create_task(db, user_id, data)

@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return StudyService.get_task(db, user_id, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return StudyService.update_task(db, user_id, task_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return StudyService.complete_task(db, user_id, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        StudyService.delete_task(db, user_id, task_id)
        return {"status": "success", "message": f"Task {task_id} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/study-material", response_model=StudyMaterialOut)
def upload_study_material(
    data: StudyMaterialCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.add_study_material(db, user_id, data)

@router.post("/study-plans/generate", response_model=StudyPlanOut)
def generate_study_plan(
    req: StudyPlanGenerateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.generate_study_plan(db, user_id, req)

@router.get("/study-plans", response_model=list[StudyPlanOut])
def get_study_plans(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.get_study_plans(db, user_id)

@router.get("/productivity/risk", response_model=ProductivityRiskOut)
def get_productivity_risk(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return StudyService.calculate_productivity_risk(db, user_id)
