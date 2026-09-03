from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.schemas.domain import AgentResult

class RiskAgent:
    def __init__(self):
        self.name = "risk_agent"

    def run(self, db: Session, findings: List[Dict[str, Any]], system_id: str = "SYS-LIMS-001") -> AgentResult:
        risks = []
        
        for finding in findings:
            code = finding.get("check_code", "")
            severity = finding.get("severity", "MEDIUM")
            
            if code == "DOC-003" or "QA Approval" in finding.get("title", ""):
                # Critical/High GxP Risk
                risks.append({
                    "finding_title": finding["title"],
                    "risk_level": "HIGH",
                    "impact_type": "GxP / Regulatory Integrity",
                    "likelihood": "High",
                    "impact": "High",
                    "score": 16,  # 4 x 4
                    "rationale": (
                        "Lack of formal Quality Unit (QA) sign-off on the User Requirements Specification "
                        "invalidates system qualification rigor. Under 21 CFR Part 11 and EU Annex 11, "
                        "an unapproved URS cannot serve as a legally defensible baseline for analytical release."
                    ),
                    "control_mapping": "ICH Q9 Quality Risk Management & ALCOA+ Attributability (Section 6)"
                })
            elif code == "CHG-001" or "Traceability" in finding.get("title", ""):
                risks.append({
                    "finding_title": finding["title"],
                    "risk_level": "MEDIUM",
                    "impact_type": "Operational / Validation Verification",
                    "likelihood": "Medium",
                    "impact": "Medium",
                    "score": 9,  # 3 x 3
                    "rationale": (
                        "Incomplete traceability between functional user requirements and qualification test scripts "
                        "risks unverified custom workflows escaping detection into production."
                    ),
                    "control_mapping": "GAMP 5 Category 4 Traceability Matrix Matrix-01"
                })
            elif code == "DOC-004" or "Overdue" in finding.get("title", ""):
                risks.append({
                    "finding_title": finding["title"],
                    "risk_level": "MEDIUM",
                    "impact_type": "Compliance Lifecycle",
                    "likelihood": "Medium",
                    "impact": "Medium",
                    "score": 8,
                    "rationale": "Operating computerized systems under expired SOPs risks operator deviation.",
                    "control_mapping": "SOP-DM-001 Section 2 Periodic Review"
                })
            else:
                risks.append({
                    "finding_title": finding["title"],
                    "risk_level": "LOW",
                    "impact_type": "Documentation",
                    "likelihood": "Low",
                    "impact": "Low",
                    "score": 4,
                    "rationale": "Minor documentation formatting or administrative gap.",
                    "control_mapping": "General GxP Documentation Controls"
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
