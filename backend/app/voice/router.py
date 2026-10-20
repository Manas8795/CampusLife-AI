import json
import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db, SessionLocal
from backend.app.core.router import get_current_user_id
from backend.app.config import settings
from backend.app.voice.schemas import (
    VoiceMessageCreate, VoiceMessageResponse,
    CallInitiateRequest, CallTurnRequest, CallOut,
    ProactiveCheckResult, ChatHistoryOut, ChatMessageOut
)
from backend.app.voice.service import VoiceService

router = APIRouter(prefix="/voice", tags=["AI Voice Assistant & Calling"])

@router.get("/tts")
async def stream_neural_speech_audio(
    text: str = Query("Hello! This is your CampusLife AI voice companion calling.", min_length=1),
    voice: str = Query("en-US-JennyNeural")
):
    """
    Streams high-definition neural speech MP3 audio directly for phone call playback.
    """
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    try:
        audio_bytes = await telegram_voice.generate_speech_audio(text, voice=voice)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ringtone.wav")
def get_phone_ringtone_wav():
    """
    Streams high-volume realistic dual-tone telephone ringing audio loop.
    """
    import math
    import struct
    import wave
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        sample_rate = 44100
        duration = 3.0
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            if t < 1.6:
                val = 0.5 * (math.sin(2 * math.pi * 440 * t) + math.sin(2 * math.pi * 480 * t))
                if t < 0.04:
                    val *= (t / 0.04)
                elif t > 1.56:
                    val *= ((1.6 - t) / 0.04)
            else:
                val = 0.0
            sample_val = int(val * 31000)
            samples.append(struct.pack('<h', max(-32767, min(32767, sample_val))))
        wav.writeframes(b''.join(samples))
    return Response(content=buf.getvalue(), media_type="audio/wav")

@router.get("/chat/history", response_model=ChatHistoryOut)
def get_chat_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retrieves the persistent conversation message history with the AI Assistant.
    """
    return VoiceService.get_active_conversation_history(db, user_id)

@router.delete("/chat/history")
def clear_chat_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Clears the persistent chat history for the user.
    """
    VoiceService.clear_conversation_history(db, user_id)
    return {"status": "success", "message": "Conversation history cleared."}

