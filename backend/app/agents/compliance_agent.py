from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.services.compliance_engine import compliance_engine
from backend.app.schemas.domain import AgentResult

class ComplianceAgent:
    def __init__(self):
        self.name = "compliance_agent"

    def run(self, db: Session, system_id: str = "SYS-LIMS-001") -> AgentResult:
        eval_result = compliance_engine.evaluate_system(db, system_id)
        
        citations = []
        for check in eval_result["checks"]:
            if check.get("citation"):
                citations.append({
                    "check_code": check["check_code"],
                    "citation": check["citation"]
                })
                
        findings_data = []
        for f in eval_result.get("findings", []):
            if isinstance(f, dict):
                findings_data.append(f)
            else:
                findings_data.append({
                    "id": getattr(f, "id", None),
                    "title": getattr(f, "title", ""),
                    "description": getattr(f, "description", ""),
                    "severity": getattr(f, "severity", "MEDIUM"),
                    "status": getattr(f, "status", "OPEN"),
                    "confidence": getattr(f, "confidence", 0.95),
                    "recommended_action": getattr(f, "recommended_action", None),
                    "source_citations": getattr(f, "source_citations", [])
                })

        return AgentResult(
            agent=self.name,
            status="completed",
            confidence=eval_result.get("confidence", 0.95),
            findings=findings_data,
            citations=citations,
            recommendations=[],
            warnings=[],
            metadata={
                "readiness_score": eval_result["readiness_score"],
                "total_checks": eval_result["total_checks"],
                "passed_checks": eval_result["passed_checks"],
                "failed_checks": eval_result["failed_checks"],
                "checks": eval_result["checks"]
            }
        )

compliance_agent = ComplianceAgent()
