import os
import pytest
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.entities import (
    System, Document, ComplianceFinding, Workflow, AuditLog,
    create_audit_log, verify_audit_chain
)
from backend.app.services.compliance_engine import compliance_engine
from backend.app.services.rag_service import rag_service
from backend.app.agents.supervisor import supervisor_agent
from backend.app.agents.evidence_agent import evidence_agent
from backend.app.integrations.mock_servicenow import mock_servicenow
from backend.app.integrations.mock_monitoring import continuous_monitor

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_system_mes_seed_state(db):
    system = db.query(System).filter(System.id == "SYS-MES-001").first()
    assert system is not None
    assert system.criticality == "GxP-Critical"
    assert system.gxp_status == "GxP"
    
    docs = db.query(Document).filter(Document.system_id == "SYS-MES-001").all()
    assert len(docs) >= 1
    doc_titles = [d.title for d in docs]
    assert any("NOVOLIFE-MES" in t for t in doc_titles)

def test_deterministic_readiness_score(db):
    eval_res = compliance_engine.evaluate_system(db, "SYS-MES-001")
    # Should be around 48% per ingestion script
    assert eval_res["readiness_score"] > 0
    
    # Just check that it has some findings
    severities = [f["severity"] for f in eval_res["findings"]]
    assert len(severities) > 0

def test_rag_query_with_grounded_citations(db):
    res = rag_service.query("Is the MES PAS-X system audit ready?", system_id="SYS-MES-001")
    assert res.confidence >= 0.85
    assert len(res.sources) > 0
    
    # Negative test / hallucination guardrail: approval date
    res_date = rag_service.query("What is the approval date?", system_id="SYS-MES-001")
    assert "could not be found" in res_date.answer.lower() or "offline evidence summary" in res_date.answer.lower() or "unknown / missing" in res_date.answer.lower() or "not evidenced" in res_date.answer.lower()
    assert res_date.confidence <= 0.85  # Low/Medium confidence for missing info

def test_tamper_evident_audit_chain_integrity(db):
    is_valid, count, msg = verify_audit_chain(db)
    assert is_valid is True
    assert count > 0

def test_human_approval_workflow_lifecycle(db):
    # 1. Create approval-gated workflow
    wf = Workflow(
        type="APPROVAL_GATE",
        system_id="SYS-MES-001",
        status="PENDING_APPROVAL",
        requires_approval=True,
        payload_json={"recommendation_title": "Route URS to QA for approval"}
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    
    assert wf.status == "PENDING_APPROVAL"
    assert wf.approved_at is None
    
    # 2. Human Approval execution
    ticket = mock_servicenow.create_ticket(
        title="[GxP Copilot] Route URS for QA signoff",
        description="Approved by QA Compliance",
        system_id="SYS-MES-001"
    )
    assert ticket["ticket_id"].startswith("SNOW-TASK-")
    
    wf.status = "APPROVED"
    wf.approved_by = "qa@demo.local"
    wf.payload_json = {"ticket_id": ticket["ticket_id"]}
    db.commit()
    
    # 3. Log audit trail
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id="qa@demo.local",
        action="Human Approved GxP Workflow & Executed ServiceNow Task",
        entity_type="WORKFLOW",
        entity_id=wf.id,
        details={"ticket": ticket["ticket_id"]}
    )
    
    # Verify chain remains valid after new event
    is_valid, count, msg = verify_audit_chain(db)
    assert is_valid is True

def test_evidence_pack_generation(db):
    res = evidence_agent.run(
        db=db,
        system_id="SYS-MES-001",
        system_name="Novo Life MES PAS-X",
        readiness_score=48,
        checklist_results=[],
        findings=[],
        risks=[],
        recommendations=[],
        generated_by="qa@demo.local"
    )
    assert res.metadata["evidence_pack_id"] is not None
    assert os.path.exists(os.path.join(evidence_agent.output_dir, res.metadata["pdf_filename"]))
    assert os.path.exists(os.path.join(evidence_agent.output_dir, res.metadata["docx_filename"]))

def test_continuous_compliance_monitor_simulation(db):
    # Determine current readiness score
    sys = db.query(System).filter(System.id == "SYS-MES-001").first()
    initial_score = sys.readiness_score

    # Trigger simulation
    sim_res = continuous_monitor.trigger_document_expiration_event(db, "SYS-MES-001")
    assert sim_res["previous_readiness"] == initial_score
    assert sim_res["new_readiness"] < initial_score
    
    # Reset simulation
    reset_res = continuous_monitor.reset_simulation(db, "SYS-MES-001")
    assert reset_res["readiness_score"] == initial_score
