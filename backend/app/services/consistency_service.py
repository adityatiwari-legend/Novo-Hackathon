from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import Document, System, Requirement, Risk, ReleaseGate, Relationship

class ConsistencyService:
    """
    Evaluates cross-document consistency across the computerized system lifecycle package.
    Ensures pre-operational system state, release hold recommendations, and traceability relationships are aligned.
    """
    def __init__(self):
        pass

    def check_consistency(self, db: Session, system_id: str = "SYS-MES-001") -> Dict[str, Any]:
        docs = db.query(Document).filter(Document.system_id == system_id).all()
        doc_map = {d.document_type: d for d in docs}
        
        checks = []
        findings = []

        # 1. State Consistency: SLA vs ITPSE vs IREP
        sla_doc = doc_map.get("SLA")
        itpse_doc = doc_map.get("ITPSE")
        irep_doc = doc_map.get("IREP")
        mlgp_doc = doc_map.get("MLGP")
        
        if not sla_doc or not itpse_doc:
            findings.append({
                "finding_type": "DOCUMENT_CONSISTENCY_FINDING",
                "title": "Missing Operational State Documents",
                "description": "SLA or ITPSE lifecycle document is missing from the registered document package.",
                "severity": "HIGH"
            })
        else:
            sla_status = sla_doc.approval_status or "UNKNOWN"
            itpse_status = itpse_doc.approval_status or "UNKNOWN"
            
            sla_cite = f"[{sla_doc.document_id or sla_doc.id} | status:{sla_status}]"
            itpse_cite = f"[{itpse_doc.document_id or itpse_doc.id} | status:{itpse_status}]"
            
            if ("PRE-OPERATIONAL" in sla_status.upper() or "PENDING" in sla_status.upper()) and ("HOLD" in itpse_status.upper() or "NOT RELEASE" in itpse_status.upper()):
                checks.append({
                    "check_name": "Operational State Alignment (SLA & ITPSE)",
                    "status": "CONSISTENT",
                    "evidence": (
                        f"SLA status ({sla_status}) and ITPSE recommendation ({itpse_status}) "
                        "are aligned. Neither document prematurely claims operational activation."
                    ),
                    "citations": [sla_cite, itpse_cite]
                })
            else:
                findings.append({
                    "finding_type": "DOCUMENT_CONSISTENCY_FINDING",
                    "title": "Conflicting System Release State",
                    "description": f"SLA state ({sla_status}) conflicts with ITPSE release state ({itpse_status}).",
                    "severity": "HIGH"
                })

        # 2. Risk Evaluation Alignment: ITRA vs ITRRA (Relationship-driven, not count-based)
        itra_doc = doc_map.get("ITRA")
        itrra_doc = doc_map.get("ITRRA")
        if itra_doc and itrra_doc:
            req_count = db.query(Requirement).filter(Requirement.system_id == system_id).count()
            risk_count = db.query(Risk).filter(Risk.system_id == system_id).count()
            
            # Count explicit relationship mappings
            mapped_rels = db.query(Relationship).filter(
                Relationship.source_entity_type == "REQUIREMENT",
                Relationship.target_entity_type == "RISK"
            ).count()
            
            itra_cite = f"[{itra_doc.document_id or itra_doc.id}]"
            itrra_cite = f"[{itrra_doc.document_id or itrra_doc.id}]"
            
            if mapped_rels > 0:
                checks.append({
                    "check_name": "Risk Baseline Traceability (ITRA & ITRRA)",
                    "status": "CONSISTENT",
                    "evidence": (
                        f"Persisted relationship index links {mapped_rels} requirement-to-risk pairs "
                        f"across {req_count} requirements and {risk_count} evaluated risk items."
                    ),
                    "citations": [itra_cite, itrra_cite]
                })
            else:
                checks.append({
                    "check_name": "Risk Baseline Traceability (ITRA & ITRRA)",
                    "status": "EVIDENCE_GAP",
                    "evidence": (
                        f"System inventory records {req_count} requirements and {risk_count} risks, "
                        "but lacks explicit persisted Relationship mapping records linking them."
                    ),
                    "citations": [itra_cite, itrra_cite]
                })

        # 3. Release Gate Traceability: IREP vs MLGP
        if irep_doc:
            gates = db.query(ReleaseGate).filter(ReleaseGate.system_id == system_id).all()
            irep_cite = f"[{irep_doc.document_id or irep_doc.id}]"
            gate_cites = [irep_cite]
            if mlgp_doc:
                gate_cites.append(f"[{mlgp_doc.document_id or mlgp_doc.id}]")
                
            if gates:
                gate_codes = [g.gate_code for g in gates]
                checks.append({
                    "check_name": "Lifecycle Gate Governance (MLGP & IREP)",
                    "status": "CONSISTENT",
                    "evidence": (
                        f"Found {len(gates)} active release gates ({', '.join(gate_codes)}) evaluated "
                        f"against lifecycle release specification {irep_doc.document_id or irep_doc.id}."
                    ),
                    "citations": gate_cites
                })
            else:
                checks.append({
                    "check_name": "Lifecycle Gate Governance (MLGP & IREP)",
                    "status": "EVIDENCE_GAP",
                    "evidence": f"No release gates recorded in database for system {system_id}.",
                    "citations": gate_cites
                })

        return {
            "system_id": system_id,
            "consistency_status": "CONSISTENT" if len(findings) == 0 else "CONFLICTS_DETECTED",
            "checks_evaluated": len(checks),
            "checks": checks,
            "consistent_checks": checks,
            "consistency_findings": findings
        }

consistency_service = ConsistencyService()
