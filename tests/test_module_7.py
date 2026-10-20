import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
headers = {"Authorization": "Bearer user_1"}

def test_voice_message_get_tasks():
    res = client.post("/api/voice/message", json={
        "message": "What assignments or tasks do I have due?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_TASKS"
    assert data["tool_executed"] == "get_tasks"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_create_task():
    res = client.post("/api/voice/message", json={
        "message": "Add task to revise virtual memory"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "CREATE_TASK"
    assert data["tool_executed"] == "create_task"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_wellness_and_sleep():
    res = client.post("/api/voice/message", json={
        "message": "How is my sleep and stress level looking?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_WELLNESS"
    assert data["tool_executed"] == "get_wellness_state"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_finances():
    res = client.post("/api/voice/message", json={
        "message": "How much money have I spent this month and what is my budget runway?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_FINANCES"
    assert data["tool_executed"] == "get_expenses_summary"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_trips():
    res = client.post("/api/voice/message", json={
        "message": "Tell me about my upcoming vacation trip"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_TRIPS"
    assert data["tool_executed"] == "get_upcoming_trips"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_student_intelligence():
    res = client.post("/api/voice/message", json={
        "message": "How am I doing overall? What is my student co-pilot status?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_INTELLIGENCE"
    assert data["tool_executed"] == "get_student_intelligence"
    assert len(data["assistant_reply"]) > 10

def test_voice_message_schedule():
    res = client.post("/api/voice/message", json={
        "message": "What is my schedule for today?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["intent_detected"] == "GET_SCHEDULE"
    assert data["tool_executed"] == "get_student_schedule"
    assert len(data["assistant_reply"]) > 20

def test_proactive_call_trigger_and_conversation():
    # Clean up any recent calls to test fresh cooldown window
    from backend.app.database import SessionLocal
    from backend.app.voice.models import VoiceCall
    with SessionLocal() as db:
        db.query(VoiceCall).filter(VoiceCall.user_id == 1).delete()
        db.commit()

    # 1. Proactive check at night verifies that Quiet Hours is enforced!
    res_night = client.post("/api/voice/calls/proactive-check", headers=headers)
    assert res_night.status_code == 200
    night_data = res_night.json()
    # At 23:00+ it correctly detects quiet hours
    if not night_data["should_call"]:
        assert any("QUIET_HOURS" in b for b in night_data["blocked_reasons"])

    # 2. Proactive check with quiet hours override initiates outbound AI call
    with SessionLocal() as db:
        db.query(VoiceCall).filter(VoiceCall.user_id == 1).delete()
        db.commit()

    res_check = client.post("/api/voice/calls/proactive-check?ignore_quiet_hours=true", headers=headers)
    assert res_check.status_code == 200
    check_data = res_check.json()
    assert check_data["should_call"] is True
    assert check_data["call_initiated"] is True
    call_id = check_data["call_id"]
    assert call_id is not None
    assert "campuslife" in check_data["greeting_script"].lower()

    # 3. Student speaks during the phone call
    res_turn = client.post(f"/api/voice/calls/{call_id}/respond", json={
        "user_speech": "Yes, can you tell me what my top priority task is?"
    })
    assert res_turn.status_code == 200
    turn_data = res_turn.json()
    assert turn_data["call_id"] == call_id
    assert turn_data["status"] == "IN_PROGRESS"
    assert len(turn_data["assistant_reply"]) > 0

    # 4. Terminate call
    res_hangup = client.post(f"/api/voice/calls/{call_id}/hangup?outcome=USER_RESCHEDULED_TASKS")
    assert res_hangup.status_code == 200
    call_out = res_hangup.json()
    assert call_out["status"] == "COMPLETED"
    assert call_out["outcome"] == "USER_RESCHEDULED_TASKS"

    # 5. Check Call History
    res_hist = client.get("/api/voice/calls/history", headers=headers)
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 1
    assert any(c["id"] == call_id for c in history)

def test_twilio_webhook_endpoint():
    res = client.post("/api/voice/webhooks/twilio")
    assert res.status_code == 200
    assert "Response" in res.text
    assert "Say" in res.text
    assert "Gather" in res.text

def test_local_student_llm_personas():
    personas = ["EMPATHETIC_MENTOR", "PRODUCTIVITY_COACH", "CAMPUS_PEER"]
    for p in personas:
        res = client.post("/api/voice/message", json={
            "message": "What tasks do I have due?",
            "persona": p
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["persona"] == p
        assert "engine" in data
        assert len(data["assistant_reply"]) > 10

def test_bolna_ai_telephony_agent_integration():
    # 1. Fetch Bolna Agent pipeline config
    res_cfg = client.get("/api/voice/telephony/bolna/config", headers=headers)
    assert res_cfg.status_code == 200
    cfg = res_cfg.json()
    assert "agent_id" in cfg
    assert "https://github.com/bolna-ai/bolna" in cfg["repository"]
    assert cfg["agent_type"] == "outbound_phone"
    assert len(cfg["tasks"]) > 0

    # 2. Dispatch outbound call via Bolna
    res_dial = client.post("/api/voice/calls/bolna/dial", headers=headers)
    assert res_dial.status_code == 200
    call_data = res_dial.json()
    assert call_data["provider"] == "BOLNA_AI"
    assert call_data["status"] == "INITIATED"
    call_id = call_data["id"]

    # 3. Respond in speech turn
    res_turn = client.post(f"/api/voice/calls/{call_id}/respond", json={
        "user_speech": "Can you check my upcoming deadlines?"
    })
    assert res_turn.status_code == 200
    turn_res = res_turn.json()
    assert len(turn_res["assistant_reply"]) > 0

    # 4. Hang up
    res_end = client.post(f"/api/voice/calls/{call_id}/hangup?outcome=COMPLETED_SUCCESSFULLY")
    assert res_end.status_code == 200
    assert res_end.json()["status"] == "COMPLETED"


