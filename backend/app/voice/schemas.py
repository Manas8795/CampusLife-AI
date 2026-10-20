from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class VoiceMessageCreate(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    audio_base64: Optional[str] = None  # Optional raw audio
    persona: Optional[str] = None      # EMPATHETIC_MENTOR, PRODUCTIVITY_COACH, CAMPUS_PEER

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Any

class VoiceMessageResponse(BaseModel):
    conversation_id: int
    user_query: str
    assistant_reply: str
    intent_detected: str
    tool_executed: Optional[str] = None
    tool_data: Optional[Any] = None
    requires_confirmation: bool = False
    confirmation_action: Optional[str] = None
    audio_tts_url: Optional[str] = None
    engine: Optional[str] = "Local Student Domain LLM"
    persona: Optional[str] = "EMPATHETIC_MENTOR"
    latency_ms: Optional[float] = 0.0

class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    conversation_id: int
    role: str
    content: str
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
    created_at: datetime

class ChatHistoryOut(BaseModel):
    conversation_id: int
    session_type: str
    started_at: datetime
    last_activity: datetime
    messages: List[ChatMessageOut]
class CallInitiateRequest(BaseModel):
    phone_number: Optional[str] = None
    call_type: Optional[str] = "PROACTIVE_INTERVENTION"
    trigger_reason: Optional[str] = "Proactive academic & wellness intervention"
    provider: Optional[str] = "SIMULATED" # SIMULATED or TWILIO

class CallTurnRequest(BaseModel):
    user_speech: str

class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    phone_number: str
    direction: str
    call_type: str
    trigger_reason: str
    status: str
    provider: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int
    transcript: str
    outcome: str
    created_at: datetime

class ProactiveCheckResult(BaseModel):
    should_call: bool
    eligible_reasons: List[str]
    blocked_reasons: List[str]
    call_initiated: bool
    call_id: Optional[int] = None
    greeting_script: Optional[str] = None
