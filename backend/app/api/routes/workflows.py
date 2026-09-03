from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import Workflow, Recommendation, create_audit_log
from backend.app.schemas.domain import (
    WorkflowResponse, WorkflowCreateRequest, WorkflowApprovalRequest, WorkflowRejectionRequest
)
from backend.app.integrations.mock_servicenow import mock_servicenow

router = APIRouter(prefix="/workflows", tags=["Human-in-the-Loop Workflows"])

@router.post("", response_model=WorkflowResponse)
def create_workflow(req: WorkflowCreateRequest, db: Session = Depends(get_db)):
    rec = None
    if req.recommendation_id:
        rec = db.query(Recommendation).filter(Recommendation.id == req.recommendation_id).first()
        if rec:
            rec.status = "IN_WORKFLOW"
            
    payload = req.payload.copy()
    if rec:
        payload["recommendation_title"] = rec.title
        payload["priority"] = rec.priority
        payload["suggested_owner"] = rec.suggested_owner
        
    wf = Workflow(
        type=req.type,
        system_id=req.system_id,
        recommendation_id=req.recommendation_id,
        status="PENDING_APPROVAL",
        requires_approval=True,
        payload_json=payload
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    
    # Audit log
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id="user@demo.local",
        action="Created Human Approval Gated Workflow",
        entity_type="WORKFLOW",
        entity_id=wf.id,
        details={
            "workflow_type": wf.type,
            "system_id": wf.system_id,
            "recommendation": payload.get("recommendation_title", "General Remediation")
        }
    )
    return wf

@router.get("/pending", response_model=List[WorkflowResponse])
def list_pending_workflows(system_id: str = None, db: Session = Depends(get_db)):
    q = db.query(Workflow).filter(Workflow.status == "PENDING_APPROVAL")
    if system_id:
        q = q.filter(Workflow.system_id == system_id)
    return q.order_by(Workflow.created_at.desc()).all()

@router.get("", response_model=List[WorkflowResponse])
def list_all_workflows(system_id: str = None, db: Session = Depends(get_db)):
    q = db.query(Workflow)
    if system_id:
        q = q.filter(Workflow.system_id == system_id)
    return q.order_by(Workflow.created_at.desc()).all()

@router.post("/{id}/approve", response_model=WorkflowResponse)
def approve_workflow(id: str, req: WorkflowApprovalRequest, db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if wf.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Cannot approve workflow in status '{wf.status}'")
        
    # Execute Mock ServiceNow Action
    rec_title = wf.payload_json.get("recommendation_title", "GxP IT Remediation Action")
    snow_ticket = mock_servicenow.create_ticket(
        title=f"[GxP Copilot] {rec_title}",
        description=f"Authorized by {req.actor}. Comment: {req.comment}. System: {wf.system_id}",
        system_id=wf.system_id,
        priority="2 - High"
    )
    
    now_dt = datetime.now(timezone.utc)
    wf.status = "APPROVED"
    wf.approved_by = req.actor
    wf.approved_at = now_dt
    wf.executed_at = now_dt
    
    updated_payload = dict(wf.payload_json or {})
    updated_payload["approval_comment"] = req.comment
    updated_payload["snow_ticket"] = snow_ticket
    updated_payload["ticket_id"] = snow_ticket["ticket_id"]
    wf.payload_json = updated_payload
    
    # Update linked recommendation
    if wf.recommendation_id:
        rec = db.query(Recommendation).filter(Recommendation.id == wf.recommendation_id).first()
        if rec:
            rec.status = "APPROVED"
            
    db.commit()
    db.refresh(wf)
    
    # Audit log human approval and ServiceNow execution
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id=req.actor,
        action="Human Approved GxP Workflow & Executed ServiceNow Task",
        entity_type="WORKFLOW",
        entity_id=wf.id,
        details={
            "approved_by": req.actor,
            "comment": req.comment,
            "servicenow_ticket": snow_ticket["ticket_id"],
            "snow_sys_id": snow_ticket["sys_id"],
            "workflow_type": wf.type
        }
    )
    
    return wf

@router.post("/{id}/reject", response_model=WorkflowResponse)
def reject_workflow(id: str, req: WorkflowRejectionRequest, db: Session = Depends(get_db)):
    if not req.reason or not req.reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is mandatory for GxP compliance auditability.")
        
    wf = db.query(Workflow).filter(Workflow.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if wf.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Cannot reject workflow in status '{wf.status}'")
        
    wf.status = "REJECTED"
    wf.approved_by = req.actor
    wf.rejection_reason = req.reason
    
    updated_payload = dict(wf.payload_json or {})
    updated_payload["rejection_reason"] = req.reason
    wf.payload_json = updated_payload
    
    if wf.recommendation_id:
        rec = db.query(Recommendation).filter(Recommendation.id == wf.recommendation_id).first()
        if rec:
            rec.status = "REJECTED"
            
    db.commit()
    db.refresh(wf)
    
    # Audit log
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id=req.actor,
        action="Rejected GxP Workflow",
        entity_type="WORKFLOW",
        entity_id=wf.id,
        details={
            "rejected_by": req.actor,
            "rejection_reason": req.reason,
            "workflow_type": wf.type
        }
    )
    
    return wf
