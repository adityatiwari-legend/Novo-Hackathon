import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.entities import (
    System, Document, ComplianceCheck, ComplianceFinding, Risk, Recommendation, ReleaseGate, Requirement
)

class ComplianceEngine:
    def __init__(self):
        self.rules_path = os.path.join(settings.SEED_DIR, "compliance_rules.json")
        self.checklist_path = os.path.join(settings.SEED_DIR, "compliance_checklist.json")
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.rules_path):
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("rules", [])
        elif os.path.exists(self.checklist_path):
            with open(self.checklist_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def evaluate_system(self, db: Session, system_id: str) -> Dict[str, Any]:
        """
        Runs deterministic compliance rules evaluation across indexed documents.
        Computes deterministic readiness score: Base 100 - sum(failed_rule_penalties)
        """
        system = db.query(System).filter(System.id == system_id).first()
        docs = db.query(Document).filter(Document.system_id == system_id).all()
        doc_types = {d.document_type: d for d in docs}
        
        checks_results = []
        findings = []
        total_penalty = 0

        # Dynamically evaluate rules loaded from compliance_rules.json
        for rule in self.rules:
            check_type = rule.get("check_type")
            params = rule.get("params", {})
            penalty = rule.get("penalty", 0)
            
            status = "FAIL"
            evidence = "Check failed."
            citation = {}
            finding_title = "Compliance Issue"
            finding_desc = rule.get("requirement", "")
            
            if check_type == "DOCUMENT_REQUIRED":
                doc_type = params.get("document_type")
                found = next((d for d in docs if doc_type in d.document_type or doc_type in d.title), None)
                if found:
                    status = "PASS"
                    evidence = f"{found.title} is verified."
                    citation = {"document": found.title, "section": "Metadata"}
                else:
                    evidence = f"Document of type {doc_type} is missing."
                    finding_title = f"Missing Critical Baseline: {doc_type}"
                    finding_desc = f"Mandatory document type {doc_type} not found in the evidence corpus."
                    
            elif check_type == "DOCUMENT_CURRENT":
                overdue_docs = [d for d in docs if d.status == "Overdue"]
                if not overdue_docs:
                    status = "PASS"
                    evidence = "All active documents are current."
                else:
                    titles = [d.title for d in overdue_docs]
                    evidence = f"Overdue documents found: {', '.join(titles)}"
                    finding_title = "Document Review Overdue"
                    finding_desc = f"Documents exceeded periodic review cycle: {', '.join(titles)}"
                    citation = {"documents": titles}
                    
            elif check_type == "REQUIREMENT_HAS_VERIFICATION":
                unique_reqs = db.query(Requirement).filter(Requirement.system_id == system_id).all()
                if not unique_reqs:
                    # In some systems this might be a pass or a fail if no reqs exist, we'll fail to be safe
                    evidence = "No requirements found."
                else:
                    # Using a placeholder for verification check, assuming if 'status' isn't VERIFIED, it's open.
                    missing_verification = [r for r in unique_reqs if not r.verification_reference]
                    if not missing_verification:
                        status = "PASS"
                        evidence = "All requirements have verification references."
                    else:
                        evidence = f"{len(missing_verification)} requirements missing verification."
                        finding_title = "Incomplete Requirements Traceability"
                        finding_desc = f"{len(missing_verification)} requirements missing verification reference."
                        
            elif check_type == "RESIDUAL_RISK_ACCEPTED":
                threshold = params.get("threshold_score", 10)
                high_risks = db.query(Risk).filter(Risk.system_id == system_id, Risk.score >= threshold).all()
                unique_high_risks = {r.id: r for r in high_risks}.values()
                if len(unique_high_risks) == 0:
                    status = "PASS"
                    evidence = f"No unaccepted risks above threshold {threshold}."
                else:
                    evidence = f"Found {len(unique_high_risks)} unaccepted risks above threshold {threshold}."
                    finding_title = "Residual Risks Unmitigated"
                    finding_desc = f"{len(unique_high_risks)} risks remain unmitigated/unaccepted."
                    
            elif check_type == "RELEASE_GATE_MET":
                gate_code = params.get("gate_code")
                gates = db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id, ReleaseGate.gate_code == gate_code).all()
                # Find worst status
                gate = next((g for g in gates if g.status == "NOT MET"), gates[0] if gates else None)
                if gate and gate.status != "NOT MET":
                    status = "PASS"
                    evidence = f"Gate {gate_code} is MET."
                else:
                    reason = gate.blocking_reason if gate and gate.blocking_reason else f"Gate {gate_code} is absent or not met."
                    evidence = f"Gate {gate_code} is {gate.status if gate else 'MISSING'}."
                    finding_title = f"Gate {gate_code} Not Met"
                    finding_desc = reason
            
            else:
                evidence = f"Unsupported check type: {check_type}"
                
            if status == "FAIL":
                total_penalty += penalty
                findings.append({
                    "system_id": system_id,
                    "title": finding_title,
                    "description": finding_desc,
                    "severity": rule.get("severity", "MEDIUM"),
                    "status": "OPEN",
                    "confidence": 1.0,
                    "source_citations": [citation] if citation else [{"document": "System Database", "section": check_type}],
                    "recommended_action": "Remediate to establish compliance."
                })
                
            checks_results.append({
                "check_code": rule.get("id"),
                "category": rule.get("category", "General"),
                "requirement": rule.get("requirement", ""),
                "severity": rule.get("severity", "MEDIUM"),
                "penalty": penalty,
                "status": status,
                "evidence": evidence,
                "citation": citation
            })
                    
        readiness_score = max(0, 100 - total_penalty)

        # Categorize findings by severity
        blocking_findings = [f for f in findings if f.get("severity") == "CRITICAL"]
        high_findings = [f for f in findings if f.get("severity") == "HIGH"]
        medium_findings = [f for f in findings if f.get("severity") == "MEDIUM"]
        low_findings = [f for f in findings if f.get("severity") == "LOW"]

        # Update system record in database
        if system:
            system.readiness_score = readiness_score
            system.last_assessed_at = datetime.now(timezone.utc)

        return {
            "system_id": system_id,
            "readiness_score": readiness_score,
            "confidence": 1.0,
            "total_checks": len(checks_results),
            "passed_checks": len([c for c in checks_results if c["status"] == "PASS"]),
            "failed_checks": len([c for c in checks_results if c["status"] == "FAIL"]),
            "total_penalty": total_penalty,
            "checks": checks_results,
            "findings": findings,
            "blocking_findings": len(blocking_findings),
            "high_findings": len(high_findings),
            "medium_findings": len(medium_findings),
            "low_findings": len(low_findings)
        }

compliance_engine = ComplianceEngine()
