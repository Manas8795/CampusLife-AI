from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: Optional[str] = "Food"
    merchant: Optional[str] = "Unknown"
    description: Optional[str] = ""
    expense_date: Optional[date] = None
    payment_method: Optional[str] = "UPI"
    currency: Optional[str] = "INR"

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None
    payment_method: Optional[str] = None

class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    currency: str
    category: str
    merchant: str
    description: str
    expense_date: date
    payment_method: str
    source: str
    created_at: datetime

class ReceiptUploadRequest(BaseModel):
    raw_ocr_simulation: Optional[str] = "CAMPUS BISTRO\n2x Cold Coffee - 160\n1x Veg Club Sandwich - 140\nTotal: 300\nDate: 2026-10-05"

class ReceiptOut(BaseModel):
    id: int
    user_id: int
    ocr_text: str
    parsed_json: Dict
    status: str
    created_at: datetime

class ReceiptConfirmRequest(BaseModel):
    receipt_id: int
    confirmed_amount: float
    confirmed_category: str
    confirmed_merchant: str
    confirmed_description: Optional[str] = ""

class BudgetSetRequest(BaseModel):
    month: str # e.g. "2026-10"
    total_budget: float = Field(..., gt=0)
    current_balance: Optional[float] = None
    currency: Optional[str] = "INR"

class BudgetOut(BaseModel):
    id: int
    user_id: int
    month: str
    total_budget: float
    current_balance: float
    current_spending: float
    remaining_budget: float
    utilization_percentage: float
    currency: str

class ExpenseSummaryOut(BaseModel):
    month: str
    total_spent: float
    budget_limit: float
    remaining: float
    utilization_percent: float
    category_breakdown: Dict[str, float]
    expense_count: int

class OutOfCashForecastOut(BaseModel):
    current_balance: float
    daily_burn_rate: float
    estimated_days_remaining: int
    predicted_out_of_cash_date: str
    financial_risk_level: str # LOW, MEDIUM, HIGH
    explanation: str