@router.post("/message", response_model=VoiceMessageResponse)
def voice_message(
    req: VoiceMessageCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    In-App Voice interaction turn.
    Receives user spoken query, runs intent detection and tool calling, returns conversational reply.
    """
    return VoiceService.handle_voice_message(db, user_id, req)

@router.post("/calls/initiate", response_model=CallOut)
def initiate_call(
    req: CallInitiateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Manually initiates an AI phone call (Simulated or Twilio).
    """
    return VoiceService.initiate_call(db, user_id, req)

@router.post("/calls/proactive-check", response_model=ProactiveCheckResult)
def proactive_call_check(
    ignore_quiet_hours: bool = Query(False, description="Optionally bypass quiet hours for automated test simulation"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Scans Student Intelligence (Module 6) and executes Calling Policy.
    If compound overload is detected and within allowed hours/consent, places an outbound AI call.
    """
    res = VoiceService.check_and_trigger_proactive_intervention(db, user_id, ignore_quiet_hours=ignore_quiet_hours)
    return ProactiveCheckResult(**res)

@router.post("/briefings/schedule")
def schedule_briefings(
    morning_time: str = Query("08:00", description="Morning Briefing scheduled time, e.g. 08:00"),
    morning_enabled: bool = Query(True),
    nightly_time: str = Query("22:30", description="Nightly Wind-Down scheduled time, e.g. 22:30"),
    nightly_enabled: bool = Query(True),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Schedules Morning Briefing and Nightly Wind-Down audio calls.
    """
    from backend.app.core.models import Profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
    profile.morning_briefing_time = morning_time
    profile.morning_briefing_enabled = morning_enabled
    profile.nightly_wind_down_time = nightly_time
    profile.nightly_wind_down_enabled = nightly_enabled
    db.commit()
    return {
        "status": "scheduled",
        "morning_briefing": {"time": morning_time, "enabled": morning_enabled},
        "nightly_wind_down": {"time": nightly_time, "enabled": nightly_enabled}
    }

@router.get("/briefings/morning")
def get_morning_briefing(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Synthesizes the proactive 2-minute Morning Briefing call script & details:
    'Good morning Alex. You have 2 classes today at 10 AM and 2 PM, and Operating Systems due at 5 PM.
     Your bank balance has Rs 2,400 remaining this week. Have a great day!'
    """
    import urllib.parse
    import datetime
    from backend.app.core.models import User, Profile
    from backend.app.study.models import Task
    from backend.app.expenses.models import Budget, Expense

    user = db.query(User).filter(User.id == user_id).first()
    name = user.full_name.split()[0] if (user and user.full_name) else "Alex"
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    persona = profile.vocal_persona if profile else "EMPATHETIC_MENTOR"

    tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").all()
    due_task = next((t.title for t in tasks if t.priority == "HIGH"), (tasks[0].title if tasks else "Operating Systems"))

    current_month = datetime.date.today().strftime("%Y-%m")
    budget_row = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == current_month).first()
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    monthly_expenses = [e for e in expenses if e.expense_date and str(e.expense_date).startswith(current_month)]
    total_spent = sum(e.amount for e in monthly_expenses)
    total_budget = budget_row.total_budget if budget_row else 12000.0
    remaining_balance = max(0.0, total_budget - total_spent)

    if persona == "PRODUCTIVITY_COACH":
        speech = (
            f"Rise and shine {name}! Today requires high focus. You have 2 classes at 10 AM and 2 PM, "
            f"and your critical deadline for {due_task} hits at 5 PM. Your remaining budget cushion is Rs {remaining_balance:,.0f}. "
            "Execute your study block early and let's dominate the day!"
        )
    elif persona == "CAMPUS_PEER":
        speech = (
            f"Yo {name}, morning! Just a quick heads up: you got classes at 10 AM and 2 PM, "
            f"and don't forget {due_task} is due at 5 PM today. We still got Rs {remaining_balance:,.0f} in the account for food and chai. "
            "Grab some breakfast and let's crush it!"
        )
    else: # EMPATHETIC_MENTOR
        speech = (
            f"Good morning {name}. You have 2 classes today at 10 AM and 2 PM, and {due_task} due at 5 PM. "
            f"Your bank balance has Rs {remaining_balance:,.0f} remaining this week. "
            "Take a deep breath, stay hydrated, and have a wonderful, productive day!"
        )

    return {
        "briefing_type": "MORNING_BRIEFING",
        "student_name": name,
        "persona": persona,
        "speech_text": speech,
        "audio_url": f"/voice/tts?text={urllib.parse.quote(speech)}"
    }

@router.get("/briefings/nightly")
def get_nightly_wind_down(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Synthesizes the Nightly Wind-Down call for students working late at 10:30 PM.
    """
    import urllib.parse
    from backend.app.core.models import User, Profile
    from backend.app.study.models import Task

    user = db.query(User).filter(User.id == user_id).first()
    name = user.full_name.split()[0] if (user and user.full_name) else "Alex"
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    persona = profile.vocal_persona if profile else "EMPATHETIC_MENTOR"
    sleep_target = profile.sleep_target if profile else 7.5

    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    completed = len([t for t in tasks if t.status == "COMPLETED"])

    speech = (
        f"Good evening {name}. It's 10:30 PM and you've had a demanding day with {completed} tasks marked completed. "
        f"To protect your {sleep_target:.1f}-hour sleep target and ensure peak mental sharpness tomorrow, "
        "I strongly recommend closing your laptop, doing 5 minutes of mindful breathing, and getting to sleep by 11 PM tonight. Good night!"
    )

    return {
        "briefing_type": "NIGHTLY_WIND_DOWN",
        "student_name": name,
        "persona": persona,
        "speech_text": speech,
        "audio_url": f"/voice/tts?text={urllib.parse.quote(speech)}"
    }

@router.post("/calls/{call_id}/respond")
def respond_during_call(
    call_id: int,
    req: CallTurnRequest,
    db: Session = Depends(get_db)
):
    """
    Simulates a speech turn during an ongoing phone call.
    """
    try:
        return VoiceService.process_call_speech(db, call_id, req.user_speech)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/calls/{call_id}/hangup", response_model=CallOut)
def hangup_call(
    call_id: int,
    outcome: str = Query("COMPLETED_SUCCESSFULLY"),
    db: Session = Depends(get_db)
):
    """
    Terminates the active phone call.
    """
    try:
        return VoiceService.end_call(db, call_id, outcome=outcome)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/calls/history", response_model=list[CallOut])
@router.get("/calls", response_model=list[CallOut])
@router.get("/calls/history", response_model=list[CallOut])
def get_call_history(
    limit: int = Query(15, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retrieves call history, duration, and transcripts.
    """
    return VoiceService.get_call_history(db, user_id, limit=limit)

@router.post("/calls/{call_id}/end", response_model=CallOut)
@router.post("/calls/{call_id}/hangup", response_model=CallOut)
def hangup_call_alias(
    call_id: int,
    outcome: str = Query("COMPLETED_SUCCESSFULLY"),
    db: Session = Depends(get_db)
):
    """
    Terminates the active phone call.
    """
    try:
        return VoiceService.end_call(db, call_id, outcome=outcome)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/telephony/status")
def get_telephony_status():
    """
    Fetches live Twilio and Bolna telephony status, active numbers, and verified caller IDs.
    """
    import requests
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    phone_from = settings.TWILIO_PHONE_NUMBER

    if not sid or not token:
        return {
            "configured": False,
            "provider": "SIMULATED",
            "message": "Twilio credentials not configured"
        }

    incoming_numbers = []
    verified_numbers = []
    account_status = "UNKNOWN"

    try:
        r_acc = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json", auth=(sid, token), timeout=5)
        if r_acc.status_code == 200:
            acc_data = r_acc.json()
            account_status = acc_data.get("status", "active")
            account_type = acc_data.get("type", "Trial")
        else:
            return {"configured": False, "error": "Invalid Twilio credentials"}

        r_inc = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json", auth=(sid, token), timeout=5)
        if r_inc.status_code == 200:
            incoming_numbers = [num["phone_number"] for num in r_inc.json().get("incoming_phone_numbers", [])]

        r_out = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/OutgoingCallerIds.json", auth=(sid, token), timeout=5)
        if r_out.status_code == 200:
            verified_numbers = [num["phone_number"] for num in r_out.json().get("outgoing_caller_ids", [])]

        return {
            "configured": True,
            "account_sid": sid,
            "account_status": account_status,
            "account_type": account_type,
            "twilio_phone_numbers": incoming_numbers,
            "active_caller_id": phone_from or (incoming_numbers[0] if incoming_numbers else None),
            "verified_caller_ids": verified_numbers,
            "bolna_orchestrator": "Ready",
            "local_neural_llm": settings.LOCAL_LLM_MODEL
        }
    except Exception as e:
        return {"configured": True, "error": str(e)}

@router.post("/telephony/verify-number")
def verify_phone_number(payload: dict):
    """
    Initiates phone number verification with Twilio.
    Twilio will call the phone number and read a validation code to enter, or send via SMS.
    """
    import requests
    phone_number = payload.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required (e.g. +91XXXXXXXXXX)")

    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/OutgoingCallerIds.json"
    r = requests.post(url, auth=(sid, token), data={"PhoneNumber": phone_number}, timeout=10)
    data = r.json()
    if r.status_code in (200, 201):
        return {
            "success": True,
            "phone_number": phone_number,
            "validation_code": data.get("validation_code"),
            "call_sid": data.get("call_sid"),
            "message": f"Twilio is calling {phone_number}. Enter the validation code on your phone when prompted."
        }
    else:
        return {
            "success": False,
            "error_code": data.get("code"),
            "message": data.get("message", "Verification request failed"),
            "details": data
        }

@router.post("/calls/real-phone/dial")
def dial_real_phone(payload: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    Directly initiates a live outbound call to the student's real phone number using Twilio & Bolna AI.
    """
    to_phone = payload.get("to_phone")
    from_phone = payload.get("from_phone") or settings.TWILIO_PHONE_NUMBER
    greeting = payload.get("greeting") or (
        "Hello! This is your CampusLife AI voice companion. "
        "I noticed your Operating Systems exam is approaching in three days. "
        "I am calling to check in on how you're feeling and help you prioritize your study plan."
    )

    if not to_phone:
        raise HTTPException(status_code=400, detail="to_phone is required")

    from backend.app.voice.telephony.bolna_provider import bolna_provider
    bolna_provider.twilio_phone_number = from_phone

    # Initiate call
    result = bolna_provider.initiate_call(to_number=to_phone, greeting_text=greeting)
    return result

@router.post("/webhooks/twilio")
def twilio_webhook():
    """
    TwiML webhook receiver for Twilio Voice calls.
    """
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Say voice="Polly.Aditi">Hello! This is CampusLife AI. I noticed your upcoming exam and wanted to help you organize your study tasks. Please speak after the tone.</Say>'
        '<Gather input="speech" timeout="5" action="/api/voice/webhooks/twilio" method="POST"/>'
        '</Response>'
    )
    return Response(content=twiml, media_type="application/xml")

@router.get("/telephony/bolna/config")
def get_bolna_agent_config(
    user_id: int = Depends(get_current_user_id)
):
    """
    Returns the Bolna AI Agent configuration matching https://github.com/bolna-ai/bolna schema.
    """
    from backend.app.voice.telephony.bolna_provider import bolna_provider
    return bolna_provider.create_agent_config(
        user_id=user_id,
        trigger_reason="CampusLife proactive student workload & wellness balance"
    )

@router.post("/calls/bolna/dial", response_model=CallOut)
def dial_bolna_outbound_call(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Directly initiates an outbound AI phone call powered by Bolna AI agent orchestration.
    """
    return VoiceService.initiate_call(db, user_id, CallInitiateRequest(
        call_type="PROACTIVE_INTERVENTION",
        trigger_reason="Bolna AI student co-pilot phone intervention",
        provider="BOLNA"
    ))

@router.websocket("/telephony/bolna-stream")
async def bolna_websocket_stream(websocket: WebSocket):
    """
    Bi-directional audio and event stream conforming to Bolna and Twilio Media Stream protocols.
    Streams speech audio to/from the local Ollama LLM and speech synthesizer.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data) if data.startswith("{") else {"event": "raw", "data": data}
            evt_type = event.get("event")

            if evt_type == "start":
                # Twilio / Bolna stream handshake
                await websocket.send_text(json.dumps({
                    "event": "mark",
                    "streamSid": event.get("streamSid"),
                    "status": "BOLNA_PIPELINE_ACTIVE"
                }))
            elif evt_type == "media":
                # Audio payload received
                pass
            elif evt_type == "stop":
                break
    except WebSocketDisconnect:
        pass

# ================= Telegram Voice Bot Endpoints =================

@router.get("/telegram/status")
def get_telegram_status():
    """
    Returns the current Telegram Bot connectivity, bot username, and linked Chat ID.
    """
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    tok = telegram_voice.bot_token or settings.TELEGRAM_BOT_TOKEN
    chat_id = telegram_voice.chat_id or settings.TELEGRAM_CHAT_ID

    if not tok:
        return {
            "configured": False,
            "message": "Telegram Bot Token not configured yet."
        }

    verify = telegram_voice.verify_bot(tok)
    return {
        "configured": verify.get("valid", False),
        "bot_info": verify,
        "chat_id": chat_id,
        "is_chat_linked": bool(chat_id)
    }

@router.post("/telegram/setup")
def setup_telegram_bot(payload: dict):
    """
    Configures or updates the Telegram Bot token and optional chat_id.
    """
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    bot_token = payload.get("bot_token", "").strip()
    chat_id = payload.get("chat_id", "").strip()

    if not bot_token:
        raise HTTPException(status_code=400, detail="bot_token is required")

    verify = telegram_voice.verify_bot(bot_token)
    if not verify.get("valid"):
        raise HTTPException(status_code=400, detail=f"Invalid Bot Token: {verify.get('error')}")

    telegram_voice.bot_token = bot_token
    settings.TELEGRAM_BOT_TOKEN = bot_token
    if chat_id:
        telegram_voice.chat_id = chat_id
        settings.TELEGRAM_CHAT_ID = chat_id

    return {
        "success": True,
        "bot_info": verify,
        "chat_id": telegram_voice.chat_id,
        "message": f"Successfully connected to Telegram Bot @{verify.get('username')}"
    }

@router.post("/telegram/auto-detect")
def auto_detect_telegram_chat():
    """
    Scans recent messages sent to the bot to detect the student's Chat ID automatically.
    """
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    res = telegram_voice.detect_chat_id()
    if res.get("success"):
        settings.TELEGRAM_CHAT_ID = res.get("chat_id")
    return res

@router.post("/telegram/dispatch-voice")
def dispatch_telegram_voice_call(payload: dict):
    """
    Generates high-definition neural speech audio and delivers it directly to the student's Telegram on their phone.
    """
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    text = payload.get("text") or (
        "Hello Alex! This is your CampusLife AI voice companion. "
        "I noticed your Operating Systems exam is approaching in three days, and your sleep has dropped below 6 hours. "
        "Please take 15 minutes to take a break and review your top priorities."
    )
    chat_id = payload.get("chat_id") or telegram_voice.chat_id or settings.TELEGRAM_CHAT_ID
    voice = payload.get("voice", "en-US-JennyNeural")

    if not chat_id:
        raise HTTPException(status_code=400, detail="Telegram Chat ID not found. Send /start to the bot from your phone and click Auto-Detect.")

    result = telegram_voice.send_voice_call(text=text, chat_id=chat_id, voice=voice)
    return result

# ================= Autonomous Mobile Web Calling Signaling =================

class MobileCallManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_call(self, call_payload: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(call_payload))
            except Exception:
                self.disconnect(connection)

mobile_call_manager = MobileCallManager()

@router.websocket("/call-stream/{client_id}")
async def mobile_call_stream(websocket: WebSocket, client_id: str):
    """
    Persistent bi-directional WebSocket connection with student's mobile phone.
    Enables the server to autonomously ring the phone and establish two-way voice.
    """
    await mobile_call_manager.connect(websocket)
    try:
        # Acknowledge standby mode
        await websocket.send_text(json.dumps({
            "event": "STANDBY_CONFIRMED",
            "client_id": client_id,
            "message": "Phone is armed in Standby mode. Ready for autonomous AI calls."
        }))
        while True:
            data = await websocket.receive_text()
            event = json.loads(data) if data.startswith("{") else {"event": data}
            if event.get("event") == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
    except WebSocketDisconnect:
        mobile_call_manager.disconnect(websocket)

import socket

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

CURRENT_TUNNEL_URL = "https://dbe2e99f0a18b0.lhr.life"
TUNNEL_FILE = Path(__file__).resolve().parent.parent / "tunnel_url.txt"

def get_current_tunnel_url() -> str:
    try:
        if TUNNEL_FILE.exists():
            val = TUNNEL_FILE.read_text(encoding="utf-8").strip()
            if val.startswith("http"):
                return val
    except Exception:
        pass
    return CURRENT_TUNNEL_URL

@router.get("/mobile/info")
def get_mobile_connection_info():
    """
    Returns live IP, public tunnel link, and active phone count for the Mobile Calling Station.
    """
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8000/call"
    tunnel_url = f"{get_current_tunnel_url()}/call"
    return {
        "local_ip": local_ip,
        "local_url": local_url,
        "tunnel_url": tunnel_url,
        "connected_phones": len(mobile_call_manager.active_connections),
        "telegram_bot": "@Campustempest_bot",
        "chat_id": settings.TELEGRAM_CHAT_ID or "1524191658"
    }

@router.post("/mobile/share")
async def share_mobile_link(payload: dict = None):
    """
    Sends the mobile call station link to Telegram chat so user can open it on their phone with one tap.
    """
    p = payload or {}
    chat_id = p.get("chat_id") or settings.TELEGRAM_CHAT_ID or "1524191658"
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8000/call"
    tunnel_url = f"{get_current_tunnel_url()}/call"

    from backend.app.voice.telephony.telegram_bot import telegram_voice
    
    tg_msg = (
        "📞 *CampusLife AI Phone Call Station*\n\n"
        "Open this link on your smartphone to receive live autonomous incoming calls with real ringtone, vibration, and 2-way microphone chat with Llama 3.2!\n\n"
        f"🌐 *Public Link (Works Everywhere / Mobile Data / Wi-Fi):*\n{tunnel_url}\n\n"
        f"📶 *Local Network Link:*\n{local_url}\n\n"
        "Tap the link, tap *'Arm Phone & Ring Now'*, and test talking with your AI co-pilot!"
    )

    tg_sent = False
    tg_error = None
    if telegram_voice.bot_token and chat_id:
        try:
            r = await asyncio.to_thread(telegram_voice.send_text_message, tg_msg, chat_id)
            tg_sent = bool(r.get("ok"))
            if not tg_sent:
                tg_error = r.get("error") or r.get("description")
        except Exception as e:
            tg_error = str(e)

    return {
        "success": True,
        "local_url": local_url,
        "tunnel_url": tunnel_url,
        "telegram_sent": tg_sent,
        "telegram_error": tg_error,
        "chat_id": chat_id,
        "message": "Link sent to your Telegram!" if tg_sent else "Link generated ready for phone!"
    }

@router.post("/calls/mobile-ring")
async def trigger_autonomous_mobile_ring(payload: dict = None):
    """
    Autonomously rings the student's mobile phone from the server.
    Fires the incoming call signal with ringtone & vibration to all armed standby phones,
    and sends a high-priority push link to Telegram.
    """
    p = payload or {}
    greeting = p.get("greeting") or (
        "Hello Manas! This is your CampusLife AI student voice companion calling. "
        "I noticed your Operating Systems exam is approaching in three days, and your sleep dropped below 6 hours. "
        "I am calling to help you prioritize your top study topics."
    )
    call_data = {
        "event": "INCOMING_CALL",
        "caller_name": "CampusLife Co-Pilot",
        "caller_subtitle": "Operating Systems Exam Intervention",
        "greeting": greeting,
        "call_id": f"CALL_{p.get('call_id', 'AUTO')}"
    }

    # 1. Ring all active mobile screens immediately via WebSocket
    await mobile_call_manager.broadcast_call(call_data)
    connected_count = len(mobile_call_manager.active_connections)

    # 2. Also send Telegram push alert in background without blocking
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8000/call"
    tunnel_url = f"{get_current_tunnel_url()}/call"
    from backend.app.voice.telephony.telegram_bot import telegram_voice
    chat_id = settings.TELEGRAM_CHAT_ID or "1524191658"
    if telegram_voice.bot_token and chat_id:
        tg_msg = (
            "🚨 *INCOMING AI PHONE CALL FROM CAMPUSLIFE!*\n\n"
            "Your student co-pilot is calling your phone right now!\n\n"
            f"👉 *Tap to Answer Call:*\n{tunnel_url}\n\n"
            f"Or on local Wi-Fi: {local_url}"
        )
        try:
            asyncio.create_task(asyncio.to_thread(telegram_voice.send_text_message, tg_msg, chat_id))
        except Exception:
            pass

    return {
        "success": True,
        "phones_ringing": connected_count,
        "telegram_notified": bool(chat_id),
        "local_url": local_url,
        "tunnel_url": tunnel_url,
        "message": f"Autonomous call dispatched. Ringing {connected_count} connected phone(s)!"
    }

@router.post("/demo/deadline")
def create_demo_deadline(payload: dict = None):
    """
    Sets up a real-time task with deadline in seconds_from_now (default 30s)
    to trigger autonomous call as soon as deadline passes.
    """
    import datetime
    from backend.app.database import SessionLocal
    from backend.app.study.models import Task

    p = payload or {}
    title = p.get("task_title", "Operating Systems Lab Report")
    seconds = int(p.get("seconds_from_now", 30))
    priority = p.get("priority", "HIGH")
    user_id = 1

    now = datetime.datetime.now()
    due_time = now + datetime.timedelta(seconds=seconds)

    with SessionLocal() as db:
        task = Task(
            user_id=user_id,
            title=title,
            subject="Operating Systems",
            priority=priority,
            status="PENDING",
            due_date=due_time,
            source="DEMO_DEADLINE"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Unregister from notified list so watcher can trigger call
        try:
            from backend.app.voice.deadline_watcher import deadline_watcher
            deadline_watcher.notified_task_ids.discard(task.id)
        except Exception:
            pass

        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "seconds_remaining": seconds,
            "due_date_local": str(due_time),
            "message": f"Demo deadline set for '{task.title}' in {seconds} seconds. When time expires, your phone will ring automatically!"
        }

@router.get("/deadlines/upcoming")
def get_upcoming_deadlines():
    """
    Returns list of upcoming tasks and remaining seconds for real-time mobile display.
    """
    import datetime
    from backend.app.database import SessionLocal
    from backend.app.study.models import Task

    user_id = 1
    now = datetime.datetime.now()
    with SessionLocal() as db:
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status != "COMPLETED",
            Task.due_date != None
        ).order_by(Task.due_date.asc()).limit(5).all()

        results = []
        for t in tasks:
            diff_sec = int((t.due_date - now).total_seconds())
            results.append({
                "id": t.id,
                "title": t.title,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status,
                "seconds_remaining": max(0, diff_sec),
                "is_overdue": diff_sec <= 0,
                "due_date_formatted": t.due_date.strftime("%I:%M:%S %p")
            })
        return results

@router.post("/demo/sleep-alert")
async def trigger_demo_sleep_alert(payload: dict = None):
    """
    Simulates / logs a low sleep record (< 5h) and immediately triggers the autonomous low sleep call.
    """
    p = payload or {}
    sleep_hours = float(p.get("sleep_hours", 4.5))
    user_id = 1

    with SessionLocal() as db:
        from backend.app.health.service import HealthService
        from backend.app.health.schemas import HealthLogCreate
        from backend.app.voice.deadline_watcher import deadline_watcher

        record = HealthService.log_wellness(
            db,
            user_id,
            HealthLogCreate(
                sleep_hours=sleep_hours,
                mood=2,
                energy_level=2,
                study_hours=6.5,
                notes="Late night exam prep, sleep deficit"
            )
        )
        deadline_watcher.notified_sleep_record_ids.discard(record.id)

        greeting = (
            f"Hello! CampusLife Health Sentinel detected your sleep was only {sleep_hours} hours. "
            f"Your cognitive recovery is critically low. Let's adjust your study schedule today so you can wind down and sleep early tonight."
        )
        call_payload = {
            "event": "INCOMING_CALL",
            "call_type": "LOW_SLEEP",
            "caller_name": "CampusLife Health Sentinel",
            "caller_subtitle": f"🌙 Critical Sleep Deficit: {sleep_hours}h",
            "sleep_hours": sleep_hours,
            "preview_text": f"Sleep Alert: Only {sleep_hours} hours recorded. Tap Accept Call to adjust your recovery plan.",
            "greeting": greeting,
            "call_id": f"DEMO_SLEEP_{record.id}"
        }
        await mobile_call_manager.broadcast_call(call_payload)

        return {
            "success": True,
            "record_id": record.id,
            "sleep_hours": sleep_hours,
            "message": f"Autonomous low sleep call ({sleep_hours}h) dispatched to active phone!"
        }

@router.post("/demo/health-alert")
async def trigger_demo_health_alert(payload: dict = None):
    """
    Simulates / logs a depreciating health & high stress record and triggers the autonomous health call.
    """
    user_id = 1
    with SessionLocal() as db:
        from backend.app.health.service import HealthService
        from backend.app.health.schemas import HealthLogCreate
        from backend.app.voice.deadline_watcher import deadline_watcher

        record = HealthService.log_wellness(
            db,
            user_id,
            HealthLogCreate(
                sleep_hours=5.0,
                mood=1,
                energy_level=1,
                study_hours=8.0,
                notes="Severe academic burnout and depreciating vitals"
            )
        )
        deadline_watcher.notified_health_record_ids.discard(record.id)

        greeting = (
            "Hello! Your wellness telemetry indicates your physical and mental energy are critically depleted with high stress. "
            "Please pause what you are doing, take a 15-minute breather, and let's reschedule non-urgent deadlines to protect your health."
        )
        call_payload = {
            "event": "INCOMING_CALL",
            "call_type": "HEALTH_DEPRECIATION",
            "caller_name": "CampusLife Wellness Sentinel",
            "caller_subtitle": "⚠️ Health Depreciating: High Stress",
            "preview_text": "Wellness Warning: High fatigue and stress detected. Tap Accept Call to protect your recovery.",
            "greeting": greeting,
            "call_id": f"DEMO_HEALTH_{record.id}"
        }
        await mobile_call_manager.broadcast_call(call_payload)

        return {
            "success": True,
            "record_id": record.id,
            "stress_level": record.stress_level,
            "message": "Autonomous health depreciation call dispatched to active phone!"
        }


