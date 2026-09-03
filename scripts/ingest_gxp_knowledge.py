"""
Ingestion script for Additional GxP Knowledge Sources:
1. NN_Master_IT_System_Lifecycle_SOP.pdf (HACK-IT-SOP-001)
2. 01_GxP_LIMS_Lifecycle_Documentation_Package_v0.1.pdf (LIMS-LCP-001)
3. Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx (CKL-TOP25-2026 & CKL-TOP25-CORE)

Parses metadata, sections, page numbers, Excel rows/sheets, populates AuditChecklist and
AuditQuestion entities, indexes chunks into the vector store, and creates cryptographic audit logs.
"""

import os
import sys

# Ensure workspace root is in sys.path
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.entities import (
    Document, DocumentChunk, System, AuditChecklist, AuditQuestion,
    create_audit_log, verify_audit_chain
)
from backend.app.services.document_parser import parse_document
from backend.app.services.vector_store import vector_store
from backend.app.services.audit_engine import audit_engine, CORE_25_AUDIT_SPECS

TARGET_FILES = [
    {
        "path": os.path.join(WORKSPACE_DIR, "NN_Master_IT_System_Lifecycle_SOP.pdf"),
        "system_id": "GOV-SOP",
        "doc_type": "SOP",
        "description": "Master IT System Lifecycle and Audit Readiness Governance SOP"
    },
    {
        "path": os.path.join(WORKSPACE_DIR, "01_GxP_LIMS_Lifecycle_Documentation_Package_v0.1.pdf"),
        "system_id": "SYS-LIMS-001",
        "doc_type": "LIFECYCLE_PACKAGE",
        "description": "GxP LIMS Lifecycle Documentation Package (Benchmark Reference)"
    },
    {
        "path": os.path.join(WORKSPACE_DIR, "Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx"),
        "system_id": "SYS-MES-001",
        "doc_type": "AUDIT_CHECKLIST",
        "description": "Top 25 Checklists GxP IT Audit Questions 2026 (Executable Instrument)"
    }
]

