import os
from typing import Dict, Any, List, TypedDict, Optional
from sqlalchemy.orm import Session

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Safe fallback if langgraph internals vary
    StateGraph = None
    END = "__end__"

from backend.app.models.entities import (
    System, Document, ComplianceFinding, Risk as RiskModel,
    Recommendation as RecommendationModel, create_audit_log
)
from backend.app.agents.system_knowledge import system_knowledge_agent
from backend.app.agents.compliance_agent import compliance_agent
from backend.app.agents.risk_agent import risk_agent
from backend.app.agents.evidence_agent import evidence_agent
from backend.app.agents.recommendation_agent import recommendation_agent
from backend.app.schemas.domain import AgentResult

class OrchestratorState(TypedDict):
    db: Any
    system_id: str
    system_name: str
    intent: str
    generate_evidence: bool
    actor: str
    
    system_knowledge_result: Optional[Dict[str, Any]]
    compliance_result: Optional[Dict[str, Any]]
    risk_result: Optional[Dict[str, Any]]
    recommendations_result: Optional[Dict[str, Any]]
    evidence_result: Optional[Dict[str, Any]]
    
    checks: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    readiness_score: int
    execution_trace: List[Dict[str, str]]
    final_summary: str
    confidence: float

class SupervisorAgent:
    def __init__(self):
        self.name = "supervisor_agent"
        self._build_graph()

    def _build_graph(self):
        if StateGraph is None:
            self.graph = None
            return

        workflow = StateGraph(OrchestratorState)
        
        # Nodes
        workflow.add_node("system_knowledge", self._node_system_knowledge)
        workflow.add_node("compliance", self._node_compliance)
        workflow.add_node("risk", self._node_risk)
        workflow.add_node("recommendation", self._node_recommendation)
        workflow.add_node("evidence", self._node_evidence)
        workflow.add_node("synthesize", self._node_synthesize)
        
        # Edges
        workflow.set_entry_point("system_knowledge")
        workflow.add_edge("system_knowledge", "compliance")
        workflow.add_edge("compliance", "risk")
        workflow.add_edge("risk", "recommendation")
        workflow.add_edge("recommendation", "evidence")
        workflow.add_edge("evidence", "synthesize")
        workflow.add_edge("synthesize", END)
        
        self.graph = workflow.compile()

    def _node_system_knowledge(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        
        sk_res = system_knowledge_agent.run(db, system_id)
        
        trace = state.get("execution_trace", []) + [{
            "agent": "System Knowledge Agent",
            "status": f"Indexed {sk_res.metadata['system']['documents_count']} active GxP documents"
        }]
        
        return {
            "execution_trace": trace,
            "system_knowledge_result": sk_res.model_dump() if hasattr(sk_res, "model_dump") else sk_res.dict()
        }

    def _node_compliance(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        
        comp_res = compliance_agent.run(db, system_id)
        readiness_score = comp_res.metadata["readiness_score"]
        findings = comp_res.findings
        checks = comp_res.metadata["checks"]
        
        # Sync findings to database if needed
        for f in findings:
            existing = db.query(ComplianceFinding).filter(
                ComplianceFinding.system_id == system_id,
                ComplianceFinding.title == f["title"]
            ).first()
            if not existing:
                finding_rec = ComplianceFinding(
                    system_id=system_id,
                    title=f["title"],
                    description=f["description"],
                    severity=f["severity"],
                    status="OPEN",
                    confidence=f.get("confidence", 0.9),
                    source_citations=f.get("source_citations", []),
                    recommended_action=f.get("recommended_action")
                )
                db.add(finding_rec)
        db.commit()
        
        trace = state.get("execution_trace", []) + [{
            "agent": "Compliance Agent",
            "status": f"Verified {len(checks)} controls -> Score: {readiness_score}%"
        }]
        
        return {
            "execution_trace": trace,
            "compliance_result": comp_res.model_dump() if hasattr(comp_res, "model_dump") else comp_res.dict(),
            "readiness_score": readiness_score,
            "findings": findings,
            "checks": checks
        }

    def _node_risk(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        findings = state.get("findings", [])
        
        risk_res = risk_agent.run(db, findings, system_id)
        risks = risk_res.metadata["risks"]
        
        # Sync risks to database
        for r in risks:
            existing_risk = db.query(RiskModel).filter(
                RiskModel.system_id == system_id,
                RiskModel.rationale == r["rationale"]
            ).first()
            if not existing_risk:
                risk_rec = RiskModel(
                    system_id=system_id,
                    risk_level=r["risk_level"],
                    impact_type=r["impact_type"],
                    likelihood=r["likelihood"],
                    impact=r["impact"],
                    score=r["score"],
                    rationale=r["rationale"],
                    control_mapping=r.get("control_mapping")
                )
                db.add(risk_rec)
        db.commit()
        
        highest_risk = risk_res.metadata.get("highest_risk_level", "LOW")
        trace = state.get("execution_trace", []) + [{
            "agent": "Risk Agent",
            "status": f"Computed risk matrix ({highest_risk} priority)"
        }]
        
        return {
            "execution_trace": trace,
            "risk_result": risk_res.model_dump() if hasattr(risk_res, "model_dump") else risk_res.dict(),
            "risks": risks
        }

    def _node_recommendation(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        findings = state.get("findings", [])
        
        rec_res = recommendation_agent.run(db, findings, system_id)
        recs = rec_res.recommendations
        
        # Sync recommendations to database
        for rec in recs:
            existing_rec = db.query(RecommendationModel).filter(
                RecommendationModel.system_id == system_id,
                RecommendationModel.title == rec["title"]
            ).first()
            if not existing_rec:
                rec_record = RecommendationModel(
                    system_id=system_id,
                    title=rec["title"],
                    description=rec["rationale"],
                    priority=rec["priority"],
                    rationale=rec["rationale"],
                    suggested_owner=rec["suggested_owner"],
                    status="PROPOSED",
                    confidence=rec.get("confidence", 0.92)
                )
                db.add(rec_record)
        db.commit()
        
        trace = state.get("execution_trace", []) + [{
            "agent": "Recommendation Agent",
            "status": f"Formulated {len(recs)} corrective actions gated by human authorization"
        }]
        
        return {
            "execution_trace": trace,
            "recommendations_result": rec_res.model_dump() if hasattr(rec_res, "model_dump") else rec_res.dict(),
            "recommendations": recs
        }

    def _node_evidence(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        system_name = state["system_name"]
        readiness_score = state.get("readiness_score", 0)
        checks = state.get("checks", [])
        findings = state.get("findings", [])
        risks = state.get("risks", [])
        recs = state.get("recommendations", [])
        actor = state.get("actor", "user@demo.local")
        
        ev_metadata = {}
        if state.get("generate_evidence", False):
            ev_res = evidence_agent.run(
                db=db,
                system_id=system_id,
                system_name=system_name,
                readiness_score=readiness_score,
                checklist_results=checks,
                findings=findings,
                risks=risks,
                recommendations=recs,
                generated_by=actor
            )
            ev_metadata = ev_res.metadata
            
        trace = state.get("execution_trace", []) + [{
            "agent": "Evidence Agent",
            "status": "Ready to compile tamper-evident evidence pack" if not state.get("generate_evidence") else "Compiled tamper-evident evidence pack"
        }]
        
        return {
            "execution_trace": trace,
            "evidence_result": ev_metadata
        }

    def _node_synthesize(self, state: OrchestratorState) -> Dict[str, Any]:
        db = state["db"]
        system_id = state["system_id"]
        readiness_score = state.get("readiness_score", 0)
        checks = state.get("checks", [])
        findings = state.get("findings", [])
        recs = state.get("recommendations", [])
        
        highest_risk = "LOW"
        if state.get("risk_result"):
            highest_risk = state["risk_result"].get("metadata", {}).get("highest_risk_level", "LOW")
            
        # Log Audit Trail
        create_audit_log(
            db=db,
            actor_type="AGENT",
            actor_id="supervisor_agent",
            action="Executed Full Continuous Compliance Assessment Pipeline",
            entity_type="SYSTEM",
            entity_id=system_id,
            details={
                "readiness_score": readiness_score,
                "total_checks": len(checks),
                "open_findings": len(findings),
                "highest_risk": highest_risk,
                "recommendations_count": len(recs)
            },
            agent_name="supervisor_agent"
        )
        
        return {
            "final_summary": f"System readiness confirmed at {readiness_score}%.",
            "confidence": 0.94
        }

    def run_assessment_pipeline(
        self,
        db: Session,
        system_id: str = "SYS-MES-001",
        generate_evidence: bool = False,
        actor: str = "user@demo.local"
    ) -> Dict[str, Any]:
        """
        Executes the full LangGraph multi-agent compliance pipeline end-to-end.
        """
        system = db.query(System).filter(System.id == system_id).first()
        system_name = system.name if system else "Novo Life MES PAS-X"
        
        initial_state = {
            "db": db,
            "system_id": system_id,
            "system_name": system_name,
            "intent": "continuous_compliance_assessment",
            "generate_evidence": generate_evidence,
            "actor": actor,
            "execution_trace": [{
                "agent": "Supervisor Agent", 
                "status": "Request received and decomposed into specialized subtasks"
            }],
            "checks": [],
            "findings": [],
            "risks": [],
            "recommendations": []
        }
        
        if self.graph is not None:
            final_state = self.graph.invoke(initial_state)
        else:
            # Fallback sequential execution if LangGraph is not available
            final_state = initial_state.copy()
            final_state.update(self._node_system_knowledge(final_state))
            final_state.update(self._node_compliance(final_state))
            final_state.update(self._node_risk(final_state))
            final_state.update(self._node_recommendation(final_state))
            final_state.update(self._node_evidence(final_state))
            final_state.update(self._node_synthesize(final_state))
            
        return {
            "system_id": system_id,
            "system_name": system_name,
            "readiness_score": final_state.get("readiness_score", 0),
            "confidence": final_state.get("confidence", 0.94),
            "checks": final_state.get("checks", []),
            "findings": final_state.get("findings", []),
            "risks": final_state.get("risks", []),
            "recommendations": final_state.get("recommendations", []),
            "evidence": final_state.get("evidence_result", {}),
            "execution_trace": final_state.get("execution_trace", [])
        }

supervisor_agent = SupervisorAgent()
