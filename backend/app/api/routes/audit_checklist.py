"""
FastAPI Routes for Executable GxP IT Audit Checklists,
Cross-Document SOP Comparison, and Audit Report Generation.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import AuditChecklist, AuditQuestion, create_audit_log
from backend.app.schemas.domain import (
    AuditChecklistResponse, AuditQuestionResponse, AuditAssessmentResponse,
    AuditExecuteRequest, CrossDocComparisonResponse, AuditReportRequest,
    AuditReportResponse
)
from backend.app.services.audit_engine import audit_engine
from backend.app.services.audit_report_service import audit_report_service

router = APIRouter(prefix="/audit", tags=["GxP Audit Checklist"])

@router.get("/checklists", response_model=List[AuditChecklistResponse])
def list_checklists(db: Session = Depends(get_db)):
    """List all registered audit checklists."""
    checklists = db.query(AuditChecklist).all()
    results = []
    for c in checklists:
        q_count = db.query(AuditQuestion).filter(AuditQuestion.checklist_id == c.id).count()
        results.append(AuditChecklistResponse(
            id=c.id,
            title=c.title,
            version=c.version,
            source_file=c.source_file,
            description=c.description,
            questions_count=q_count
        ))
    return results

@router.get("/checklists/{checklist_id}/questions", response_model=List[AuditQuestionResponse])
def get_checklist_questions(checklist_id: str, db: Session = Depends(get_db)):
    """Retrieve all structured questions for a given checklist."""
    questions = db.query(AuditQuestion).filter(
        AuditQuestion.checklist_id == checklist_id
    ).order_by(AuditQuestion.sequence.asc()).all()

    if not questions and checklist_id == "CKL-TOP25-CORE":
        # Fallback to the first 25 questions of CKL-TOP25-2026 if core subset isn't queried separately
        questions = db.query(AuditQuestion).order_by(AuditQuestion.sequence.asc()).limit(25).all()

    return questions

@router.post("/execute", response_model=AuditAssessmentResponse)
def execute_audit(req: AuditExecuteRequest, db: Session = Depends(get_db)):
    """
    Executes the Top 25 Audit Checklist against the target system deterministically.
    Calculates dynamic readiness score, pass/partial/fail counts, and grounded findings.
    """
    system_id = req.system_id or "SYS-MES-001"
    checklist_id = req.checklist_id or "CKL-TOP25-CORE"
    
    assessment = audit_engine.execute_audit(
        db=db,
        system_id=system_id,
        checklist_id=checklist_id,
        weights_override=req.scoring_weights
    )
    return assessment

@router.get("/assessments/latest", response_model=AuditAssessmentResponse)
def get_latest_assessment(system_id: str = Query("SYS-MES-001"), db: Session = Depends(get_db)):
    """Retrieve the most recent audit assessment for a system."""
    assessment = audit_engine.get_latest_assessment(db=db, system_id=system_id)
    if not assessment:
        raise HTTPException(status_code=404, detail=f"No audit assessments found for {system_id}")
    return assessment

@router.get("/comparison", response_model=CrossDocComparisonResponse)
def get_cross_doc_comparison(system_id: str = Query("SYS-MES-001"), db: Session = Depends(get_db)):
    """
    Performs cross-document comparison contrasting primary MES PAS-X evidence
    against Master IT System Lifecycle SOP (HACK-IT-SOP-001) expectations.
    """
    comparison = audit_engine.cross_document_comparison(db=db, system_id=system_id)
    return comparison

@router.post("/report", response_model=AuditReportResponse)
def generate_audit_report(req: AuditReportRequest, db: Session = Depends(get_db)):
    """
    Generates professional 14-section PDF and DOCX GxP IT Audit Reports.
    """
    system_id = req.system_id or "SYS-MES-001"
    checklist_id = req.checklist_id or "CKL-TOP25-CORE"
    
    report_res = audit_report_service.generate_full_dossier(
        db=db,
        system_id=system_id,
        checklist_id=checklist_id
    )

    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id="qa@demo.local",
        action="AUDIT_REPORT_GENERATED",
        entity_type="REPORT",
        entity_id=system_id,
        details={
            "pdf_path": report_res["pdf_path"],
            "docx_path": report_res["docx_path"],
            "readiness_score": report_res["readiness_score"]
        },
        agent_name="audit_report_service"
    )

    return AuditReportResponse(
        success=report_res["success"],
        pdf_path=report_res["pdf_path"],
        docx_path=report_res["docx_path"],
        summary=report_res["summary"],
        readiness_score=report_res["readiness_score"],
        disclaimer=report_res["disclaimer"]
    )

@router.get("/download")
def download_audit_report(file_path: str = Query(...)):
    """Secure endpoint for downloading generated PDF or DOCX audit reports."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested report file not found on server.")
    
    filename = os.path.basename(file_path)
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(file_path, filename=filename, media_type=media_type)