def ingest_additional_gxp_sources():
    db = SessionLocal()
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    print("============================================================")
    print("Ingesting Additional GxP Knowledge Sources (SOP, LIMS, Top 25 XLSX)")
    print("============================================================")

    # 1. Ensure Reference Systems exist
    lims_sys = db.query(System).filter(System.id == "SYS-LIMS-001").first()
    if not lims_sys:
        lims_sys = System(
            id="SYS-LIMS-001",
            name="Validated GxP LIMS (System B)",
            description="Laboratory Information Management System (Benchmark Reference Knowledge Source).",
            criticality="GxP-Critical",
            gxp_status="GxP",
            business_owner="Quality Control Operations",
            lifecycle_status="OPERATIONAL",
            release_recommendation="RELEASED / VALIDATED",
            readiness_score=88,
            last_assessed_at=datetime.now(timezone.utc)
        )
        db.add(lims_sys)
        db.commit()
        print("  [+] Registered Reference System: Validated GxP LIMS (SYS-LIMS-001)")

    vector_chunks_to_add = []

    for file_info in TARGET_FILES:
        fpath = file_info["path"]
        if not os.path.exists(fpath):
            print(f"  [!] Warning: Target file not found at {fpath}. Skipping.")
            continue

        filename = os.path.basename(fpath)
        print(f"\nProcessing {filename}...")

        parsed = parse_document(fpath, system_id=file_info["system_id"])
        print(f"  -> Extracted ID: {parsed.document_id} | Title: {parsed.title} | Version: {parsed.version}")
        print(f"  -> Generated {len(parsed.chunks)} chunks | Sections: {len(parsed.sections)}")

        # Upsert Document entity
        doc_record = db.query(Document).filter(
            (Document.checksum == parsed.checksum) | (Document.title == parsed.title) | (Document.file_path == fpath)
        ).first()

        if not doc_record:
            doc_record = Document(
                title=parsed.title,
                document_type=parsed.document_type,
                system_id=file_info["system_id"],
                version=parsed.version,
                owner_id=parsed.owner,
                status=parsed.approval_status,
                review_date=parsed.review_date,
                approval_status=parsed.approval_status,
                source_system="Corporate Quality Management System",
                file_path=fpath,
                checksum=parsed.checksum,
                metadata_json={
                    "document_id": parsed.document_id,
                    "sections_count": len(parsed.sections),
                    "classification": getattr(parsed, "classification", "Internal Use")
                }
            )
            db.add(doc_record)
        else:
            doc_record.title = parsed.title
            doc_record.document_type = parsed.document_type
            doc_record.version = parsed.version
            doc_record.status = parsed.approval_status
            doc_record.approval_status = parsed.approval_status
            doc_record.checksum = parsed.checksum
            doc_record.file_path = fpath
            doc_record.review_date = parsed.review_date

        db.commit()
        db.refresh(doc_record)

        # Clear old chunks for this document in database
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
                "document_title": parsed.title,
                "system_id": file_info["system_id"],
                "content": ch.content,
                "page_number": ch.page_number,
                "section": ch.section,
                "metadata": ch.metadata
            })
        db.commit()
        print(f"  [+] Ingested {len(parsed.chunks)} document chunks for {filename}")

        # 2. If this is the Excel Audit Checklist, populate AuditChecklist and AuditQuestion
        if parsed.structured_audit_questions:
            print(f"  [+] Populating Audit Checklist database with {len(parsed.structured_audit_questions)} questions...")
            
            # Master Checklist
            master_chk = db.query(AuditChecklist).filter(AuditChecklist.id == "CKL-TOP25-2026").first()
            if not master_chk:
                master_chk = AuditChecklist(
                    id="CKL-TOP25-2026",
                    title="Top 25 Checklists GxP IT Audit Questions (Master 2026)",
                    version="2026.1",
                    source_file=filename,
                    description="Comprehensive Master GxP IT Difficult-Auditor Questions across all 14 lifecycle phases."
                )
                db.add(master_chk)
                db.commit()

            # Core 25 Checklist
            core_chk = db.query(AuditChecklist).filter(AuditChecklist.id == "CKL-TOP25-CORE").first()
            if not core_chk:
                core_chk = AuditChecklist(
                    id="CKL-TOP25-CORE",
                    title="Top 25 Difficult-Auditor GxP IT Audit Questions (Core 2026)",
                    version="2026.1",
                    source_file=filename,
                    description="Curated primary Top 25 Audit Checklist covering critical lifecycle gates for MES PAS-X."
                )
                db.add(core_chk)
                db.commit()

            # Insert / update questions
            core_q_ids = set([s["q_id"] for s in CORE_25_AUDIT_SPECS])
            seen_q_ids = set()
            for q_data in parsed.structured_audit_questions:
                q_id = q_data["id"]
                if q_id in seen_q_ids:
                    continue
                seen_q_ids.add(q_id)

                existing_q = db.query(AuditQuestion).filter(AuditQuestion.id == q_id).first()
                if not existing_q:
                    q_model = AuditQuestion(
                        id=q_id,
                        checklist_id="CKL-TOP25-CORE" if q_id in core_q_ids else "CKL-TOP25-2026",
                        sequence=q_data["sequence"],
                        phase_no=q_data["phase_no"],
                        lifecycle_phase=q_data["lifecycle_phase"],
                        audit_domain=q_data["audit_domain"],
                        control_topic=q_data["control_topic"],
                        priority=q_data["priority"],
                        audit_question=q_data["audit_question"],
                        follow_up_probe=q_data["follow_up_probe"],
                        audit_rationale=q_data["audit_rationale"],
                        expected_evidence=q_data["expected_evidence"],
                        sampling_triangulation=q_data["sampling_triangulation"],
                        primary_roles=q_data["primary_roles"],
                        regulatory_alignment=q_data["regulatory_alignment"],
                        source_urls=q_data["source_urls"],
                        red_flags=q_data["red_flags"],
                        sheet_name=q_data["sheet_name"],
                        row_number=q_data["row_number"],
                        weight=q_data["weight"]
                    )
                    db.add(q_model)
            db.commit()
            print(f"  [+] Stored {len(seen_q_ids)} unique AuditQuestion records.")

        # Record tamper-evident audit log
        create_audit_log(
            db=db,
            actor_type="AGENT",
            actor_id="gxp_knowledge_ingestion_service",
            action="DOCUMENT_INGESTED",
            entity_type="DOCUMENT",
            entity_id=doc_record.id,
            details={"title": parsed.title, "document_id": parsed.document_id, "chunks": len(parsed.chunks)},
            agent_name="document_parser"
        )

    # 3. Add chunks to vector store
    if vector_chunks_to_add:
        print(f"\nIndexing {len(vector_chunks_to_add)} chunks into Hybrid Vector Store...")
        vector_store.add_chunks(vector_chunks_to_add)
        vector_store.save()
        print("  [+] Vector store index updated and saved.")

    # 4. Execute Top 25 Audit against MES PAS-X
    print("\nExecuting initial Top 25 Audit assessment against Novo Life MES PAS-X (SYS-MES-001)...")
    assessment_res = audit_engine.execute_audit(db, "SYS-MES-001", "CKL-TOP25-CORE")
    print(f"  [+] Audit Readiness Score: {assessment_res.readiness_score}%")
    print(f"  [+] Passed: {assessment_res.passed_count} | Partial: {assessment_res.partial_count} | Failed: {assessment_res.failed_count}")
    print(f"  [+] Critical Findings: {assessment_res.critical_findings_count}")

    # 5. Cryptographic chain verification
    is_valid, records_checked, msg = verify_audit_chain(db)
    print(f"\nAudit Chain Verification: {msg} (Checked: {records_checked}, Valid: {is_valid})")
    print("============================================================")
    print("GxP Knowledge Ingestion & Audit Engine Setup Completed!")
    print("============================================================")
    db.close()

if __name__ == "__main__":
    ingest_additional_gxp_sources()
