import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.infra.ml_serving import ModelRegistry
from backend.app.infra.llm_client import llm_client
from backend.app.infra.ocr_engine import OCREngine
from backend.app.infra.rag_memory import rag_memory

client = TestClient(app)
headers = {"Authorization": "Bearer user_1"}

def test_infra_model_registry_endpoint():
    res = client.get("/api/infra/models", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SERVING"
    assert data["total_models"] == 5
    assert "procrastination_predictor" in data["models"]
    assert "stress_classifier" in data["models"]
    assert "budget_forecast_model" in data["models"]
    assert "travel_cost_estimator" in data["models"]
    assert "student_compound_risk_model" in data["models"]

def test_infra_ml_serving_predictions():
    # Test model serving methods directly
    proc_pred = ModelRegistry.predict_procrastination(
        total_tasks=5,
        pending_tasks=3,
        overdue_tasks=1,
        completion_rate=0.4
    )
    assert "risk_score" in proc_pred
    assert "risk_level" in proc_pred
    assert proc_pred["risk_score"] > 0

    stress_pred = ModelRegistry.predict_stress(
        mood=2,
        sleep_hours=5.0,
        study_hours=8.0,
        energy_level=2
    )
    assert "stress_score" in stress_pred
    assert stress_pred["stress_level"] in ["LOW", "MEDIUM", "HIGH"]

    budget_pred = ModelRegistry.forecast_budget(
        monthly_budget=12000.0,
        total_spent=8500.0,
        current_balance=3500.0,
        day_of_month=18
    )
    assert "daily_burn_rate" in budget_pred
    assert "estimated_days_runway" in budget_pred

def test_infra_llm_generate_endpoint():
    res = client.post("/api/infra/llm/generate", json={
        "prompt": "Recommend a study break activity for an exhausted student",
        "temperature": 0.5
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "provider" in data
    assert len(data["output"]) > 0

def test_infra_ocr_extract_endpoint():
    receipt = """
    CAMPUS BOOKSTORE
    Receipt #9923
    Data Structures Notebook  Rs. 180
    Gel Pens Pack             Rs. 70
    TOTAL:                    INR 250.00
    Date: 2026-10-05
    """
    res = client.post("/api/infra/ocr/extract", json={
        "receipt_text": receipt
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_amount"] == 250.0
    assert data["category"] == "Education"
    assert data["lines_extracted"] > 0

def test_infra_rag_memory_endpoint():
    res = client.get("/api/infra/memory?query=exam", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "contexts" in data
    assert len(data["contexts"]) > 0
    assert "importance" in data["contexts"][0]

def test_infra_system_health():
    res = client.get("/api/infra/system/health", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["active_modules"] == 8
    assert data["ml_serving_status"] == "SERVING"

def test_all_module_html_pages():
    pages = [
        ("/", "CampusLife AI"),
        ("/study", "Study Planner"),
        ("/health", "Health & Wellness"),
        ("/expenses", "Expense & Financial Manager"),
        ("/travel", "Travel & Trip Planner"),
        ("/intelligence", "Student Intelligence Engine"),
        ("/voice", "AI Voice Assistant"),
        ("/infra", "AI/ML Infrastructure & Deployment"),
    ]
    for path, expected_title in pages:
        res = client.get(path)
        assert res.status_code == 200
        assert expected_title.lower() in res.text.lower()
