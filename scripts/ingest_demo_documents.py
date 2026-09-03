"""
Ingestion script for authentic fictional "Novo Life MES PAS-X" dummy lifecycle documents.
Parses, classifies, extracts metadata, requirements, risks, gates, builds vector chunks,
and populates the database with SHA-256 audit ledger records.
"""

import os
import sys
import glob
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.entities import (
    User, System, Document, DocumentChunk, Requirement, TraceabilityLink, ReleaseGate,
    ComplianceCheck, ComplianceFinding, Risk, Recommendation, EvidencePack, Workflow, AuditLog,
    create_audit_log, verify_audit_chain
)
from backend.app.services.document_parser import parse_document
from backend.app.services.vector_store import vector_store
from backend.app.services.compliance_engine import compliance_engine
from backend.app.services.release_gate_engine import release_gate_engine
from backend.app.services.traceability_engine import traceability_engine
from backend.app.agents.evidence_agent import audit_evidence_agent

def ingest_all_lifecycle_documents():
    db = SessionLocal()
    print("============================================================")
    print("Ingesting Authentic Novo Life MES PAS-X Dummy Lifecycle Docs")
    print("============================================================")

    # 1. Ensure System SYS-MES-001 exists
    mes_sys = db.query(System).filter(System.id == "SYS-MES-001").first()
    if not mes_sys:
        mes_sys = System(
            id="SYS-MES-001",
            name="Novo Life MES PAS-X",
            description=(
                "Fictional Werum PAS-X Manufacturing Execution System (MES) implementation "
                "for commercial packaging line execution (GAMP 5 Category 4 Configured Software). "
                "Currently in Pre-Operational / Not Activated state."
            ),
            criticality="GxP-Critical",
            gxp_status="GxP",
            business_owner="Sarah Jenkins",
            lifecycle_status="PRE-OPERATIONAL / NOT ACTIVATED",
            release_recommendation="HOLD / DEFER - DO NOT RELEASE",
            readiness_score=48,
            last_assessed_at=datetime.now(timezone.utc)
        )
        db.add(mes_sys)
        db.commit()
        print("  [+] Registered System: Novo Life MES PAS-X (SYS-MES-001)")

    # 2. Locate documents in data/sample_documents
    doc_files = glob.glob(os.path.join(settings.SAMPLE_DOCS_DIR, "NL-MES-*.docx"))
    if not doc_files:
        print("  [!] No NL-MES documents found. Generating them first...")
        from scripts.create_mes_lifecycle_documents import generate_all_mes_documents
        generate_all_mes_documents()
        doc_files = glob.glob(os.path.join(settings.SAMPLE_DOCS_DIR, "NL-MES-*.docx"))

    vector_chunks_to_add = []

    for file_path in doc_files:
        filename = os.path.basename(file_path)
        print(f"\nProcessing {filename}...")

        parsed = parse_document(file_path, system_id="SYS-MES-001")
        
        # Check if already in DB
        existing_doc = db.query(Document).filter(Document.title == filename).first()
        if existing_doc:
            doc_record = existing_doc
            doc_record.document_type = parsed.document_type
            doc_record.version = parsed.version
            doc_record.status = parsed.approval_status
            doc_record.approval_status = parsed.approval_status
            doc_record.checksum = parsed.checksum
            doc_record.review_date = parsed.review_date
            doc_record.file_path = file_path
        else:
            doc_record = Document(
                title=filename,
                document_type=parsed.document_type,
                system_id="SYS-MES-001",
                version=parsed.version,
                owner_id=parsed.owner,
                status=parsed.approval_status,
                review_date=parsed.review_date,
                approval_status=parsed.approval_status,
                source_system="Veeva Vault Quality (Simulated)",
                file_path=file_path,
                checksum=parsed.checksum,
                metadata_json={"document_id": parsed.document_id, "sections_count": len(parsed.sections)}
            )
            db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # Clear existing chunks for this doc
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_record.id).delete()
        db.commit()

        # Insert chunks
        for ch in parsed.chunks:
            chunk_rec = DocumentChunk(
                document_id=doc_record.id,
                chunk_index=ch.chunk_index,
                content=ch.content,
                page_number=ch.page_number,
                section=ch.section,
                metadata_json=ch.metadata
            )
            db.add(chunk_rec)
            vector_chunks_to_add.append({
                "id": chunk_rec.id,
                "document_id": parsed.document_id,
                "document_title": filename,
                "system_id": "SYS-MES-001",
                "content": ch.content,
                "page_number": ch.page_number,
                "section": ch.section,
                "metadata": ch.metadata
            })
        db.commit()
        print(f"  [+] Ingested {len(parsed.chunks)} vector chunks for {filename}")

        # Ingest Requirements if extracted
        if parsed.extracted_requirements:
            print(f"  [+] Extracting {len(parsed.extracted_requirements)} URS requirements...")
            for req in parsed.extracted_requirements:
                existing_req = db.query(Requirement).filter(
                    Requirement.system_id == "SYS-MES-001",
                    Requirement.requirement_id == req["requirement_id"]
                ).first()
                if not existing_req:
                    db.add(Requirement(
                        requirement_id=req["requirement_id"],
                        system_id="SYS-MES-001",
                        document_id=doc_record.title,
                        text=req["text"],
                        type=req["type"],
                        source_page=req["source_page"],
                        source_section=req["source_section"],
                        risk_reference=req["risk_reference"],
                        verification_reference=req["verification_reference"],
                        status=req["status"]
                    ))
                    # Link to Traceability
                    db.add(TraceabilityLink(
                        system_id="SYS-MES-001",
                        requirement_id=req["requirement_id"],
                        fs_id=f"FS-MOD-{req['requirement_id'][-3:]}",
                        risk_id=req["risk_reference"],
                        test_id=f"TP-MES-{req['requirement_id'][-3:]}",
                        test_status="COMPLETE" if req["requirement_id"] in ["URS-009", "URS-010", "URS-030"] else "NOT_PERFORMED",
                        implementation_status="COMPLETE" if req["requirement_id"] in ["URS-009", "URS-010", "URS-030"] else "NOT_MET"
                    ))
            db.commit()

        # Ingest Risks if extracted
        if parsed.extracted_risks:
            print(f"  [+] Extracting {len(parsed.extracted_risks)} system risks...")
            for rk in parsed.extracted_risks:
                existing_rk = db.query(Risk).filter(
                    Risk.system_id == "SYS-MES-001",
                    Risk.id == rk["id"]
                ).first()
                if not existing_rk:
                    db.add(Risk(
                        id=rk["id"],
                        system_id="SYS-MES-001",
                        risk_level=rk["risk_level"],
                        impact_type=rk["impact_type"],
                        likelihood=rk["likelihood"],
                        impact=rk["impact"],
                        score=rk["score"],
                        rationale=rk["rationale"],
                        control_mapping=rk["control_mapping"]
                    ))
            db.commit()

        # Ingest Gates if extracted
        if parsed.extracted_gates:
            print(f"  [+] Extracting {len(parsed.extracted_gates)} lifecycle phase gates...")
            for g in parsed.extracted_gates:
                existing_g = db.query(ReleaseGate).filter(
                    ReleaseGate.system_id == "SYS-MES-001",
                    ReleaseGate.gate_code == g["gate_code"]
                ).first()
                if not existing_g:
                    db.add(ReleaseGate(
                        system_id="SYS-MES-001",
                        gate_code=g["gate_code"],
                        gate_name=g["gate_name"],
                        status=g["status"],
                        evidence_doc=g["evidence_doc"],
                        evidence_section=g["evidence_section"],
                        blocking_reason=g["blocking_reason"],
                        prerequisites="Refer to NL-MES-MLGP-001 section 3"
                    ))
            db.commit()

        create_audit_log(
            db=db,
            actor_type="AGENT",
            actor_id="document_ingestion_service",
            action="DOCUMENT_INGESTED",
            entity_type="DOCUMENT",
            entity_id=doc_record.id,
            details={"title": filename, "checksum": parsed.checksum, "chunks": len(parsed.chunks)},
            agent_name="document_parser"
        )

    # 3. Add chunks to vector index
    if vector_chunks_to_add:
        print(f"\nIndexing {len(vector_chunks_to_add)} chunks into Hybrid Vector Store...")
        vector_store.add_chunks(vector_chunks_to_add)
        vector_store.save()

    # 4. Evaluate Compliance Rules
    print("\nRunning deterministic compliance rules evaluation...")
    eval_res = compliance_engine.evaluate_system(db, "SYS-MES-001")
    score = eval_res["readiness_score"]
    print(f"  [+] Calculated Deterministic Readiness Score: {score}%")
    print(f"  [+] Release Recommendation: {eval_res['release_recommendation']}")
    print(f"  [+] Active Findings: {len(eval_res['findings'])}")

    # Clear old findings for this system and add new ones
    db.query(ComplianceFinding).filter(ComplianceFinding.system_id == "SYS-MES-001").delete()
    db.commit()
    for f in eval_res["findings"]:
        db.add(f)
    db.commit()

    # 5. Populate Recommendations
    db.query(Recommendation).filter(Recommendation.system_id == "SYS-MES-001").delete()
    db.commit()
    recs = [
        Recommendation(
            system_id="SYS-MES-001",
            source_agent="recommendation_agent",
            title="Execute Intended-Use Verification (OV / PfV / UAT)",
            description="Complete intended-use qualification test scripts on the shopfloor to resolve the critical verification gap blocking Gate G5.",
            priority="CRITICAL",
            rationale="NL-MES-IREP-001 Section 3.2 records operational verification as NOT PERFORMED.",
            suggested_owner="Sarah Jenkins",
            status="PROPOSED",
            confidence=0.98
        ),
        Recommendation(
            system_id="SYS-MES-001",
            source_agent="recommendation_agent",
            title="Conduct Authorized Residual Risk Acceptance Review",
            description="Route 49 working high requirements through authorized residual risk evaluation with the Quality Unit to unblock Gate G5.",
            priority="CRITICAL",
            rationale="NL-MES-ITRRA-001 indicates residual risk is NOT RATED across all working high requirements.",
            suggested_owner="Dr. Elena Rostova",
            status="PROPOSED",
            confidence=0.97
        ),
        Recommendation(
            system_id="SYS-MES-001",
            source_agent="recommendation_agent",
            title="Complete Shopfloor Training & Operational SLA Handover",
            description="Qualify shopfloor packaging operators (0 of 250 trained) and activate operational SLA tiers to satisfy Gate G6.",
            priority="HIGH",
            rationale="NL-MES-SLA-001 is currently in PRE-OPERATIONAL / NOT ACTIVATED state.",
            suggested_owner="Henrik Lindqvist",
            status="PROPOSED",
            confidence=0.95
        )
    ]
    for r in recs:
        db.add(r)
    db.commit()

    # 6. Seed Pending Workflow
    db.query(Workflow).filter(Workflow.system_id == "SYS-MES-001").delete()
    db.commit()
    wf = Workflow(
        type="APPROVAL_GATE",
        system_id="SYS-MES-001",
        recommendation_id=recs[0].id,
        status="PENDING_APPROVAL",
        requires_approval=True,
        payload_json={
            "recommendation_title": recs[0].title,
            "priority": "CRITICAL",
            "justification": "Required to unblock release gate G5 and resolve unperformed operational verification."
        }
    )
    db.add(wf)
    db.commit()

    # 7. Generate Initial Evidence Pack
    print("\nCompiling initial Audit Evidence Dossier...")
    pack_res = audit_evidence_agent.execute(db, "SYS-MES-001")
    print(f"  [+] {pack_res.metadata.get('summary', 'Evidence pack generated successfully.')}")

    # 8. Cryptographic Chain Verification
    is_valid, records_checked, msg = verify_audit_chain(db)
    print(f"\nAudit Chain Verification: {msg} (Checked: {records_checked}, Valid: {is_valid})")
    print("============================================================")
    print("Ingestion & Seeding for Novo Life MES PAS-X Completed Successfully!")
    print("============================================================")
    db.close()

if __name__ == "__main__":
    ingest_all_lifecycle_documents()
