import os
os.environ["DATABASE_URL"] = "sqlite:///./test_prove.db"
os.environ["LLM_MODE"] = "mock"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
PAYLOAD = {"target_role":"Junior Data Analyst","target_domain":"Data Analytics","claimed_skills":["Python","SQL","Excel","Data Analysis"],"experience":"During my internship I cleaned 20,000 rows in Excel, wrote SQL queries, and created a dashboard.","project_description":"Sales data dashboard","evidence":[{"name":"GitHub Repository","type":"github","url":"https://github.com/example/proof"}],"outcome":"Identified declining product categories.","ai_usage":"AI-assisted"}

def test_analyze_maps_skills_and_scores():
    response = client.post("/api/proof/analyze", json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    statuses = {item["skill"]: item["status"] for item in data["skills"]}
    assert statuses["SQL"] == "Proven"
    assert statuses["Python"] == "Claimed"
    assert 0 <= data["evidence_quality"]["overall"] <= 1

def test_numeric_claim_is_guarded():
    payload = PAYLOAD | {"outcome":"Improved conversion by 40%."}
    data = client.post("/api/proof/analyze", json=payload).json()
    assert data["claim_checks"][0]["status"] == "unsupported"
    assert all("40%" not in outcome for outcome in data["artifact"]["outcome"])

def test_build_persists_and_gets():
    built = client.post("/api/proof/build", json=PAYLOAD)
    assert built.status_code == 200
    stored = client.get(f"/api/proof/{built.json()['id']}")
    assert stored.status_code == 200
    assert stored.json()["input"]["target_role"] == "Junior Data Analyst"

def test_input_validation():
    response = client.post("/api/proof/analyze", json={})
    assert response.status_code == 422
