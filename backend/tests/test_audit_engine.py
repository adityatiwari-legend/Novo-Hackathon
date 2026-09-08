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
    # Check that some expected PAS-X documents exist
    assert any("User Requirement Specification" in t for t in doc_titles)
    assert any("IT Risk Assessment" in t for t in doc_titles)
    assert any("IT Implementation Report" in t for t in doc_titles)
    
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
    assert any("NL-MES-" in cite for cite in q_items["DA-09-001"].evidence_citations), q_items["DA-09-001"].evidence_citations
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
    # 1. Ask about system description
    sys_res = rag_service.query("What is the description of the MES system?", system_id="SYS-MES-001", mode="GxP Audit")
    assert "UNKNOWN / NOT EVIDENCED" in sys_res.answer or len(sys_res.citations) > 0

    # 2. Top 25 Audit execution query - Top 25 might not be in docs, so we expect missing or fallback
    run_res = rag_service.query("Run the top 25 audit checklist against MES PAS-X", system_id="SYS-MES-001", mode="GxP Audit")
    assert "UNKNOWN / NOT EVIDENCED" in run_res.answer or "OFFLINE EVIDENCE SUMMARY" in run_res.answer or "NOT EVIDENCED" in run_res.answer

    # 3. Master SOP comparison query
    sop_res = rag_service.query("Compare PAS-X against the master lifecycle SOP", system_id="SYS-MES-001", mode="GxP Audit")
    assert "UNKNOWN / NOT EVIDENCED" in sop_res.answer or "OFFLINE EVIDENCE SUMMARY" in sop_res.answer or "NOT EVIDENCED" in sop_res.answer

def test_temporal_regression_with_real_documents():
    from backend.app.models.entities import Document, EvidenceItem
    from backend.app.services.temporal_service import get_applicable_evidence
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    # Create two documents: an old one and a new one
    old_doc_id = "DOC-TEMP-OLD"
    new_doc_id = "DOC-TEMP-NEW"
    
    past_date = datetime.now() - timedelta(days=365)
    recent_date = datetime.now() - timedelta(days=10)
    future_date = datetime.now() + timedelta(days=365)
    
    old_doc = Document(
        id=old_doc_id,
        title="Old SOP",
        system_id="SYS-MES-001",
        effective_from=past_date,
        effective_to=recent_date,
        document_type="SOP"
    )
    new_doc = Document(
        id=new_doc_id,
        title="New SOP",
        system_id="SYS-MES-001",
        effective_from=recent_date,
        effective_to=future_date,
        document_type="SOP"
    )
    db.add(old_doc)
    db.add(new_doc)
    
    # Add evidence items to map to documents
    db.add(EvidenceItem(document_id=old_doc_id, text="Old evidence", status="APPROVED"))
    db.add(EvidenceItem(document_id=new_doc_id, text="New evidence", status="APPROVED"))
    db.commit()
    
    try:
        # Test 1: Query during old doc's validity
        old_target = past_date + timedelta(days=10)
        old_evidence = get_applicable_evidence(db, "SYS-MES-001", old_target)
        old_doc_ids = {e.document_id for e in old_evidence}
        assert old_doc_id in old_doc_ids
        assert new_doc_id not in old_doc_ids
        
        # Test 2: Query during new doc's validity
        new_target = recent_date + timedelta(days=10)
        new_evidence = get_applicable_evidence(db, "SYS-MES-001", new_target)
        new_doc_ids = {e.document_id for e in new_evidence}
        assert new_doc_id in new_doc_ids
        assert old_doc_id not in new_doc_ids
        
        # Test 3: Query far in the future
        far_future = future_date + timedelta(days=100)
        future_evidence = get_applicable_evidence(db, "SYS-MES-001", far_future)
        future_doc_ids = {e.document_id for e in future_evidence}
        assert new_doc_id not in future_doc_ids
        assert old_doc_id not in future_doc_ids
        
        # Also test RAG service fallback when querying out of bounds
        future_res = rag_service.query("What was the status of MES on 15 March 2050?", system_id="SYS-MES-001")
        assert "UNKNOWN" in future_res.answer or "NOT EVIDENCED" in future_res.answer or future_res.confidence < 0.9
        
    finally:
        # Cleanup
        db.query(EvidenceItem).filter(EvidenceItem.document_id.in_([old_doc_id, new_doc_id])).delete()
        db.query(Document).filter(Document.id.in_([old_doc_id, new_doc_id])).delete()
        db.commit()
        db.close()
