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

def test_system_a_seed_state(db):
    system = db.query(System).filter(System.id == "SYS-LIMS-001").first()
    assert system is not None
    assert system.criticality == "GxP-Critical"
    assert system.gxp_status == "GxP"
    
    docs = db.query(Document).filter(Document.system_id == "SYS-LIMS-001").all()
    assert len(docs) >= 4
    doc_titles = [d.title for d in docs]
    assert "System_A_URS.docx" in doc_titles
    assert "System_A_Risk_Assessment.docx" in doc_titles
    assert "SOP_Change_Control.docx" in doc_titles
    assert "SOP_Document_Management.docx" in doc_titles

def test_deterministic_readiness_score(db):
    eval_res = compliance_engine.evaluate_system(db, "SYS-LIMS-001")
    # Must be exactly 82%
    assert eval_res["readiness_score"] == 82
    assert eval_res["failed_checks"] == 3
    
    # 1 High risk finding (QA approval missing) and 2 medium findings
    severities = [f["severity"] for f in eval_res["findings"]]
    assert severities.count("HIGH") == 1
    assert severities.count("MEDIUM") == 2

def test_rag_query_with_grounded_citations(db):
    res = rag_service.query("Is System A audit ready?", system_id="SYS-LIMS-001")
    assert res.confidence >= 0.90
    assert len(res.sources) > 0
    assert "82%" in res.answer
    
    # Negative test / hallucination guardrail: approval date
    res_date = rag_service.query("What is the approval date?", system_id="SYS-LIMS-001")
    assert "could not be found" in res_date.answer.lower()
    assert res_date.confidence < 0.70  # Low confidence

def test_tamper_evident_audit_chain_integrity(db):
    is_valid, count, msg = verify_audit_chain(db)
    assert is_valid is True
    assert count > 0

def test_human_approval_workflow_lifecycle(db):
    # 1. Create approval-gated workflow
    wf = Workflow(
        type="APPROVAL_GATE",
        system_id="SYS-LIMS-001",
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
        system_id="SYS-LIMS-001"
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
        system_id="SYS-LIMS-001",
        system_name="Validated LIMS",
        readiness_score=82,
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
    # Trigger simulation
    sim_res = continuous_monitor.trigger_document_expiration_event(db, "SYS-LIMS-001")
    assert sim_res["previous_readiness"] == 82
    assert sim_res["new_readiness"] == 76  # 82 -> 76 drop!
    
    # Reset simulation back to 82%
    reset_res = continuous_monitor.reset_simulation(db, "SYS-LIMS-001")
    assert reset_res["readiness_score"] == 82
