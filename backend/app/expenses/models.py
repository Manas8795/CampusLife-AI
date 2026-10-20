import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from backend.app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    category = Column(String(50), default="Food") # Food, Transport, Education, Shopping, Entertainment, Accommodation, Travel, Bills, Other
    merchant = Column(String(255), default="Unknown")
    description = Column(Text, default="")
    expense_date = Column(Date, default=datetime.date.today, index=True)
    payment_method = Column(String(50), default="UPI")
    source = Column(String(50), default="MANUAL") # MANUAL, OCR_RECEIPT
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    file_path = Column(String(500), nullable=True)
    ocr_text = Column(Text, default="")
    parsed_json = Column(Text, default="{}") # JSON containing extracted merchant, amount, category, items
    status = Column(String(50), default="PROCESSED") # UPLOADED, PROCESSED, CONFIRMED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    month = Column(String(7), nullable=False) # e.g. "2026-10"
    total_budget = Column(Float, default=10000.0)
    current_balance = Column(Float, default=5000.0)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
