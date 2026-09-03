import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.entities import Document, DocumentChunk, AuditChecklist, AuditQuestion
from backend.app.services.audit_engine import audit_engine
from backend.app.services.audit_report_service import audit_report_service
from backend.app.services.rag_service import rag_service

def test_gxp_knowledge_documents_ingested():
    db = SessionLocal()
    docs = db.query(Document).all()
    doc_titles = [d.title for d in docs]
    
    # Check that the 3 new knowledge sources exist
    assert any("Manage IT System Lifecycle" in t or "HACK-IT-SOP-001" in str(d.metadata_json) for d, t in zip(docs, doc_titles))
    assert any("GxP LIMS" in t or "LIMS-LCP-001" in str(d.metadata_json) for d, t in zip(docs, doc_titles))
    assert any("Top 25" in t or "CKL-TOP25-2026" in str(d.metadata_json) for d, t in zip(docs, doc_titles))
    
    # Check that questions are stored in AuditQuestion table
    q_count = db.query(AuditQuestion).count()
    assert q_count >= 25
    db.close()

def test_deterministic_audit_execution():
    db = SessionLocal()
    assessment = audit_engine.execute_audit(db, "SYS-MES-001", "CKL-TOP25-CORE")
    assert assessment.total_questions == 25
    assert assessment.readiness_score > 0
    assert assessment.passed_count > 0
    assert assessment.failed_count > 0
    assert assessment.critical_findings_count >= 3
    
    # Check question 7 or intended-use verification question status
    q_items = {item.question_id: item for item in assessment.items}
    # Verify DA-09-001 or DA-03-005 failed
    assert "DA-09-001" in q_items
    assert q_items["DA-09-001"].status == "FAIL"
    assert q_items["DA-09-001"].risk_level == "CRITICAL"
    assert any("NL-MES-IREP-001" in cite for cite in q_items["DA-09-001"].evidence_citations)
    db.close()

def test_cross_document_comparison():
    db = SessionLocal()
    comparison = audit_engine.cross_document_comparison(db, "SYS-MES-001")
    assert comparison.total_compared >= 4
    assert comparison.deviations_count >= 2
    assert comparison.aligned_count >= 2
    
    # Verify deviation has SOP and MES citations
    dev_item = [it for it in comparison.items if it.alignment_status == "POTENTIAL_LIFECYCLE_DEVIATION"][0]
    assert any("HACK-IT-SOP-001" in c for c in dev_item.sop_citations)
    assert any("NL-MES-" in c for c in dev_item.mes_citations)
    db.close()

def test_rag_audit_queries():
    # 1. Question 7 failure reasoning
    q7_res = rag_service.query("Why did question 7 fail?", system_id="SYS-MES-001", mode="GxP Audit")
    assert "Assessment:" in q7_res.answer
    assert "FAIL" in q7_res.answer
    assert "NL-MES-IREP-001" in q7_res.answer
    assert "Gate G5" in q7_res.answer

    # 2. Top 25 Audit execution query
    run_res = rag_service.query("Run the top 25 audit checklist against MES PAS-X", system_id="SYS-MES-001", mode="GxP Audit")
    assert "Total Questions: 25" in run_res.answer
    assert "Passed:" in run_res.answer
    assert "Critical Findings:" in run_res.answer

    # 3. Master SOP comparison query
    sop_res = rag_service.query("Compare PAS-X against the master lifecycle SOP", system_id="SYS-MES-001", mode="GxP Audit")
    assert "POTENTIAL LIFECYCLE DEVIATION" in sop_res.answer
    assert "HACK-IT-SOP-001" in sop_res.answer
