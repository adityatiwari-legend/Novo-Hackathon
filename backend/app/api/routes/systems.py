from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.services.system_state import SystemStateService
from backend.app.services.temporal_service import get_applicable_evidence
from backend.app.services.graph_service import get_requirement_trace, get_risk_trace
from backend.app.models.entities import System

router = APIRouter(prefix="/api/systems", tags=["Systems"])

@router.get("/")
def list_systems(db: Session = Depends(get_db)):
    systems = db.query(System).all()
    return [{"id": s.id, "name": s.name, "status": s.lifecycle_status} for s in systems]

@router.get("/{system_id}/state")
def get_system_state(system_id: str, db: Session = Depends(get_db)):
    state_service = SystemStateService(db)
    state = state_service.get_system_state(system_id)
    if not state:
        raise HTTPException(status_code=404, detail="System not found")
    return state

@router.get("/{system_id}/evidence")
def get_system_evidence(
    system_id: str, 
    target_date: Optional[datetime] = None, 
    db: Session = Depends(get_db)
):
    evidence = get_applicable_evidence(db, system_id, target_date)
    return [
        {
            "id": e.evidence_id, 
            "type": e.evidence_type, 
            "text": e.text,
            "status": e.status,
            "locator": e.locator
        } for e in evidence
    ]

@router.get("/{system_id}/trace/REQUIREMENT/{req_id}")
def get_req_trace(system_id: str, req_id: str, db: Session = Depends(get_db)):
    trace = get_requirement_trace(db, req_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return trace

@router.get("/{system_id}/trace/RISK/{risk_id}")
def get_rk_trace(system_id: str, risk_id: str, db: Session = Depends(get_db)):
    trace = get_risk_trace(db, risk_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Risk not found")
    return trace
