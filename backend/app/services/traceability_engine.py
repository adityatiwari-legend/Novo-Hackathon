from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.entities import Requirement, Risk, Document, ComplianceFinding
from backend.app.services.graph_service import get_requirement_trace

_UNSET = object()

class TraceabilityEngine:
    """
    Builds the bidirectional GxP traceability graph and detects compliance gaps.
    Chain:
    Business Need -> URS Requirement -> Risk -> Functional Spec -> Verification -> Result -> Release
    """
    def __init__(self):
        pass

    def build_traceability_matrix(self, db: Session, system_id: str = "SYS-MES-001") -> List[Dict[str, Any]]:
        # Map to graph_service if available, or just return basic requirements
        reqs = db.query(Requirement).filter(Requirement.system_id == system_id).all()
        matrix = []
        
        # Use graph_service to trace
        for req in reqs:
            trace = get_requirement_trace(db, req.requirement_id)
            if not trace:
                trace = {}
            
            # Risk relationship: derived strictly from req.risk_reference, never manufactured
            risk_ref = req.risk_reference
            risk_obj = None
            if risk_ref:
                risk_obj = db.query(Risk).filter(Risk.id == risk_ref).first()
            
            risk_id = risk_ref if risk_ref else "NOT_EVIDENCED"
            risk_level = risk_obj.risk_level if risk_obj else "NOT_EVIDENCED"
            
            # Functional specification module: query trace/relationships, never manufacture FS-MOD-xxx
            fs_nodes = [node for node in trace.get("related_nodes", []) if node.get("type") in ("FUNCTIONAL_SPEC", "FS_MODULE")]
            fs_module = fs_nodes[0].get("id") if fs_nodes else "NOT_EVIDENCED"
            
            # Verification reference and status: derived strictly from req and verified tests
            tests = [node for node in trace.get("related_nodes", []) if node.get("type") == "TEST_CASE"]
            if req.status == "VERIFIED" or (tests and any(t.get("status") in ("VERIFIED", "PASSED", "MET") for t in tests)):
                test_status = "COMPLETE"
            else:
                test_status = "NOT_PERFORMED"
                
            verification_id = req.verification_reference if req.verification_reference else "NOT_EVIDENCED"
            
            matrix.append({
                "requirement_id": req.requirement_id,
                "requirement_text": req.text,
                "type": req.type,
                "fs_module": fs_module,
                "risk_id": risk_id,
                "risk_level": risk_level,
                "residual_risk_state": "NOT RATED / UNACCEPTED" if risk_level != "NOT_EVIDENCED" else "NOT_EVIDENCED",
                "verification_id": verification_id,
                "verification_status": test_status,
                "implementation_status": "COMPLETE" if test_status == "COMPLETE" else "NOT_MET",
                "release_blocker": test_status != "COMPLETE",
                "source_document_id": req.source_document_id or "Unknown",
                "evidence_id": req.evidence_id or "Unknown",
                "source_locator": f"p.{req.source_page} {req.source_section}" if req.source_page else "Unknown"
            })
            
        return matrix

    def detect_traceability_gaps(self, db: Session, system_id: str = "SYS-MES-001", risk_threshold: Any = _UNSET) -> List[Dict[str, Any]]:
        matrix = self.build_traceability_matrix(db, system_id)
        gaps = []

        unverified = [m for m in matrix if m["verification_status"] == "NOT_PERFORMED"]
        if unverified:
            source_docs = list(set([m["source_document_id"] for m in unverified if m["source_document_id"] != "Unknown"]))
            gaps.append({
                "gap_code": f"GAP-TRC-{len(gaps)+1:03d}",
                "title": f"Intended-Use Verification Not Performed ({len(unverified)} Requirements)",
                "description": f"{len(unverified)} requirements have verification status marked as 'NOT_PERFORMED'.",
                "severity": "CRITICAL",
                "source_document": source_docs[0] if source_docs else "Unknown",
                "source_section": "Verification Status",
                "source_page": unverified[0]["source_locator"] if unverified else "Unknown",
                "affected_count": len(unverified),
                "affected_items": [m["requirement_id"] for m in unverified]
            })

        if risk_threshold is _UNSET:
            from backend.app.services.audit_engine import CORE_25_AUDIT_SPECS
            da03_spec = next((s for s in CORE_25_AUDIT_SPECS if s.get("q_id") == "DA-03-005"), None)
            if da03_spec and "rule_parameters" in da03_spec and "risk_threshold" in da03_spec["rule_parameters"]:
                effective_threshold = da03_spec["rule_parameters"]["risk_threshold"]
            else:
                effective_threshold = None
        else:
            effective_threshold = risk_threshold

        if effective_threshold is not None:
            from backend.app.models.entities import Risk
            unrated_risks = db.query(Risk).filter(Risk.system_id == system_id, Risk.score >= effective_threshold).all()
            if unrated_risks:
                source_docs = list(set([r.source_document_id for r in unrated_risks if r.source_document_id]))
                gaps.append({
                    "gap_code": f"GAP-TRC-{len(gaps)+1:03d}",
                    "title": "Residual Risk Not Rated or Accepted by Quality Unit",
                    "description": f"{len(unrated_risks)} requirements remain with residual risk unmitigated (score >= {effective_threshold}) without formal Quality Unit acceptance.",
                    "severity": "CRITICAL",
                    "source_document": source_docs[0] if source_docs else "Unknown",
                    "source_section": "Residual Risk Evaluation",
                    "source_page": "Unknown",
                    "affected_count": len(unrated_risks),
                    "affected_items": [r.id for r in unrated_risks]
                })
        else:
            gaps.append({
                "gap_code": f"GAP-TRC-{len(gaps)+1:03d}",
                "title": "Residual Risk Evaluation NOT_EVALUABLE (Unconfigured Threshold)",
                "description": "Risk threshold parameter is missing in system audit configuration. Cannot evaluate residual risks.",
                "severity": "HIGH",
                "source_document": "System Configuration",
                "source_section": "Risk Configuration",
                "source_page": "Unknown",
                "affected_count": 0,
                "affected_items": []
            })

        from backend.app.models.entities import ReleaseGate
        handover_gate = db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id, ReleaseGate.gate_code == "G6").first()
        if handover_gate and handover_gate.status != "MET":
            gaps.append({
                "gap_code": f"GAP-TRC-{len(gaps)+1:03d}",
                "title": "Operational Handover Incomplete",
                "description": handover_gate.blocking_reason or "Operational handover is blocked.",
                "severity": "HIGH",
                "source_document": handover_gate.evidence_doc or "Unknown",
                "source_section": "Operational Status",
                "source_page": "Unknown",
                "affected_count": 1,
                "affected_items": ["G6"]
            })

        return gaps

traceability_engine = TraceabilityEngine()
