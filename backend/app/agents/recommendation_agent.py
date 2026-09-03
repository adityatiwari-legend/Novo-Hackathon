from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.schemas.domain import AgentResult

class RecommendationAgent:
    def __init__(self):
        self.name = "recommendation_agent"

    def run(self, db: Session, findings: List[Dict[str, Any]], system_id: str = "SYS-LIMS-001") -> AgentResult:
        recommendations = []
        
        for f in findings:
            title = f.get("title", "")
            code = f.get("check_code", "")
            
            if code == "DOC-003" or "QA Approval" in title:
                recommendations.append({
                    "title": "Route URS to QA/System Owner for formal approval",
                    "priority": "CRITICAL",
                    "suggested_owner": "Sarah Jenkins (Technical System Owner) & QA Validation Lead",
                    "due_date_suggestion": "Immediate (Within 5 Business Days)",
                    "rationale": (
                        "Section 6 of System_A_URS.docx lacks Quality Assurance digital signature. "
                        "A formal approval workflow must be routed via ServiceNow / Veeva Vault Quality "
                        "before operational qualification (OQ) execution."
                    ),
                    "related_finding": title,
                    "workflow_type": "APPROVAL_GATE",
                    "target_action": "route_for_qa_signoff",
                    "confidence": 0.95
                })
            elif code == "CHG-001" or "Traceability" in title:
                recommendations.append({
                    "title": "Execute Bidirectional Requirements Traceability Matrix Validation",
                    "priority": "HIGH",
                    "suggested_owner": "IT Quality & Validation Engineer",
                    "due_date_suggestion": "Prior to Next Major Release",
                    "rationale": (
                        "Link requirements REQ-001 through REQ-004 directly to executed test scripts (OQ-01 through OQ-04) "
                        "to satisfy GAMP 5 Category 4 verification standards."
                    ),
                    "related_finding": title,
                    "workflow_type": "REMEDIATION_TASK",
                    "target_action": "update_traceability_matrix",
                    "confidence": 0.92
                })
            elif code == "DOC-004" or "Overdue" in title:
                recommendations.append({
                    "title": "Initiate Periodic Document Review Cycle",
                    "priority": "HIGH",
                    "suggested_owner": "Global Quality Assurance Document Owner",
                    "due_date_suggestion": "Within 10 Days",
                    "rationale": "SOP periodic review window has elapsed. Route document revision or periodic review affirmation.",
                    "related_finding": title,
                    "workflow_type": "REMEDIATION_TASK",
                    "target_action": "periodic_review_extension",
                    "confidence": 0.94
                })
            else:
                recommendations.append({
                    "title": f"Remediate {title}",
                    "priority": "MEDIUM",
                    "suggested_owner": "System Administrator",
                    "due_date_suggestion": "Next Scheduled Maintenance Cycle",
                    "rationale": f.get("description", "Address compliance discrepancy."),
                    "related_finding": title,
                    "workflow_type": "REMEDIATION_TASK",
                    "target_action": "general_remediation",
                    "confidence": 0.88
                })
                
        return AgentResult(
            agent=self.name,
            status="completed",
            confidence=0.94,
            findings=[],
            citations=[],
            recommendations=recommendations,
            warnings=[],
            metadata={
                "total_recommendations": len(recommendations)
            }
        )

recommendation_agent = RecommendationAgent()
