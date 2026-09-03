from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import Document, ComplianceFinding, Recommendation, create_audit_log
from backend.app.services.compliance_engine import compliance_engine

class ContinuousComplianceMonitor:
    def __init__(self):
        self.simulation_active = False

    def trigger_document_expiration_event(self, db: Session, system_id: str = "SYS-LIMS-001") -> Dict[str, Any]:
        """
        Simulates an asynchronous background compliance trigger:
        SOP_Document_Management.docx periodic review expires.
        Transitions document status to 'Overdue', re-evaluates compliance (82% -> 76%),
        adds finding and recommendation, logs tamper-evident audit event.
        """
        # Find SOP document
        doc = db.query(Document).filter(
            Document.system_id == system_id,
            Document.title.ilike("%SOP_Document_Management%")
        ).first()
        
        if not doc:
            # Fallback to any SOP
            doc = db.query(Document).filter(Document.document_type == "SOP").first()
            
        doc_title = doc.title if doc else "SOP_Document_Management.docx"
        if doc:
            doc.status = "Overdue"
            db.commit()
            
        # Re-evaluate compliance
        eval_result = compliance_engine.evaluate_system(db, system_id)
        new_score = eval_result["readiness_score"]  # 82 - 6 = 76!
        
        finding_title = f"Document Review Overdue: {doc_title}"
        existing_finding = db.query(ComplianceFinding).filter(
            ComplianceFinding.system_id == system_id,
            ComplianceFinding.title == finding_title
        ).first()
        
        if not existing_finding:
            finding = ComplianceFinding(
                system_id=system_id,
                document_id=doc.id if doc else None,
                title=finding_title,
                description=(
                    f"Continuous Compliance Monitor detected that {doc_title} exceeded its "
                    "24-month periodic review cycle. Under GxP SOP-DM-001, operating with an overdue SOP "
                    "constitutes a compliance deviation."
                ),
                severity="MEDIUM",
                status="OPEN",
                confidence=0.97,
                source_citations=[{"document": doc_title, "section": "Section 2: Periodic Review"}],
                recommended_action="Initiate formal periodic review and extension workflow."
            )
            db.add(finding)
            
            rec = Recommendation(
                system_id=system_id,
                source_agent="continuous_monitoring_simulation",
                title=f"Renew Expired SOP: {doc_title}",
                description="Route SOP to Document Owner and QA for biennial periodic review affirmation.",
                priority="HIGH",
                rationale="Document lifecycle overdue violates EU Annex 11 / 21 CFR Part 11 periodic maintenance.",
                suggested_owner="Global Quality Assurance Document Owner",
                status="PROPOSED",
                confidence=0.96
            )
            db.add(rec)
            db.commit()
            
        # Log Audit Trail
        create_audit_log(
            db=db,
            actor_type="SYSTEM",
            actor_id="continuous_compliance_monitor",
            action="Triggered Periodic Review Expiration Event",
            entity_type="DOCUMENT",
            entity_id=doc.id if doc else "DOC-SOP-DM-001",
            details={
                "event": "SOP_PERIODIC_REVIEW_OVERDUE",
                "document": doc_title,
                "previous_readiness": 82,
                "new_readiness": new_score,
                "score_delta": -6
            },
            agent_name="continuous_compliance_monitor"
        )
        
        self.simulation_active = True
        return {
            "event": "SOP_PERIODIC_REVIEW_EXPIRED",
            "system_id": system_id,
            "document_affected": doc_title,
            "previous_readiness": 82,
            "new_readiness": new_score,
            "notification": f"New compliance gap detected: {doc_title} is overdue for periodic review. Readiness score decreased to {new_score}%."
        }

    def reset_simulation(self, db: Session, system_id: str = "SYS-LIMS-001") -> Dict[str, Any]:
        """Resets the document status back to Effective and removes simulated findings."""
        doc = db.query(Document).filter(
            Document.system_id == system_id,
            Document.title.ilike("%SOP_Document_Management%")
        ).first()
        if doc:
            doc.status = "Effective"
            
        db.query(ComplianceFinding).filter(
            ComplianceFinding.title.ilike("%Document Review Overdue%")
        ).delete()
        db.query(Recommendation).filter(
            Recommendation.title.ilike("%Renew Expired SOP%")
        ).delete()
        db.commit()
        
        self.simulation_active = False
        return {"status": "reset", "readiness_score": 82}

continuous_monitor = ContinuousComplianceMonitor()
