import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.models.entities import EvidencePack, System, create_audit_log
from backend.app.schemas.domain import EvidencePackResponse
from backend.app.agents.evidence_agent import evidence_agent
from backend.app.agents.supervisor import supervisor_agent

router = APIRouter(prefix="/evidence", tags=["Audit Evidence"])

class GenerateEvidenceRequest(BaseModel):
    system_id: str = "SYS-LIMS-001"
    actor: str = "qa@demo.local"

@router.post("/generate")
def generate_evidence_pack(req: GenerateEvidenceRequest, db: Session = Depends(get_db)):
    system = db.query(System).filter(System.id == req.system_id).first()
    system_name = system.name if system else "Validated LIMS"
    
    # Run assessment to gather fresh data
    pipeline_res = supervisor_agent.run_assessment_pipeline(
        db=db,
        system_id=req.system_id,
        generate_evidence=False,
        actor=req.actor
    )
    
    # Generate pack
    ev_res = evidence_agent.run(
        db=db,
        system_id=req.system_id,
        system_name=system_name,
        readiness_score=pipeline_res["readiness_score"],
        checklist_results=pipeline_res["checks"],
        findings=pipeline_res["findings"],
        risks=pipeline_res["risks"],
        recommendations=pipeline_res["recommendations"],
        generated_by=req.actor
    )
    
    # Audit log
    create_audit_log(
        db=db,
        actor_type="AGENT",
        actor_id="audit_evidence_agent",
        action="Generated Formal GxP IT Audit Evidence Pack",
        entity_type="EVIDENCE_PACK",
        entity_id=ev_res.metadata.get("evidence_pack_id"),
        details={
            "pdf_file": ev_res.metadata.get("pdf_filename"),
            "docx_file": ev_res.metadata.get("docx_filename"),
            "readiness_score": pipeline_res["readiness_score"],
            "findings_count": len(pipeline_res["findings"])
        },
        agent_name="audit_evidence_agent"
    )
    
    return ev_res.metadata

@router.get("", response_model=List[EvidencePackResponse])
def list_evidence_packs(system_id: str = None, db: Session = Depends(get_db)):
    q = db.query(EvidencePack)
    if system_id:
        q = q.filter(EvidencePack.system_id == system_id)
    return q.order_by(EvidencePack.created_at.desc()).all()

@router.get("/{id}", response_model=EvidencePackResponse)
def get_evidence_pack(id: str, db: Session = Depends(get_db)):
    pack = db.query(EvidencePack).filter(EvidencePack.id == id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    return pack

@router.get("/download/{id}/pdf")
def download_evidence_pdf(id: str, db: Session = Depends(get_db)):
    pack = db.query(EvidencePack).filter(EvidencePack.id == id).first()
    if not pack or not pack.file_path or not os.path.exists(pack.file_path):
        raise HTTPException(status_code=404, detail="PDF evidence file not found on server")
    return FileResponse(
        path=pack.file_path,
        filename=os.path.basename(pack.file_path),
        media_type="application/pdf"
    )

@router.get("/download/{id}/docx")
def download_evidence_docx(id: str, db: Session = Depends(get_db)):
    pack = db.query(EvidencePack).filter(EvidencePack.id == id).first()
    if not pack or not pack.docx_file_path or not os.path.exists(pack.docx_file_path):
        raise HTTPException(status_code=404, detail="DOCX evidence file not found on server")
    return FileResponse(
        path=pack.docx_file_path,
        filename=os.path.basename(pack.docx_file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
