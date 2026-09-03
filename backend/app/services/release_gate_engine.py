from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import ReleaseGate, System

class ReleaseGateEngine:
    """
    Deterministic Release Gate evaluation engine for GxP computerized systems.
    Evaluates gates G1 through G6 based on lifecycle documentation evidence.
    Enforces the rule: If a critical gate (G5, G6) is NOT_MET, release status is strictly HOLD / DEFER.
    """
    def __init__(self):
        pass

    def evaluate_release_gates(self, db: Session, system_id: str = "SYS-MES-001") -> Dict[str, Any]:
        gates_in_db = db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id).order_by(ReleaseGate.gate_code).all()
        
        # Default gates if not yet seeded
        gate_definitions = [
            {
                "gate_code": "G1",
                "gate_name": "Project Inception & Regulatory Scope",
                "status": "MET",
                "evidence_doc": "NL-MES-MLGP-001",
                "evidence_section": "1. Purpose & Scope",
                "blocking_reason": None,
                "critical": False
            },
            {
                "gate_code": "G2",
                "gate_name": "Requirements Baseline Approval",
                "status": "MET",
                "evidence_doc": "NL-MES-URS-001",
                "evidence_section": "1. Executive Summary",
                "blocking_reason": None,
                "critical": False
            },
            {
                "gate_code": "G3",
                "gate_name": "Detailed Design & Specification Freeze",
                "status": "MET",
                "evidence_doc": "NL-MES-FS-001",
                "evidence_section": "1. Module Architecture",
                "blocking_reason": None,
                "critical": False
            },
            {
                "gate_code": "G4",
                "gate_name": "Technical Verification & IQ",
                "status": "MET",
                "evidence_doc": "NL-MES-IREP-001",
                "evidence_section": "2. Technical Verification Status",
                "blocking_reason": "Technical interfaces and IQ passed; intended-use testing pending.",
                "critical": False
            },
            {
                "gate_code": "G5",
                "gate_name": "Release Readiness & Residual Risk Acceptance",
                "status": "NOT_MET",
                "evidence_doc": "NL-MES-IREP-001",
                "evidence_section": "4. Lifecycle Phase Gate Status",
                "blocking_reason": (
                    "Blocked by missing intended-use verification (OV/PfV/UAT not performed), "
                    "unrated residual risks across 49 working high requirements, and deferred VSR."
                ),
                "critical": True
            },
            {
                "gate_code": "G6",
                "gate_name": "Operational Handover & SLA Activation",
                "status": "NOT_MET",
                "evidence_doc": "NL-MES-IREP-001",
                "evidence_section": "4. Lifecycle Phase Gate Status",
                "blocking_reason": "Blocked by incomplete shopfloor training (0 of 250 operators qualified) and unactivated SLA.",
                "critical": True
            }
        ]

        # Use database records if available
        if gates_in_db:
            eval_gates = []
            for g in gates_in_db:
                eval_gates.append({
                    "gate_code": g.gate_code,
                    "gate_name": g.gate_name,
                    "status": g.status,
                    "evidence_doc": g.evidence_doc,
                    "evidence_section": g.evidence_section,
                    "blocking_reason": g.blocking_reason,
                    "critical": g.gate_code in ["G5", "G6"]
                })
        else:
            eval_gates = gate_definitions

        not_met_gates = [g for g in eval_gates if g["status"].upper().replace(" ", "_") in ["NOT_MET", "BLOCKED", "HOLD"]]
        is_blocked = len(not_met_gates) > 0
        
        # Deterministic release decision
        release_recommendation = "HOLD / DEFER - DO NOT RELEASE" if is_blocked else "PROCEED TO RELEASE"
        overall_status = "HOLD / BLOCKED" if is_blocked else "READY"
        
        return {
            "system_id": system_id,
            "overall_decision": release_recommendation,
            "lifecycle_status": "PRE-OPERATIONAL / NOT ACTIVATED",
            "gates_evaluated": len(eval_gates),
            "met_gates_count": len(eval_gates) - len(not_met_gates),
            "blocked_gates_count": len(not_met_gates),
            "gates": eval_gates,
            "blocking_reasons": [
                f"[{g['gate_code']}] {g['blocking_reason']}" for g in not_met_gates if g["blocking_reason"]
            ]
        }

release_gate_engine = ReleaseGateEngine()
