import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_create_assessment_and_poll():
    # 1. Create assessment
    res = client.post("/api/v1/assessments", json={"query": "Potomac River near Great Falls"})
    assert res.status_code == 202
    data = res.json()
    assert "run_id" in data
    assert data["status"] == "pending"
    
    run_id = data["run_id"]
    
    # 2. Check status (may be pending or completed synchronously depending on test execution)
    status_res = client.get(f"/api/v1/assessments/{run_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["run_id"] == run_id
    assert status_data["status"] in ("pending", "completed", "failed", "needs_clarification")
