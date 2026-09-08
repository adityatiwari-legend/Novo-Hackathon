"""
Canonical Ingestion Script for Novo Life MES PAS-X (Phase 1).
Reads documents, extracts true metadata, creates EvidenceItems, and valid Relationships.
Idempotent processing based on checksums.
"""

import os
import glob
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.entities import (
    System, Document, DocumentChunk, Requirement, Risk, ReleaseGate, Relationship,
    EvidenceItem, ComplianceFinding, Recommendation, Workflow, create_audit_log, verify_audit_chain
)
from backend.app.services.document_parser import parse_document
from backend.app.services.vector_store import vector_store
from backend.app.services.date_parser import parse_date

def get_dt(date_str):
    res = parse_date(date_str)
    return res["parsed"] if res else None

def ingest_pasx_documents():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("============================================================")
    print("Ingesting Canonical Novo Life MES PAS-X Documents (Phase 1)")
    print("============================================================")

    system_id = "SYS-MES-001"
    mes_sys = db.query(System).filter(System.id == system_id).first()
    if not mes_sys:
        mes_sys = System(
            id=system_id,
            name="Novo Life MES PAS-X",
            description=(
                "Fictional Werum PAS-X Manufacturing Execution System (MES) implementation "
                "for commercial packaging line execution (GAMP 5 Category 4 Configured Software)."
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
        print(f"  [+] Registered Canonical System: {system_id}")

    pasx_dir = os.path.join(settings.DATA_DIR, "pasx_documents")
    doc_files = glob.glob(os.path.join(pasx_dir, "NOVOLIFE-MES-*.docx"))
    if not doc_files:
        print("  [!] No NOVOLIFE-MES documents found in data/pasx_documents. Please extract them first.")
        return

    vector_chunks_to_add = []

    for file_path in doc_files:
        filename = os.path.basename(file_path)
        print(f"\nProcessing {filename}...")
        
        parsed = parse_document(file_path, system_id=system_id)
        
        # Check idempotency
        existing_doc = db.query(Document).filter(Document.title == filename, Document.system_id == system_id).first()
        if existing_doc and existing_doc.checksum == parsed.checksum:
            print(f"  [-] Skipping {filename} (Checksum unchanged: {parsed.checksum})")
            continue
            
        if existing_doc:
            print(f"  [~] Updating {filename}...")
            doc_record = existing_doc
            doc_record.document_type = parsed.document_type
            doc_record.version = parsed.version
            doc_record.status = parsed.approval_status
            doc_record.approval_status = parsed.approval_status
            doc_record.checksum = parsed.checksum
            doc_record.review_date = parsed.review_date
            doc_record.effective_from = get_dt(parsed.effective_from)
            doc_record.effective_to = get_dt(parsed.effective_to)
            doc_record.issue_date = get_dt(parsed.issue_date)
            doc_record.review_due = get_dt(parsed.review_due)
            doc_record.owner = parsed.owner
            doc_record.owner_id = parsed.owner
            doc_record.approver = parsed.approver
            doc_record.file_path = file_path
        else:
            print(f"  [+] Inserting {filename}...")
            doc_record = Document(
                title=filename,
                document_id=parsed.document_id,
                document_type=parsed.document_type,
                system_id=system_id,
                version=parsed.version,
                owner=parsed.owner,
                owner_id=parsed.owner,
                approver=parsed.approver,
                status=parsed.approval_status,
                review_date=parsed.review_date,
                approval_status=parsed.approval_status,
                effective_from=get_dt(parsed.effective_from),
                effective_to=get_dt(parsed.effective_to),
                issue_date=get_dt(parsed.issue_date),
                review_due=get_dt(parsed.review_due),
                source_system="Veeva Vault Quality (Simulated)",
                source_filename=filename,
                file_path=file_path,
                checksum=parsed.checksum,
                metadata_json={"sections_count": len(parsed.sections)}
            )
            db.add(doc_record)
        
        db.commit()
        db.refresh(doc_record)
        
        # Remove old chunks/evidence/entities for this doc
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_record.id).delete()
        db.query(EvidenceItem).filter(EvidenceItem.document_id == doc_record.id).delete()
        db.query(Requirement).filter(Requirement.source_document_id == doc_record.id).delete()
        db.query(Risk).filter(Risk.source_document_id == doc_record.id).delete()
        db.query(ReleaseGate).filter(ReleaseGate.source_document_id == doc_record.id).delete()
        db.query(Relationship).filter(Relationship.source_document_id == doc_record.id).delete()
        db.commit()

        # Insert Document Chunks & Evidence Items
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
            db.flush()
            
            # Create a corresponding EvidenceItem (1-1 with chunk for this simple ingestion)
            ev = EvidenceItem(
                evidence_id=f"EV-{doc_record.document_id}-{ch.chunk_index}",
                document_id=doc_record.id,
                locator=f"Page {ch.page_number} / {ch.section}",
                section=ch.section,
                page=ch.page_number,
                text=ch.content,
                evidence_type="TEXT_CHUNK",
                status="VERIFIED",
                source_version=parsed.version,
                effective_from=get_dt(parsed.effective_from),
                effective_to=get_dt(parsed.effective_to),
                extracted_by="ingest_pasx"
            )
            db.add(ev)
            
            vector_chunks_to_add.append({
                "id": chunk_rec.id,
                "document_id": parsed.document_id,
                "document_title": filename,
                "system_id": system_id,
                "content": ch.content,
                "page_number": ch.page_number,
                "section": ch.section,
                "metadata": ch.metadata
            })
            
        db.commit()
        print(f"  [+] Ingested {len(parsed.chunks)} chunks & evidence items")
        
        # Requirements
        if parsed.extracted_requirements:
            for req in parsed.extracted_requirements:
                db.add(Requirement(
                    requirement_id=req["requirement_id"],
                    system_id=system_id,
                    document_id=doc_record.document_id,
                    source_document_id=doc_record.id,
                    text=req["text"],
                    type=req["type"],
                    source_page=req["source_page"],
                    source_section=req["source_section"],
                    status=req["status"]
                ))
            db.commit()
            print(f"  [+] Ingested {len(parsed.extracted_requirements)} Requirements")

        # Risks
        if parsed.extracted_risks:
            for rk in parsed.extracted_risks:
                existing_risk = db.query(Risk).filter(Risk.id == rk["id"], Risk.system_id == system_id).first()
                if not existing_risk:
                    db.add(Risk(
                        id=rk["id"],
                        system_id=system_id,
                        source_document_id=doc_record.id,
                        risk_level=rk["risk_level"],
                        impact_type=rk["impact_type"],
                        likelihood=rk["likelihood"],
                        impact=rk["impact"],
                        score=rk["score"],
                        rationale=rk["rationale"],
                        control_mapping=rk.get("control_mapping")
                    ))
                else:
                    existing_risk.control_mapping = rk.get("control_mapping") or existing_risk.control_mapping
                    
            db.commit()
            print(f"  [+] Ingested {len(parsed.extracted_risks)} Risks")

        # Gates
        if parsed.extracted_gates:
            for g in parsed.extracted_gates:
                db.add(ReleaseGate(
                    system_id=system_id,
                    source_document_id=doc_record.id,
                    gate_code=g["gate_code"],
                    gate_name=g["gate_name"],
                    status=g["status"],
                    evidence_doc=g["evidence_doc"],
                    evidence_section=g["evidence_section"],
                    blocking_reason=g["blocking_reason"]
                ))
            db.commit()
            print(f"  [+] Ingested {len(parsed.extracted_gates)} Gates")
            
        create_audit_log(
            db=db,
            actor_type="AGENT",
            actor_id="document_ingestion_service",
            action="DOCUMENT_INGESTED",
            entity_type="DOCUMENT",
            entity_id=doc_record.id,
            details={"title": filename, "checksum": parsed.checksum},
            agent_name="ingest_pasx"
        )
        
    if vector_chunks_to_add:
        print(f"\nIndexing {len(vector_chunks_to_add)} chunks into Hybrid Vector Store...")
        vector_store.add_chunks(vector_chunks_to_add)
        vector_store.save()

    is_valid, records_checked, msg = verify_audit_chain(db)
    print(f"\nAudit Chain Verification: {msg} (Checked: {records_checked}, Valid: {is_valid})")
    print("============================================================")
    print("Canonical PAS-X Ingestion Completed Successfully!")
    print("============================================================")
    db.close()

if __name__ == "__main__":
    ingest_pasx_documents()
