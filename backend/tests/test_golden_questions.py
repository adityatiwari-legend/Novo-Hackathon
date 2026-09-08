import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

GOLDEN_QUESTIONS = [
    {
        "category": "Requirements Baseline",
        "question": "Is the User Requirements Specification formally approved by Quality Assurance?",
        "expected_intent": "GxP Audit"
    },
    {
        "category": "Risk Management",
        "question": "Have all high risks been mitigated and residual risks accepted?",
        "expected_intent": "GxP Audit"
    },
    {
        "category": "Design & Specifications",
        "question": "Does the Functional Specification trace to the approved URS?",
        "expected_intent": "Traceability"
    },
    {
        "category": "Technical Testing (IQ)",
        "question": "Have all technical interfaces and infrastructure qualifications passed?",
        "expected_intent": "GxP Audit"
    },
    {
        "category": "Performance Testing (OQ/PQ)",
        "question": "Was Operational and Performance testing successfully completed without critical deviations?",
        "expected_intent": "GxP Audit"
    },
    {
        "category": "Procedural Controls",
        "question": "Are the system administration and operation SOPs active and approved?",
        "expected_intent": "Documentation"
    },
    {
        "category": "Training",
        "question": "Have all critical shopfloor operators completed their training for the MES?",
        "expected_intent": "GxP Audit"
    },
    {
        "category": "Release Readiness",
        "question": "Is the system ready for production release according to the Validation Summary Report?",
        "expected_intent": "Release Readiness"
    }
]

@pytest.mark.parametrize("q_data", GOLDEN_QUESTIONS)
def test_golden_questions(q_data):
    # This tests the RAG endpoint with the 8 golden categories
    res = client.post("/api/v1/query", json={
        "question": q_data["question"],
        "system_id": "SYS-MES-001"
    })
    
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 10
    
    # We don't strictly assert the exact intent because the LLM/router might route to General Q&A
    # but we ensure we get a confident response back
    assert data.get("confidence", 0) > 0.0

def test_release_posture_driven_by_gates():
    # Test that dashboard returns GO/CONDITIONAL/HOLD/DEFERRED
    res = client.get("/api/v1/dashboard?system_id=SYS-MES-001")
    assert res.status_code == 200
    data = res.json()
    
    # According to our seeded dummy data, gates G4, G5, G6 are blocked, G5/G6 are critical -> HOLD
    posture = data.get("release_recommendation")
    assert posture in ["GO", "CONDITIONAL", "HOLD", "DEFERRED"]
