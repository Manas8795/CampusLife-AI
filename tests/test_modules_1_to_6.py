import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.tools.campuslife_tools import (
    get_tasks, create_task, complete_task, get_wellness_state,
    get_expenses_summary, get_upcoming_trips, get_student_intelligence
)

client = TestClient(app)

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert "CampusLife AI" in res.text

    res_status = client.get("/api/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["project"] == "CampusLife AI"
    assert len(data["active_modules"]) >= 6

    res2 = client.get("/healthz")
    assert res2.status_code == 200
    assert res2.json() == {"status": "healthy"}

def test_module_1_core_and_auth():
    # Login with seeded user
    res = client.post("/api/auth/login", json={
        "email": "alex@campuslife.ai",
        "password": "campuslife123"
    })
    assert res.status_code == 200
    token_data = res.json()
    assert token_data["email"] == "alex@campuslife.ai"
    assert token_data["user_id"] == 1
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get User profile
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["full_name"] == "Alex Sharma"

    # Get Preferences
    res_prefs = client.get("/api/users/me/preferences", headers=headers)
    assert res_prefs.status_code == 200
    assert res_prefs.json()["voice_calls_enabled"] is True

    # Quick Add
    res_qa = client.post("/api/quick-add/task", json={
        "title": "Quick Task: Read chapter 5",
        "priority": "HIGH"
    }, headers=headers)
    assert res_qa.status_code == 200
    assert res_qa.json()["status"] == "success"

    # Dashboard
    res_dash = client.get("/api/dashboard", headers=headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert dash_data["student_name"] == "Alex Sharma"
    assert "study" in dash_data
    assert "health" in dash_data
    assert "expenses" in dash_data
    assert "intelligence" in dash_data

def test_module_2_study_planner():
    headers = {"Authorization": "Bearer user_1"}

    # Get Tasks
    res = client.get("/api/study/tasks", headers=headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) >= 5

    # Create new task
    res_create = client.post("/api/study/tasks", json={
        "title": "Study Cryptography Basics",
        "subject": "Cybersecurity",
        "priority": "HIGH",
        "status": "PENDING"
    }, headers=headers)
    assert res_create.status_code == 200
    new_task = res_create.json()
    assert new_task["title"] == "Study Cryptography Basics"

    # Complete task
    res_comp = client.post(f"/api/study/tasks/{new_task['id']}/complete", headers=headers)
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "COMPLETED"

    # Productivity Delay Risk
    res_risk = client.get("/api/study/productivity/risk", headers=headers)
    assert res_risk.status_code == 200
    risk_data = res_risk.json()
    assert "risk_level" in risk_data
    assert "reason_codes" in risk_data

def test_module_3_health_wellness():
    headers = {"Authorization": "Bearer user_1"}

    # Wellness summary
    res_summary = client.get("/api/health/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert "average_sleep_7d" in summary
    assert summary["sleep_status"] in ["HEALTHY", "BELOW_BASELINE"]

    # Stress prediction
    res_stress = client.get("/api/health/stress/predict", headers=headers)
    assert res_stress.status_code == 200
    stress_data = res_stress.json()
    assert stress_data["stress_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(stress_data["signals"]) > 0

    # Wellness recommendation
    res_rec = client.post("/api/health/recommendations", json={"type": "MINDFULNESS"}, headers=headers)
    assert res_rec.status_code == 200
    assert "4-7-8 Breathing" in res_rec.json()["title"]

def test_module_4_expense_manager():
    headers = {"Authorization": "Bearer user_1"}

    # List expenses
    res = client.get("/api/expenses", headers=headers)
    assert res.status_code == 200
    expenses = res.json()
    assert len(expenses) >= 4

    # Budget summary
    res_summary = client.get("/api/expenses/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_spent"] > 0
    assert "Food" in summary["category_breakdown"]

    # Out of cash forecast
    res_fc = client.get("/api/expenses/forecast", headers=headers)
    assert res_fc.status_code == 200
    fc = res_fc.json()
    assert fc["daily_burn_rate"] > 0
    assert "financial_risk_level" in fc

    # Receipt upload simulation
    res_ocr = client.post("/api/expenses/receipts/upload", json={
        "raw_ocr_simulation": "CAMPUS BOOKSTORE\nDatabase Systems Textbook - 650\nTotal: 650"
    }, headers=headers)
    assert res_ocr.status_code == 200
    rec_data = res_ocr.json()
    assert rec_data["parsed_json"]["category"] == "Education"

def test_module_5_travel_planner():
    headers = {"Authorization": "Bearer user_1"}

    # Get Trips
    res = client.get("/api/travel/trips", headers=headers)
    assert res.status_code == 200
    trips = res.json()
    assert len(trips) >= 1
    trip_id = trips[0]["id"]

    # Generate Itinerary
    res_itin = client.post(f"/api/travel/trips/{trip_id}/itinerary/generate", json={
        "preferred_pace": "RELAXED",
        "interests": ["Beaches", "Seafood"]
    }, headers=headers)
    assert res_itin.status_code == 200
    assert res_itin.json()["status"] == "CONFIRMED"

    # Budget Estimate
    res_budget = client.get(f"/api/travel/trips/{trip_id}/budget", headers=headers)
    assert res_budget.status_code == 200
    assert res_budget.json()["estimated_total"] > 0

    # Academic Conflicts
    res_conflict = client.get(f"/api/travel/trips/{trip_id}/conflicts", headers=headers)
    assert res_conflict.status_code == 200
    conf_data = res_conflict.json()
    assert conf_data["has_conflict"] is True
    assert conf_data["conflict_count"] > 0

def test_module_6_student_intelligence():
    headers = {"Authorization": "Bearer user_1"}

    # Unified Student State
    res_state = client.get("/api/intelligence/state", headers=headers)
    assert res_state.status_code == 200
    state = res_state.json()
    assert state["compound_risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(state["baselines"]) >= 3
    assert len(state["detected_risks"]) >= 1
    assert len(state["priority_insights"]) >= 1

    # Proactive call recommendation evaluated for student scenario
    assert isinstance(state["proactive_intervention_recommended"], bool)

def test_module_7_and_8_tool_interfaces():
    # Directly test the tools designed for Module 7's Voice Assistant
    user_id = 1

    tasks = get_tasks(user_id)
    assert len(tasks) > 0

    new_task = create_task(user_id, "Voice: Review Chapter 2", priority="HIGH")
    assert new_task["status"] == "success"

    wellness = get_wellness_state(user_id)
    assert "average_sleep_7d" in wellness
    assert "current_stress_level" in wellness

    finances = get_expenses_summary(user_id)
    assert finances["total_spent"] > 0

    trips = get_upcoming_trips(user_id)
    assert len(trips) > 0
    assert trips[0]["has_academic_conflict"] is True

    intel = get_student_intelligence(user_id)
    assert intel["compound_risk_level"] in ["HIGH", "MEDIUM", "LOW"]
    assert isinstance(intel["proactive_intervention_recommended"], bool)
    assert isinstance(intel["proactive_call_permitted"], bool)
