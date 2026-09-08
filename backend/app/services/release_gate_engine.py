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

    # Configuration-driven gate definitions
    GATE_CONFIG = {
        "G1": {"blocking": True, "severity": "MEDIUM", "critical": False},
        "G2": {"blocking": True, "severity": "MEDIUM", "critical": False},
        "G3": {"blocking": True, "severity": "HIGH", "critical": False},
        "G4": {"blocking": True, "severity": "HIGH", "critical": False},
        "G5": {"blocking": True, "severity": "CRITICAL", "critical": True},
        "G6": {"blocking": True, "severity": "CRITICAL", "critical": True},
    }

    def evaluate_release_gates(self, db: Session, system_id: str = "SYS-MES-001") -> Dict[str, Any]:
        gates_in_db = db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id).order_by(ReleaseGate.gate_code).all()
        
        eval_gates = []
        for g in gates_in_db:
            gate_conf = self.GATE_CONFIG.get(g.gate_code, {"critical": False, "blocking": False, "severity": "MEDIUM"})
            is_critical = gate_conf.get("critical", False)
            
            # Map status handling spaces/underscores for consistency
            normalized_status = g.status.upper().replace(" ", "_") if g.status else "UNKNOWN"
            
            eval_gates.append({
                "gate_code": g.gate_code,
                "gate_name": g.gate_name or f"Gate {g.gate_code}",
                "status": g.status,
                "evidence_doc": g.evidence_doc,
                "evidence_section": g.evidence_section,
                "blocking_reason": g.blocking_reason,
                "critical": is_critical
            })

        not_met_gates = [g for g in eval_gates if g["status"] and g["status"].upper().replace(" ", "_") in ["NOT_MET", "BLOCKED", "HOLD"]]
        
        # Posture Calculation
        critical_blocked = any(g["critical"] for g in not_met_gates)
        non_critical_blocked = any(not g["critical"] for g in not_met_gates)
        
        if critical_blocked:
            overall_decision = "HOLD"
        elif non_critical_blocked:
            overall_decision = "CONDITIONAL"
        elif len(eval_gates) == 0:
            overall_decision = "DEFERRED"  # No gates configured/evaluated
        else:
            overall_decision = "GO"
            
        lifecycle_status = "PRE-OPERATIONAL / NOT ACTIVATED" if overall_decision in ["HOLD", "DEFERRED"] else "OPERATIONAL"
        
        return {
            "system_id": system_id,
            "overall_decision": overall_decision,
            "lifecycle_status": lifecycle_status,
            "gates_evaluated": len(eval_gates),
            "met_gates_count": len(eval_gates) - len(not_met_gates),
            "blocked_gates_count": len(not_met_gates),
            "gates": eval_gates,
            "blocking_reasons": [
                f"[{g['gate_code']}] {g['blocking_reason']}" for g in not_met_gates if g["blocking_reason"]
            ]
        }

release_gate_engine = ReleaseGateEngine()
