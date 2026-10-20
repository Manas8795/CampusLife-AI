from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.router import get_current_user_id
from backend.app.expenses.schemas import (
    ExpenseCreate, ExpenseUpdate, ExpenseOut,
    ReceiptUploadRequest, ReceiptOut, ReceiptConfirmRequest,
    BudgetSetRequest, BudgetOut, ExpenseSummaryOut, OutOfCashForecastOut
)
from backend.app.expenses.service import ExpenseService
import json

router = APIRouter(prefix="/expenses", tags=["Expenses & Finances"])

@router.post("", response_model=ExpenseOut)
def create_expense(
    data: ExpenseCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return ExpenseService.create_expense(db, user_id, data)

@router.get("", response_model=list[ExpenseOut])
def get_expenses(
    category: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_expenses(db, user_id, category=category, limit=limit)

@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return ExpenseService.update_expense(db, user_id, expense_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        ExpenseService.delete_expense(db, user_id, expense_id)
        return {"status": "success", "message": f"Expense {expense_id} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/summary", response_model=ExpenseSummaryOut)
def get_summary(
    month: str = Query(None, description="Format: YYYY-MM"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_expense_summary(db, user_id, month)

@router.get("/forecast", response_model=OutOfCashForecastOut)
def get_forecast(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return ExpenseService.forecast_out_of_cash(db, user_id)

@router.post("/receipts/upload", response_model=ReceiptOut)
def upload_receipt(
    req: ReceiptUploadRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    rec = ExpenseService.upload_and_parse_receipt(db, user_id, req)
    return ReceiptOut(
        id=rec.id,
        user_id=rec.user_id,
        ocr_text=rec.ocr_text,
        parsed_json=json.loads(rec.parsed_json),
        status=rec.status,
        created_at=rec.created_at
    )

@router.post("/receipts/confirm", response_model=ExpenseOut)
def confirm_receipt(
    req: ReceiptConfirmRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return ExpenseService.confirm_receipt_as_expense(db, user_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/budget", response_model=BudgetOut)
def set_budget(
    req: BudgetSetRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    ExpenseService.set_budget(db, user_id, req)
    return ExpenseService.get_budget_status(db, user_id, req.month)

@router.get("/budget", response_model=BudgetOut)
def get_budget(
    month: str = Query(None, description="Format: YYYY-MM"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_budget_status(db, user_id, month)
