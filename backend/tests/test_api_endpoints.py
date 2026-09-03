import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_root_and_health(client):
    r1 = client.get("/")
    assert r1.status_code == 200
    assert "Novo Nordisk" in r1.json()["company"]
    
    r2 = client.get("/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "Healthy"

def test_dashboard_endpoint(client):
    # Test SYS-LIMS-001
    r_lims = client.get("/api/v1/dashboard?system_id=SYS-LIMS-001")
    assert r_lims.status_code == 200
    data_lims = r_lims.json()
    assert data_lims["system_id"] == "SYS-LIMS-001"
    assert data_lims["readiness_score"] == 82
    assert data_lims["open_findings"] >= 3
    
    # Test SYS-MES-001
    r_mes = client.get("/api/v1/dashboard?system_id=SYS-MES-001")
    assert r_mes.status_code == 200
    data_mes = r_mes.json()
    assert data_mes["system_id"] == "SYS-MES-001"
    assert data_mes["release_recommendation"] == "HOLD / DEFER - DO NOT RELEASE"

def test_documents_endpoint(client):
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    docs = r.json()
    assert len(docs) >= 10

def test_rag_query_endpoint(client):
    r = client.post("/api/v1/query", json={"question": "Is System A audit ready?", "system_id": "SYS-LIMS-001"})
    assert r.status_code == 200
    data = r.json()
    assert "82%" in data["answer"]
    assert data["confidence"] >= 0.90
    assert len(data["sources"]) > 0

def test_audit_log_verify_endpoint(client):
    r = client.get("/api/v1/audit-log/verify")
    assert r.status_code == 200
    data = r.json()
    assert data["is_valid"] is True
    assert data["records_checked"] > 0

def test_agents_health_endpoint(client):
    r = client.get("/api/v1/agents/health")
    assert r.status_code == 200
    data = r.json()
    assert len(data["active_agents"]) >= 6
    assert len(data["enterprise_stubs"]) == 5
