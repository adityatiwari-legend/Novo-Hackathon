from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.schemas.domain import AgentResult
from backend.app.models.entities import Risk

class RiskAgent:
    def __init__(self):
        self.name = "risk_agent"

    def run(self, db: Session, findings: List[Dict[str, Any]], system_id: str = "SYS-MES-001") -> AgentResult:
        # Query actual database Risk records
        db_risks = db.query(Risk).filter(Risk.system_id == system_id).all()
        
        risks = []
        for r in db_risks:
            risks.append({
                "risk_id": r.id,
                "finding_title": "Risk Record",
                "risk_level": r.risk_level,
                "status": "OPEN",
                "owner": "Unknown",
                "control_mapping": r.control_mapping,
                "residual_state": "Unknown",
                "impact_type": r.impact_type,
                "likelihood": r.likelihood,
                "impact": r.impact,
                "score": r.score if r.score else 0,
                "rationale": r.rationale
            })
            
        # Aggregate highest risk level
        highest = "LOW"
        for r in risks:
            if r["risk_level"] == "CRITICAL":
                highest = "CRITICAL"
                break
            elif r["risk_level"] == "HIGH":
                highest = "HIGH"
            elif r["risk_level"] == "MEDIUM" and highest != "HIGH":
                highest = "MEDIUM"
                
        return AgentResult(
            agent=self.name,
            status="completed",
            confidence=0.95,
            findings=[],
            citations=[],
            recommendations=[],
            warnings=[] if highest in ["LOW", "MEDIUM"] else [f"System risk posture elevated: Highest finding risk is {highest}"],
            metadata={
                "highest_risk_level": highest,
                "total_risks": len(risks),
                "risks": risks
            }
        )

risk_agent = RiskAgent()
