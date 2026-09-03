from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.models.entities import ComplianceFinding, Risk as RiskModel, Recommendation as RecommendationModel
from backend.app.schemas.domain import (
    ComplianceFindingResponse, RiskResponse, RecommendationResponse
)
from backend.app.agents.supervisor import supervisor_agent
from backend.app.services.compliance_engine import compliance_engine
from backend.app.services.traceability_engine import traceability_engine
from backend.app.services.release_gate_engine import release_gate_engine
from backend.app.services.consistency_service import consistency_service

router = APIRouter(tags=["Compliance & Risk"])

class AssessRequest(BaseModel):
    system_id: str = "SYS-MES-001"
    generate_evidence: bool = False
    actor: str = "qa@demo.local"

@router.post("/compliance/assess")
def run_compliance_assessment(req: AssessRequest, db: Session = Depends(get_db)):
    return supervisor_agent.run_assessment_pipeline(
        db=db,
        system_id=req.system_id,
        generate_evidence=req.generate_evidence,
        actor=req.actor
    )

@router.get("/compliance/readiness/{system_id}")
def get_system_readiness(system_id: str, db: Session = Depends(get_db)):
    eval_result = compliance_engine.evaluate_system(db, system_id)
    return {
        "system_id": system_id,
        "readiness_score": eval_result["readiness_score"],
        "release_recommendation": eval_result.get("release_recommendation", "HOLD / DEFER - DO NOT RELEASE"),
        "lifecycle_status": eval_result.get("lifecycle_status", "PRE-OPERATIONAL / NOT ACTIVATED"),
        "total_checks": eval_result["total_checks"],
        "passed_checks": eval_result["passed_checks"],
        "failed_checks": eval_result["failed_checks"],
        "checks": eval_result["checks"],
        "blocking_findings": eval_result.get("blocking_findings", 0),
        "high_findings": eval_result.get("high_findings", 0),
        "confidence": 0.95
    }

@router.get("/compliance/findings", response_model=List[ComplianceFindingResponse])
def list_findings(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    findings = db.query(ComplianceFinding).filter(ComplianceFinding.system_id == system_id).all()
    if not findings:
        supervisor_agent.run_assessment_pipeline(db, system_id=system_id)
        findings = db.query(ComplianceFinding).filter(ComplianceFinding.system_id == system_id).all()
    return findings

@router.get("/risk", response_model=List[RiskResponse])
def list_risks(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    risks = db.query(RiskModel).filter(RiskModel.system_id == system_id).all()
    if not risks:
        supervisor_agent.run_assessment_pipeline(db, system_id=system_id)
        risks = db.query(RiskModel).filter(RiskModel.system_id == system_id).all()
    return risks

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    recs = db.query(RecommendationModel).filter(RecommendationModel.system_id == system_id).all()
    if not recs:
        supervisor_agent.run_assessment_pipeline(db, system_id=system_id)
        recs = db.query(RecommendationModel).filter(RecommendationModel.system_id == system_id).all()
    return recs

@router.get("/compliance/traceability")
def get_traceability(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    matrix = traceability_engine.build_traceability_matrix(db, system_id)
    gaps = traceability_engine.detect_traceability_gaps(db, system_id)
    return {
        "system_id": system_id,
        "total_requirements": len(matrix),
        "verified_count": len([m for m in matrix if m["verification_status"] == "COMPLETE"]),
        "unverified_count": len([m for m in matrix if m["verification_status"] == "NOT_PERFORMED"]),
        "gaps_count": len(gaps),
        "gaps": gaps,
        "matrix": matrix
    }

@router.get("/compliance/release-gates")
def get_release_gates(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    return release_gate_engine.evaluate_release_gates(db, system_id)

@router.get("/compliance/consistency")
def get_document_consistency(system_id: str = "SYS-MES-001", db: Session = Depends(get_db)):
    return consistency_service.check_consistency(db, system_id)
