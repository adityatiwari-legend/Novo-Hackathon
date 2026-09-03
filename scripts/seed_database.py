"""
Seed database script for Novo Nordisk GxP AI Co-Pilot hackathon prototype.
Seeds:
- Users (QA, System Owner, Auditor, Admin)
- System A (Validated LIMS)
- Documents & Chunks (System_A_URS, Risk Assessment, SOP Change Control, SOP Document Mgmt)
- Indexes chunks in Hybrid Vector Store
- Initial Compliance Evaluation (Readiness = 82%)
- Tamper-Evident Hash-Chained Audit Trail
"""
import os
import sys

# Ensure workspace root is on sys.path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.entities import (
    User, System, Document, DocumentChunk, ComplianceFinding,
    Risk, Recommendation, Workflow, AuditLog
)
from backend.app.models import create_audit_log, verify_audit_chain
from backend.app.services.document_parser import parse_document
from backend.app.services.vector_store import vector_store
from backend.app.agents.supervisor import supervisor_agent

def seed():
    print("[*] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Seed Users
    print("[*] Seeding Demo Users...")
    demo_users = [
        {"name": "Sarah Jenkins", "email": "owner@demo.local", "role": "SYSTEM_OWNER", "dept": "IT Quality & Validated Systems"},
        {"name": "Dr. Elena Rostova", "email": "qa@demo.local", "role": "QA_COMPLIANCE", "dept": "Global Quality Assurance"},
        {"name": "Henrik Lindqvist", "email": "auditor@demo.local", "role": "AUDITOR", "dept": "Regulatory Affairs & Compliance"},
        {"name": "System Administrator", "email": "admin@demo.local", "role": "ADMIN", "dept": "GxP IT Operations"},
    ]
    for u in demo_users:
        if not db.query(User).filter(User.email == u["email"]).first():
            user = User(
                name=u["name"],
                email=u["email"],
                role=u["role"],
                department=u["dept"],
                permissions=["*"] if u["role"] == "ADMIN" else ["view", "review", "approve"]
            )
            db.add(user)
    db.commit()
    
    # 2. Seed System A
    print("[*] Seeding System A: Validated LIMS...")
    sys_id = "SYS-LIMS-001"
    system = db.query(System).filter(System.id == sys_id).first()
    if not system:
        system = System(
            id=sys_id,
            name="Validated Laboratory Information Management System",
            description="Enterprise QC analytical laboratory platform managing sample disposition, test execution, and batch release data pursuant to GAMP 5 Category 4.",
            criticality="GxP-Critical",
            gxp_status="GxP",
            business_owner="Dr. Marcus Vance (Head of Analytical QC)"
        )
        db.add(system)
        db.commit()
        
    # Clear vector store for fresh seed
    vector_store.clear()
    
    # 3. Ingest Sample Documents
    print("[*] Ingesting and Vector-Indexing Sample Documents...")
    sample_docs = [
        ("System_A_URS.docx", "URS"),
        ("System_A_Risk_Assessment.docx", "RISK_ASSESSMENT"),
        ("SOP_Change_Control.docx", "SOP"),
        ("SOP_Document_Management.docx", "SOP"),
    ]
    sample_dir = os.path.join(workspace_root, "data", "sample_documents")
    
    for filename, doc_type in sample_docs:
        filepath = os.path.join(sample_dir, filename)
        if not os.path.exists(filepath):
            print(f"[-] Warning: {filepath} not found. Skipping.")
            continue
            
        parsed = parse_document(filepath, default_system_id=sys_id)
        
        # Check existing doc
        existing_doc = db.query(Document).filter(
            Document.title == parsed.title,
            Document.system_id == sys_id
        ).first()
        
        if existing_doc:
            doc = existing_doc
            doc.checksum = parsed.checksum
            doc.version = parsed.version
            doc.approval_status = parsed.approval_status
            doc.review_date = parsed.review_date
            doc.file_path = filepath
        else:
            doc = Document(
                title=parsed.title,
                document_type=doc_type,
                system_id=sys_id,
                version=parsed.version,
                owner_id=parsed.owner,
                status="Effective" if parsed.approval_status == "Approved" else "Draft",
                review_date=parsed.review_date,
                approval_status=parsed.approval_status,
                source_system="Validation Repository",
                file_path=filepath,
                checksum=parsed.checksum,
                metadata_json={"sections": parsed.sections}
            )
            db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.commit()
        
        new_vec_chunks = []
        for c in parsed.chunks:
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=c.chunk_index,
                content=c.content,
                page_number=c.page_number,
                section=c.section,
                embedding_reference=f"vec_{doc.id}_{c.chunk_index}",
                metadata_json=c.metadata
            )
            db.add(chunk_rec)
            
            new_vec_chunks.append({
                "id": f"{doc.id}_{c.chunk_index}",
                "document_id": doc.id,
                "document_title": doc.title,
                "system_id": sys_id,
                "content": c.content,
                "page_number": c.page_number,
                "section": c.section,
                "metadata": c.metadata
            })
        db.commit()
        vector_store.add_chunks(new_vec_chunks)
        
        # Tamper-Evident Audit Log
        create_audit_log(
            db=db,
            actor_type="SYSTEM",
            actor_id="ingestion_pipeline",
            action="Indexed GxP Document",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            details={
                "title": doc.title,
                "version": doc.version,
                "approval_status": doc.approval_status,
                "chunks_count": len(parsed.chunks)
            }
        )
        print(f"  [+] Ingested {doc.title} ({len(parsed.chunks)} chunks)")

    # 4. Run Initial Supervisor Assessment Pipeline
    print("[*] Running LangGraph Supervisor Assessment Pipeline...")
    pipeline_res = supervisor_agent.run_assessment_pipeline(db, system_id=sys_id, generate_evidence=False)
    
    readiness = pipeline_res["readiness_score"]
    findings_count = len(pipeline_res["findings"])
    risks_count = len(pipeline_res["risks"])
    recs_count = len(pipeline_res["recommendations"])
    
    print(f"[+] Initial Audit Readiness Score: {readiness}%")
    print(f"[+] Identified Compliance Gaps: {findings_count}")
    print(f"[+] High/Medium Risks: {risks_count}")
    print(f"[+] Proposed Remediation Recommendations: {recs_count}")
    
    # 5. Verify Cryptographic Audit Chain
    is_valid, count, msg = verify_audit_chain(db)
    print(f"[+] Audit Chain Verification: {msg} ({count} blocks chained, valid={is_valid})")
    
    db.close()
    print("[*] Database seeding complete and ready for demo.")

if __name__ == "__main__":
    seed()
