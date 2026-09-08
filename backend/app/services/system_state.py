from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.entities import System, Document, EvidenceItem, ComplianceFinding, ReleaseGate

class SystemStateService:
    def __init__(self, db: Session):
        self.db = db

    def get_system_state(self, system_id: str) -> Dict[str, Any]:
        """
        Returns the canonical state of a given system.
        """
        sys = self.db.query(System).filter(System.id == system_id).first()
        if not sys:
            return None
            
        docs = self.db.query(Document).filter(Document.system_id == system_id).all()
        findings = self.db.query(ComplianceFinding).filter(ComplianceFinding.system_id == system_id).all()
        gates = self.db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id).all()
        evidence_items = self.db.query(EvidenceItem).join(Document, EvidenceItem.document_id == Document.id).filter(Document.system_id == system_id).all()
        
        open_findings = [f for f in findings if f.status != "CLOSED"]
        blocked_gates = [g for g in gates if g.status in ["NOT_MET", "BLOCKED"]]
        
        return {
            "system_id": sys.id,
            "name": sys.name,
            "lifecycle_status": sys.lifecycle_status,
            "readiness_score": sys.readiness_score,
            "release_recommendation": sys.release_recommendation,
            "document_count": len(docs),
            "evidence_item_count": len(evidence_items),
            "open_findings_count": len(open_findings),
            "blocked_gates_count": len(blocked_gates),
            "open_findings": [{"id": f.id, "title": f.title, "severity": f.severity} for f in open_findings],
            "blocked_gates": [{"code": g.gate_code, "name": g.gate_name, "reason": g.blocking_reason} for g in blocked_gates]
        }
