import json
import re
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.app.expenses.models import Expense, Receipt, Budget
from backend.app.expenses.schemas import (
    ExpenseCreate, ExpenseUpdate, ReceiptUploadRequest, ReceiptConfirmRequest,
    BudgetSetRequest, BudgetOut, ExpenseSummaryOut, OutOfCashForecastOut
)

class ExpenseService:
    @staticmethod
    def create_expense(db: Session, user_id: int, data: ExpenseCreate, source: str = "MANUAL") -> Expense:
        exp_date = data.expense_date or datetime.date.today()
        expense = Expense(
            user_id=user_id,
            amount=round(data.amount, 2),
            currency=data.currency or "INR",
            category=data.category or "Food",
            merchant=data.merchant or "Unknown",
            description=data.description or "",
            expense_date=exp_date,
            payment_method=data.payment_method or "UPI",
            source=source
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def get_expenses(db: Session, user_id: int, category: str = None, limit: int = 50) -> list[Expense]:
        query = db.query(Expense).filter(Expense.user_id == user_id)
        if category:
            query = query.filter(Expense.category == category)
        return query.order_by(Expense.expense_date.desc(), Expense.id.desc()).limit(limit).all()

    @staticmethod
    def update_expense(db: Session, user_id: int, expense_id: int, data: ExpenseUpdate) -> Expense:
        exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
        if not exp:
            raise ValueError("Expense not found")
        for key, val in data.dict(exclude_unset=True).items():
            if val is not None:
                setattr(exp, key, val)
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def delete_expense(db: Session, user_id: int, expense_id: int) -> bool:
        exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
        if not exp:
            raise ValueError("Expense not found")
        db.delete(exp)
        db.commit()
        return True

    @staticmethod
    def upload_and_parse_receipt(db: Session, user_id: int, req: ReceiptUploadRequest) -> Receipt:
        ocr_text = req.raw_ocr_simulation or "General Merchant Receipt - Total 250"
        
        # Heuristic AI parser skeleton
        merchant_match = re.search(r"^[^\n\r]+", ocr_text)
        merchant = merchant_match.group(0).strip() if merchant_match else "Campus Merchant"
        
        amount = 150.0
        amount_match = re.search(r"(?:total|amt|inr|rs\.?|₹)\s*:?\s*(\d+(?:\.\d{1,2})?)", ocr_text, re.IGNORECASE)
        if amount_match:
            amount = float(amount_match.group(1))

        category = "Food"
        lower = ocr_text.lower()
        if any(w in lower for w in ["book", "stationery", "print", "xerox", "course"]):
            category = "Education"
        elif any(w in lower for w in ["cab", "auto", "metro", "bus", "uber", "ola", "train"]):
            category = "Transport"
        elif any(w in lower for w in ["movie", "game", "netflix"]):
            category = "Entertainment"

        parsed = {
            "merchant": merchant,
            "total_amount": amount,
            "category": category,
            "detected_date": datetime.date.today().strftime("%Y-%m-%d"),
            "raw_preview": ocr_text[:100]
        }

        receipt = Receipt(
            user_id=user_id,
            ocr_text=ocr_text,
            parsed_json=json.dumps(parsed),
            status="PROCESSED"
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        return receipt

    @staticmethod
    def confirm_receipt_as_expense(db: Session, user_id: int, req: ReceiptConfirmRequest) -> Expense:
        receipt = db.query(Receipt).filter(Receipt.id == req.receipt_id, Receipt.user_id == user_id).first()
        if not receipt:
            raise ValueError("Receipt not found")

        expense = Expense(
            user_id=user_id,
            amount=req.confirmed_amount,
            category=req.confirmed_category,
            merchant=req.confirmed_merchant,
            description=req.confirmed_description or f"Receipt #{receipt.id}",
            expense_date=datetime.date.today(),
            payment_method="UPI",
            source="OCR_RECEIPT"
        )
        receipt.status = "CONFIRMED"
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def set_budget(db: Session, user_id: int, req: BudgetSetRequest) -> Budget:
        budget = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == req.month).first()
        if not budget:
            budget = Budget(
                user_id=user_id,
                month=req.month,
                total_budget=req.total_budget,
                current_balance=req.current_balance if req.current_balance is not None else req.total_budget,
                currency=req.currency or "INR"
            )
            db.add(budget)
        else:
            budget.total_budget = req.total_budget
            if req.current_balance is not None:
                budget.current_balance = req.current_balance
            if req.currency:
                budget.currency = req.currency
        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def get_budget_status(db: Session, user_id: int, month: str = None) -> BudgetOut:
        if not month:
            month = datetime.date.today().strftime("%Y-%m")

        budget = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).first()
        if not budget:
            budget = Budget(
                user_id=user_id,
                month=month,
                total_budget=10000.0,
                current_balance=6000.0,
                currency="INR"
            )
            db.add(budget)
            db.commit()
            db.refresh(budget)

        # Calculate spending in that month
        year_int, month_int = map(int, month.split("-"))
        total_spent = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.expense_date) == year_int,
            extract('month', Expense.expense_date) == month_int
        ).scalar()

        total_spent = round(float(total_spent), 2)
        remaining = max(0.0, round(budget.total_budget - total_spent, 2))
        utilization = round((total_spent / budget.total_budget * 100), 1) if budget.total_budget > 0 else 0.0

        return BudgetOut(
            id=budget.id,
            user_id=user_id,
            month=budget.month,
            total_budget=budget.total_budget,
            current_balance=budget.current_balance,
            current_spending=total_spent,
            remaining_budget=remaining,
            utilization_percentage=utilization,
            currency=budget.currency
        )

    @staticmethod
    def get_expense_summary(db: Session, user_id: int, month: str = None) -> ExpenseSummaryOut:
        if not month:
            month = datetime.date.today().strftime("%Y-%m")

        year_int, month_int = map(int, month.split("-"))
        expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            extract('year', Expense.expense_date) == year_int,
            extract('month', Expense.expense_date) == month_int
        ).all()

        total_spent = round(sum(e.amount for e in expenses), 2)
        breakdown = {}
        for e in expenses:
            breakdown[e.category] = round(breakdown.get(e.category, 0.0) + e.amount, 2)

        budget_status = ExpenseService.get_budget_status(db, user_id, month)

        return ExpenseSummaryOut(
            month=month,
            total_spent=total_spent,
            budget_limit=budget_status.total_budget,
            remaining=budget_status.remaining_budget,
            utilization_percent=budget_status.utilization_percentage,
            category_breakdown=breakdown,
            expense_count=len(expenses)
        )

    @staticmethod
    def forecast_out_of_cash(db: Session, user_id: int) -> OutOfCashForecastOut:
        current_month = datetime.date.today().strftime("%Y-%m")
        budget_status = ExpenseService.get_budget_status(db, user_id, current_month)
        summary = ExpenseService.get_expense_summary(db, user_id, current_month)

        # Days passed in current month
        day_of_month = max(1, datetime.date.today().day)
        daily_burn_rate = round(summary.total_spent / day_of_month, 2) if summary.total_spent > 0 else 150.0

        # Predict remaining days with remaining funds
        balance_to_use = budget_status.current_balance if budget_status.current_balance > 0 else budget_status.remaining_budget
        days_remaining = int(balance_to_use / daily_burn_rate) if daily_burn_rate > 0 else 30
        predicted_date = (datetime.date.today() + datetime.timedelta(days=days_remaining)).strftime("%Y-%m-%d")

        if days_remaining <= 5:
            risk_level = "HIGH"
            explanation = f"Critical budget burn! At INR {daily_burn_rate}/day, funds will be exhausted around {predicted_date}."
        elif days_remaining <= 12:
            risk_level = "MEDIUM"
            explanation = f"Moderate spending rate of INR {daily_burn_rate}/day gives approximately {days_remaining} days of runway."
        else:
            risk_level = "LOW"
            explanation = f"Financial runway is healthy (~{days_remaining} days remaining at INR {daily_burn_rate}/day)."

        return OutOfCashForecastOut(
            current_balance=balance_to_use,
            daily_burn_rate=daily_burn_rate,
            estimated_days_remaining=days_remaining,
            predicted_out_of_cash_date=predicted_date,
            financial_risk_level=risk_level,
            explanation=explanation
        )
