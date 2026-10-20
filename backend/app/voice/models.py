import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Conversation(Base):
    __tablename__ = "voice_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    session_type = Column(String(50), default="IN_APP_VOICE")  # IN_APP_VOICE, PHONE_CALL
    status = Column(String(20), default="ACTIVE")              # ACTIVE, CLOSED
    context_data = Column(Text, default="{}")                  # JSON tracking current intent, last tool, subject
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)

    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMessage(Base):
    __tablename__ = "voice_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("voice_conversations.id"), index=True, nullable=False)
    role = Column(String(20), nullable=False)                  # USER, ASSISTANT, SYSTEM, TOOL
    content = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_result = Column(Text, nullable=True)                  # JSON string of tool execution result
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class VoiceCall(Base):
    __tablename__ = "voice_calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    phone_number = Column(String(50), nullable=False)
    direction = Column(String(20), default="OUTBOUND")         # OUTBOUND, INBOUND
    call_type = Column(String(50), default="PROACTIVE_INTERVENTION") # PROACTIVE_INTERVENTION, STUDY_REMINDER, WELLNESS_CHECKIN, MANUAL
    trigger_reason = Column(Text, default="")
    status = Column(String(30), default="SCHEDULED")           # SCHEDULED, QUEUED, INITIATED, RINGING, CONNECTED, IN_PROGRESS, COMPLETED, NO_ANSWER, FAILED, CANCELLED
    provider = Column(String(50), default="SIMULATED")         # SIMULATED, TWILIO
    provider_call_sid = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    transcript = Column(Text, default="[]")                    # JSON list of call dialogue turns
    outcome = Column(String(100), default="PENDING")           # COMPLETED_SUCCESSFULLY, RESCHEDULED_TASKS, NO_ANSWER, USER_DECLINED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
