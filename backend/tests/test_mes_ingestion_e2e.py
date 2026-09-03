import pytest
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, SessionLocal
from backend.app.models import (
    System, Document, DocumentChunk, Requirement, Risk,
    verify_audit_chain
)
from backend.app.services.traceability_engine import traceability_engine
from backend.app.services.release_gate_engine import release_gate_engine
from backend.app.services.consistency_service import consistency_service
from backend.app.services.rag_service import rag_service

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_mes_system_seeded(db: Session):
    sys = db.query(System).filter(System.id == "SYS-MES-001").first()
    assert sys is not None, "SYS-MES-001 must exist in the database"
    assert sys.name == "Novo Life MES PAS-X"
    assert "Category 4" in sys.description or "Configured Software" in sys.description
    assert sys.release_recommendation == "HOLD / DEFER - DO NOT RELEASE"
    assert sys.lifecycle_status == "PRE-OPERATIONAL / NOT ACTIVATED"

def test_all_10_lifecycle_documents_ingested(db: Session):
    docs = db.query(Document).filter(Document.system_id == "SYS-MES-001").all()
    assert len(docs) >= 10, f"Expected at least 10 documents, found {len(docs)}"
    
    doc_titles = {d.title for d in docs}
    expected_ids = [
        "NL-MES-MLGP-001",
        "NL-MES-URS-001",
        "NL-MES-FS-001",
        "NL-MES-ITRA-001",
        "NL-MES-ITRRA-001",
        "NL-MES-SUPA-001",
        "NL-MES-OMSOP-001",
        "NL-MES-SLA-001",
        "NL-MES-ITPSE-001",
        "NL-MES-IREP-001",
    ]
    for eid in expected_ids:
        assert any(eid in title for title in doc_titles), f"Document {eid} not found in database titles: {doc_titles}"

def test_50_urs_requirements_extracted(db: Session):
    reqs = db.query(Requirement).filter(Requirement.system_id == "SYS-MES-001").all()
    assert len(reqs) == 50, f"Expected exactly 50 URS requirements, found {len(reqs)}"
    
    # Check functional vs non-functional distribution
    functional = [r for r in reqs if "FUNCTIONAL" in r.type.upper() and "NON" not in r.type.upper()]
    non_functional = [r for r in reqs if "NON" in r.type.upper()]
    assert len(functional) == 25, f"Expected 25 functional, found {len(functional)}"
    assert len(non_functional) == 25, f"Expected 25 non-functional, found {len(non_functional)}"

def test_26_system_risks_extracted(db: Session):
    risks = db.query(Risk).filter(Risk.system_id == "SYS-MES-001").all()
    assert len(risks) == 26, f"Expected 26 system risks RSK-MES-001..RSK-MES-026, found {len(risks)}"

def test_traceability_matrix_coverage_and_gaps(db: Session):
    matrix = traceability_engine.build_traceability_matrix(db, "SYS-MES-001")
    gaps = traceability_engine.detect_traceability_gaps(db, "SYS-MES-001")
    
    assert len(matrix) == 50
    unverified = [m for m in matrix if m["verification_status"] == "NOT_PERFORMED"]
    assert len(unverified) >= 47  # At least 47 unverified
    
    assert len(gaps) >= 2
    gap_codes = {g["gap_code"] for g in gaps}
    assert "GAP-TRC-001" in gap_codes
    assert "GAP-TRC-002" in gap_codes

def test_release_gate_engine_evaluates_hold(db: Session):
    gate_report = release_gate_engine.evaluate_release_gates(db, "SYS-MES-001")
    assert gate_report is not None
    assert gate_report["overall_decision"] == "HOLD / DEFER - DO NOT RELEASE"
    assert gate_report["lifecycle_status"] == "PRE-OPERATIONAL / NOT ACTIVATED"
    
    # Verify Gate G5 is NOT MET
    gates_by_code = {g["gate_code"]: g for g in gate_report["gates"]}
    assert "G5" in gates_by_code
    assert gates_by_code["G5"]["status"] in ["NOT MET", "NOT_MET", "BLOCKED"]
    
    # Verify Gate G6 is NOT MET
    assert "G6" in gates_by_code
    assert gates_by_code["G6"]["status"] in ["NOT MET", "NOT_MET", "BLOCKED"]
    
    # Check blocking rationale
    assert len(gate_report["blocking_reasons"]) >= 2

def test_cross_document_consistency_aligned(db: Session):
    consistency = consistency_service.check_consistency(db, "SYS-MES-001")
    assert consistency is not None
    assert consistency["consistency_status"] == "CONSISTENT"
    assert len(consistency["consistent_checks"]) >= 3

def test_rag_grounded_answer_and_citations(db: Session):
    rag_res = rag_service.query("What is blocking the release of MES PAS-X?", system_id="SYS-MES-001")
    assert rag_res is not None
    answer = rag_res.answer
    assert "HOLD" in answer or "DEFER" in answer or "Gate G5" in answer or "PRE-OPERATIONAL" in answer
    
    # Assert structured citations are returned
    citations = rag_res.citations
    assert len(citations) > 0, "RAG response should return grounded citations"
    
    # Verify citation format [DocumentID | p.X | Section]
    for cite in citations:
        assert "[" in cite and "]" in cite
        assert "NL-MES-" in cite or "NL-MES" in cite

def test_tamper_evident_audit_trail_integrity(db: Session):
    is_valid, records_checked, msg = verify_audit_chain(db)
    assert is_valid is True, f"Audit chain verification failed: {msg}"
    assert records_checked > 0, "Expected checked audit records"
