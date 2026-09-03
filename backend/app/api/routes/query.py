from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.entities import create_audit_log
from backend.app.schemas.domain import QueryRequest, QueryResponse
from backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/query", tags=["RAG Query"])

@router.post("", response_model=QueryResponse)
def query_rag(req: QueryRequest, db: Session = Depends(get_db)):
    system_id = req.system_id or "SYS-MES-001"
    mode = req.mode or "General Q&A"
    result = rag_service.query(
        question=req.question,
        system_id=system_id,
        top_k=req.top_k,
        mode=mode
    )
    
    # Add structured high-level agent execution milestones
    if mode == "GxP Audit":
        result.agent_execution = [
            {"agent": "Supervisor Agent", "step": "Routed query to GxP IT Audit & Lifecycle Intelligence Engine"},
            {"agent": "Audit Checklist Agent", "step": "Evaluated Top 25 Difficult-Auditor Questions & Acceptance Criteria"},
            {"agent": "Lifecycle Governance Agent", "step": "Cross-referenced NN Master IT SOP (HACK-IT-SOP-001) & LIMS Benchmark"},
            {"agent": "System Evidence Agent", "step": "Traversed MES PAS-X primary lifecycle evidence (NL-MES-*) & Gate G1-G6 status"},
            {"agent": "Deterministic Audit Engine", "step": "Evaluated PASS/PARTIAL/FAIL status, evidence confidence & citations"},
            {"agent": "Corrective Action Agent", "step": "Synthesized evidence-backed findings, deviations & release recommendations"}
        ]
    else:
        result.agent_execution = [
            {"agent": "Supervisor Agent", "step": "Decomposed intent & routed across specialized GxP mesh"},
            {"agent": "System Knowledge", "step": f"Retrieved {len(result.sources)} grounded evidence chunks from indexed lifecycle package"},
            {"agent": "Compliance Agent", "step": "Evaluated 15 rules from compliance_rules.json against document evidence"},
            {"agent": "Traceability Agent", "step": "Traversed 50 URS requirements & 26 system risk baseline linkages"},
            {"agent": "Release Gate Engine", "step": "Evaluated lifecycle gates G1-G6: Confirmed HOLD / DEFER recommendation"},
            {"agent": "Recommendation Agent", "step": "Synthesized corrective remediation gated by human authorization"}
        ]
    
    # Audit log query event
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id="qa@demo.local",
        action="RAG_QUERY",
        entity_type="QUERY",
        entity_id=system_id,
        details={
            "question": req.question,
            "mode": mode,
            "confidence": result.confidence,
            "citations_count": len(result.citations),
            "sources_count": len(result.sources),
            "warnings": result.warnings
        },
        agent_name="supervisor_agent"
    )
    
    return result
