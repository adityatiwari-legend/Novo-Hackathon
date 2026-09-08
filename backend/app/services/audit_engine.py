"""
Deterministic Audit Execution Engine for GxP IT Systems.
Executes the Top 25 GxP IT Audit Checklist against system lifecycle evidence,
computes deterministic scores, evaluates evidence confidence, performs cross-document
comparison against Master IT SOP, and generates actionable findings.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import logging
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    AuditChecklist, AuditQuestion, AuditAssessment, AuditEvidence,
    System, Document, DocumentChunk, ReleaseGate, Risk, ComplianceFinding,
    create_audit_log, EvidenceItem
)
from backend.app.schemas.domain import (
    AuditAssessmentResponse, AuditAssessmentItem, CrossDocComparisonItem,
    CrossDocComparisonResponse
)

logger = logging.getLogger(__name__)

# Core Top 25 Audit Questions configuration with mapping to evidence
CORE_25_AUDIT_SPECS = [
    {
        "seq": 1,
        "q_id": "DA-01-001",
        "phase": "Concept & Business Case",
        "topic": "Intended Use & System Boundary",
        "question": "Walk through the proposed intended use, patient/product decisions supported, and evidence used to draw the GxP system boundary.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Approved concept statement, process diagrams, preliminary GxP assessment with named owners.",
        "check_type": "DOCUMENT_APPROVED",
        "rule_parameters": {"target_document_type": "System Scope"}
    },
    {
        "seq": 2,
        "q_id": "DA-01-003",
        "phase": "Concept & Business Case",
        "topic": "Data Lifecycle & ALCOA+ Protection",
        "question": "Describe the data lifecycle and show where the concept explicitly protects attributable, legible, contemporaneous, original, and accurate data.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Data criticality register, ALCOA+ assessment, data flow map, and technical controls.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["ALCOA", "Data Lifecycle", "URS"]}
    },
    {
        "seq": 3,
        "q_id": "DA-02-001",
        "phase": "User Requirements Specification",
        "topic": "Completeness of GxP User Requirements",
        "question": "Demonstrate that the URS captures all GxP, operational, data integrity, and regulatory expectations with clear acceptance criteria.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Approved URS with unique IDs, testable criteria, and QA signoff.",
        "check_type": "DOCUMENT_APPROVED",
        "rule_parameters": {"target_document_type": "URS"}
    },
    {
        "seq": 4,
        "q_id": "DA-03-001",
        "phase": "Risk Management (GAMP)",
        "topic": "Initial System Risk Assessment & Hazard Identification",
        "question": "Show how system risk assessment differentiated patient-safety, product-quality, and data-integrity harm to establish control rigor.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "System risk assessment (ITRA), hazard statements, severity/probability/detectability scoring.",
        "check_type": "DOCUMENT_APPROVED",
        "rule_parameters": {"target_document_type": "Risk Assessment"}
    },
    {
        "seq": 5,
        "q_id": "DA-03-005",
        "phase": "Risk Management (GAMP)",
        "topic": "Authorized Residual Risk Acceptance",
        "question": "Demonstrate that all high-risk items have verified mitigations and that residual risks are formally accepted by the Quality Unit.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Formal residual risk assessment, signed risk acceptance matrix, QA Unit approval.",
        "check_type": "RESIDUAL_RISK_ACCEPTED",
        "rule_parameters": {"risk_threshold": 10}
    },
    {
        "seq": 6,
        "q_id": "DA-04-001",
        "phase": "Supplier Qualification",
        "topic": "Supplier Audit & Quality Agreement",
        "question": "Confirm that the software supplier (Werum IT Solutions) underwent formal audit, assessment, and has an effective Quality Agreement.",
        "priority": "High",
        "weight": 10,
        "expected_evidence": "Supplier audit report, QA agreement, capability assessment, and escrow agreements.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Supplier", "Werum", "SLA"]}
    },
    {
        "seq": 7,
        "q_id": "DA-07-001",
        "phase": "Installation Qualification (IQ)",
        "topic": "Technical Environment & Installation Verification",
        "question": "Verify that all production hardware, operating systems, database schemas, and network configurations match approved design specs.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Approved IQ protocol, execution logs, discrepancy logs, and signed summary report.",
        "check_type": "DOCUMENT_APPROVED",
        "rule_parameters": {"target_document_type": "Implementation Report"}
    },
    {
        "seq": 8,
        "q_id": "DA-08-001",
        "phase": "Operational Qualification (OQ)",
        "topic": "Functional & Security Control Verification",
        "question": "Show that all automated functions, calculations, security permissions, and error handling operate according to Functional Specs.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Approved OQ protocol, test execution records, security penetration test, and deviation logs.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Implementation Report", "OQ", "Functional"]}
    },
    {
        "seq": 9,
        "q_id": "DA-09-001",
        "phase": "Performance Qualification (PQ / UAT)",
        "topic": "Intended-Use Qualification & Shopfloor Verification (OV / PfV / UAT)",
        "question": "Demonstrate that the system was tested under realistic operating conditions across full packaging workflows by qualified business operators.",
        "priority": "Critical",
        "weight": 25,
        "expected_evidence": "Approved PQ/UAT protocols, executed shopfloor test runs, operator qualification, and signed VSR.",
        "check_type": "RELEASE_GATE_MET",
        "rule_parameters": {"gate_code": "G5"}
    },
    {
        "seq": 10,
        "q_id": "DA-10-001",
        "phase": "Go-Live & Handover",
        "topic": "Operational Handover, Service Level Agreements & Support Readiness",
        "question": "Show that operational support models, SLA tiers, incident response escalation, and administrator handovers are formally approved and activated.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Approved SLA, support handover checklist, incident runbooks, and disaster escalation roster.",
        "check_type": "RELEASE_GATE_MET",
        "rule_parameters": {"gate_code": "G6"}
    },
    {
        "seq": 11,
        "q_id": "DA-10-005",
        "phase": "Go-Live & Handover",
        "topic": "End-User Training & Qualification Records",
        "question": "Demonstrate that all personnel with access to the system are trained on relevant SOPs, data integrity, and system operations.",
        "priority": "High",
        "weight": 15,
        "expected_evidence": "LMS training records, curriculum matrix, competency assessments, and trainer qualifications.",
        "check_type": "TRAINING_COMPLETE",
    },
    {
        "seq": 12,
        "q_id": "DA-10-007",
        "phase": "Go-Live & Handover",
        "topic": "Validation Summary Report (VSR) & Formal Release Gate G5",
        "question": "Confirm that a Validation Summary Report synthesizing all qualification results has received formal Quality Unit sign-off.",
        "priority": "Critical",
        "weight": 25,
        "expected_evidence": "Signed VSR, gate G5 sign-off matrix, deviation summary, and unconditional/conditional release memo.",
        "check_type": "RELEASE_GATE_MET",
        "rule_parameters": {"gate_code": "G5"}
    },
    {
        "seq": 13,
        "q_id": "DA-11-001",
        "phase": "Operations & Periodic Review",
        "topic": "Periodic System Evaluation & Validated State Conclusion",
        "question": "Reconstruct the most recent periodic evaluation from source populations and show how the conclusion that the system remains in a validated state was reached.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Periodic evaluation report (ITPSE), frozen source data for incidents/changes/access, and QA signoff.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Periodic System Evaluation", "ITPSE"]}
    },
    {
        "seq": 14,
        "q_id": "DA-11-005",
        "phase": "Operations & Periodic Review",
        "topic": "Backup, Disaster Recovery & Business Continuity Testing",
        "question": "Walk through the most recent backup and restore test and verify that disaster recovery procedures can restore the validated state within agreed RTO/RPO.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "DR test protocol, restore execution logs, checksum validation, and QA sign-off.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Disaster", "Backup", "Restore", "Implementation Report"]}
    },
    {
        "seq": 15,
        "q_id": "DA-12-001",
        "phase": "Change & Configuration Management",
        "topic": "Production Change Population & Reconciliation",
        "question": "Build the complete population of production changes and reconcile it to approved change tickets, deployment logs, and repo commits.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Change control SOP, ServiceNow ticket extracts, git commit logs, deployment audit trails.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Lifecycle Governance", "Change Management"]}
    },
    {
        "seq": 16,
        "q_id": "DA-12-005",
        "phase": "Change & Configuration Management",
        "topic": "Emergency Change & Post-Implementation Review",
        "question": "Examine the population of emergency and hotfix changes to ensure that retrospective approval and post-release testing were completed within SLA.",
        "priority": "High",
        "weight": 15,
        "expected_evidence": "Emergency change procedure, deviation logs, post-fix verification records.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Emergency Change", "Lifecycle Governance"]}
    },
    {
        "seq": 17,
        "q_id": "DA-13-001",
        "phase": "Incident & Problem Management",
        "topic": "Event Population & GxP Impact Assessment",
        "question": "Reconcile system monitoring alerts, service desk tickets, and audit trail exceptions to formally logged incidents and quality deviations.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Incident SOP, monitoring event extracts, GxP impact assessment criteria, and QA oversight records.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Incident Triage", "SLA"]}
    },
    {
        "seq": 18,
        "q_id": "DA-13-005",
        "phase": "Incident & Problem Management",
        "topic": "CAPA Linkage & Root Cause Analysis",
        "question": "Trace recurrent incidents or critical defects to root-cause investigation and verified CAPA effectiveness.",
        "priority": "High",
        "weight": 15,
        "expected_evidence": "Quality deviation records, Ishikawa/5-Why root cause diagrams, CAPA effectiveness checks.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["CAPA Management"]}
    },
    {
        "seq": 19,
        "q_id": "DA-02-005",
        "phase": "User Requirements Specification",
        "topic": "Audit Trail & Electronic Signature Compliance (Part 11 / Annex 11)",
        "question": "Show that the audit trail is secure, computer-generated, time-stamped, and captures user identity, prior value, new value, and reason for change.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Audit trail functional specs, test scripts verifying immutability, and review procedures.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Audit Trail", "Signature", "URS"]}
    },
    {
        "seq": 20,
        "q_id": "DA-05-001",
        "phase": "Functional Design",
        "topic": "Functional Specification & Architecture Modularity",
        "question": "Demonstrate that functional specifications trace directly to user requirements and detail all interfaces, algorithms, and batch logic.",
        "priority": "High",
        "weight": 15,
        "expected_evidence": "Approved FS/DS, interface control documents, and requirement traceability matrix.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Functional", "URS"]}
    },
    {
        "seq": 21,
        "q_id": "DA-06-001",
        "phase": "Configuration & Development",
        "topic": "Configuration Management & Repository Control",
        "question": "Verify that all configuration files, master recipe parameters, and source code are under strict version control in restricted repositories.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Git repository access logs, branching policy, configuration specification, peer code reviews.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Lifecycle Governance"]}
    },
    {
        "seq": 22,
        "q_id": "DA-14-001",
        "phase": "Decommissioning & Data Retention",
        "topic": "Data Retention, Archival & Retrieval Readability",
        "question": "Show that electronic batch records and audit trails can be retained and retrieved in human-readable format throughout the statutory retention period.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "Archival policy, long-term readability validation, migration strategy, PDF/A conversion checks.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Archival", "Retention", "Lifecycle"]}
    },
    {
        "seq": 23,
        "q_id": "DA-02-010",
        "phase": "User Requirements Specification",
        "topic": "Role-Based Access Control & Segregation of Duties",
        "question": "Verify that user authorization enforces least privilege, prevents self-approval of batch records, and segregates administrator privileges.",
        "priority": "Critical",
        "weight": 20,
        "expected_evidence": "RBAC matrix, active directory integration spec, segregation of duties policy.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Role-Based Access", "URS-009"]}
    },
    {
        "seq": 24,
        "q_id": "DA-08-010",
        "phase": "Operational Qualification (OQ)",
        "topic": "Automated Interface Verification (ERP / SCADA / Serialization)",
        "question": "Demonstrate that data exchanges between MES, SAP ERP, and shopfloor packaging equipment preserve accuracy, checksums, and error alerts.",
        "priority": "High",
        "weight": 15,
        "expected_evidence": "Interface test protocols, message queue monitoring, failed-transaction reconciliation logs.",
        "check_type": "DOCUMENT_EXISTS",
        "rule_parameters": {"keywords": ["Interface Testing", "Implementation Report"]}
    },
    {
        "seq": 25,
        "q_id": "DA-10-025",
        "phase": "Go-Live & Handover",
        "topic": "Release Gate Checklist Reconciliation & Regulatory Readiness",
        "question": "Reconcile all lifecycle gate deliverables (G1 through G6) to verify no unapproved waivers or unmitigated GxP risks exist.",
        "priority": "Critical",
        "weight": 25,
        "expected_evidence": "Completed release gate checklist, Quality Unit sign-off, regulatory readiness memo.",
        "check_type": "RELEASE_GATE_MET",
        "rule_parameters": {"gate_code": "G5"}
    }
]


class AuditEngine:
    def __init__(self):
        self.checklist_id = "CKL-TOP25-CORE"

    def execute_audit(
        self,
        db: Session,
        system_id: str = "SYS-MES-001",
        checklist_id: str = "CKL-TOP25-CORE",
        weights_override: Optional[Dict[str, float]] = None
    ) -> AuditAssessmentResponse:
        """
        Executes the Top 25 Audit Checklist against the target system deterministically.
        Calculates scores using: PASS=100, PARTIAL=50, FAIL=0, NOT_EVIDENCED=0.
        """
        # Score mappings (deterministic)
        default_score_map = {
            "PASS": 100.0,
            "PARTIAL": 50.0,
            "FAIL": 0.0,
            "NOT_EVIDENCED": 0.0,
            "NOT_APPLICABLE": 100.0
        }
        score_map = weights_override or default_score_map

        total_weight = 0.0
        weighted_score = 0.0

        passed_count = 0
        partial_count = 0
        failed_count = 0
        not_evidenced_count = 0
        na_count = 0

        critical_findings_count = 0
        high_findings_count = 0
        medium_findings_count = 0
        low_findings_count = 0

        items: List[AuditAssessmentItem] = []
        findings: List[Dict[str, Any]] = []
        lifecycle_gaps: List[Dict[str, Any]] = []

        for spec in CORE_25_AUDIT_SPECS:
            weight = spec["weight"]
            priority = spec.get("priority", "MEDIUM")
            
            # Evaluate dynamically
            eval_result = self._evaluate_rule(db, system_id, spec)
            status, quality, confidence, citations, observed, gap, severity, recommendation = eval_result

            # Counting
            if status == "PASS":
                passed_count += 1
            elif status == "PARTIAL":
                partial_count += 1
            elif status == "FAIL":
                failed_count += 1
            elif status == "NOT_EVIDENCED":
                not_evidenced_count += 1
            elif status == "NOT_APPLICABLE":
                na_count += 1

            if status in ["FAIL", "PARTIAL"]:
                if severity == "CRITICAL":
                    critical_findings_count += 1
                elif severity == "HIGH":
                    high_findings_count += 1
                elif severity == "MEDIUM":
                    medium_findings_count += 1
                else:
                    low_findings_count += 1

                # Add structured finding
                f_entry = {
                    "question_id": spec["q_id"],
                    "sequence": spec["seq"],
                    "title": f"Audit Finding [{spec['q_id']}]: {spec['topic']}",
                    "severity": severity,
                    "status": status,
                    "gap": gap,
                    "risk": severity,
                    "recommendation": recommendation,
                    "citations": citations
                }
                findings.append(f_entry)

                if gap:
                    lifecycle_gaps.append({
                        "phase": spec["phase"],
                        "topic": spec["topic"],
                        "gap": gap,
                        "recommendation": recommendation
                    })

            # Math calculation (deterministic)
            item_points = score_map.get(status, 0.0)
            weighted_score += (weight * item_points)
            total_weight += weight

            item = AuditAssessmentItem(
                sequence=spec["seq"],
                question_id=spec["q_id"],
                priority=priority,
                lifecycle_phase=spec["phase"],
                control_topic=spec["topic"],
                audit_question=spec["question"],
                status=status,
                evidence_quality=quality,
                confidence=confidence,
                evidence_citations=citations,
                expected_controls=spec["expected_evidence"],
                observed_evidence=observed,
                gap_description=gap,
                risk_level=severity,
                recommendation=recommendation,
                benchmark_note=spec.get("benchmark")
            )
            items.append(item)

        overall_readiness_score = round(weighted_score / total_weight, 1) if total_weight > 0 else 0.0

        # Save to database
        assessment = AuditAssessment(
            system_id=system_id,
            checklist_id=checklist_id,
            assessed_at=datetime.now(timezone.utc),
            readiness_score=overall_readiness_score,
            total_questions=len(CORE_25_AUDIT_SPECS),
            passed_count=passed_count,
            partial_count=partial_count,
            failed_count=failed_count,
            not_evidenced_count=not_evidenced_count,
            na_count=na_count,
            critical_findings_count=critical_findings_count,
            high_findings_count=high_findings_count,
            medium_findings_count=medium_findings_count,
            low_findings_count=low_findings_count,
            items_json=[i.model_dump() for i in items],
            findings_json=findings,
            lifecycle_gaps_json=lifecycle_gaps,
            status="COMPLETED"
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # Record tamper-evident audit log
        create_audit_log(
            db=db,
            actor_type="AGENT",
            actor_id="audit_engine",
            action="AUDIT_CHECKLIST_EXECUTED",
            entity_type="AUDIT_ASSESSMENT",
            entity_id=assessment.id,
            details={
                "system_id": system_id,
                "checklist_id": checklist_id,
                "readiness_score": overall_readiness_score,
                "passed": passed_count,
                "failed": failed_count,
                "partial": partial_count,
                "critical_findings": critical_findings_count
            },
            agent_name="audit_engine"
        )

        return AuditAssessmentResponse(
            id=assessment.id,
            system_id=assessment.system_id,
            checklist_id=assessment.checklist_id,
            assessed_at=assessment.assessed_at,
            readiness_score=assessment.readiness_score,
            total_questions=assessment.total_questions,
            passed_count=assessment.passed_count,
            partial_count=assessment.partial_count,
            failed_count=assessment.failed_count,
            not_evidenced_count=assessment.not_evidenced_count,
            na_count=assessment.na_count,
            critical_findings_count=assessment.critical_findings_count,
            high_findings_count=assessment.high_findings_count,
            medium_findings_count=assessment.medium_findings_count,
            low_findings_count=assessment.low_findings_count,
            items=[AuditAssessmentItem(**i) for i in assessment.items_json],
            findings=assessment.findings_json,
            lifecycle_gaps=assessment.lifecycle_gaps_json,
            status=assessment.status
        )

    def _evaluate_rule(self, db: Session, system_id: str, spec: dict):
        check_type = spec.get("check_type", "UNKNOWN_CHECK")
        rule_params = spec.get("rule_parameters", {})
        status = "UNKNOWN"
        evidence_quality = "Missing"
        confidence = 0.5
        citations = []
        observed = "No sufficient evidence found."
        gap = None
        severity = spec.get("priority", "MEDIUM").upper()
        recommendation = "Investigate missing evidence."

        candidate_evidence = db.query(EvidenceItem).filter(
            EvidenceItem.text.ilike(f"%{spec['topic']}%")
        ).all()
        for ce in candidate_evidence[:2]:
            citations.append(f"[{ce.document_id} | p.{ce.page}]")

        if check_type == "DOCUMENT_APPROVED":
            doc_type = rule_params.get("target_document_type", "")
            docs = db.query(Document).filter(
                Document.system_id == system_id,
                Document.title.ilike(f"%{doc_type}%")
            ).all()
            if not docs:
                status = "FAIL"
                gap = f"Required document '{doc_type}' is missing."
                observed = f"No document matching '{doc_type}' exists."
                recommendation = f"Create and approve {doc_type}."
            else:
                approved = [d for d in docs if d.status == "Effective" or d.approval_status == "Approved"]
                if approved:
                    status = "PASS"
                    evidence_quality = "Found"
                    confidence = 0.95
                    observed = f"Document '{doc_type}' is approved."
                    gap = None
                    citations.append(f"[{approved[0].id} | {approved[0].title}]")
                else:
                    status = "PARTIAL"
                    evidence_quality = "Partial"
                    gap = f"Document '{doc_type}' exists but is not approved."
                    observed = f"Document '{docs[0].title}' is in {docs[0].status} state."
                    recommendation = f"Approve the {doc_type} document."
                    citations.append(f"[{docs[0].id} | {docs[0].title}]")

        elif check_type == "RELEASE_GATE_MET":
            gate_code = rule_params.get("gate_code", "")
            gate = db.query(ReleaseGate).filter(
                ReleaseGate.system_id == system_id,
                ReleaseGate.gate_code == gate_code
            ).first()
            if not gate:
                status = "UNKNOWN"
                gap = f"Release gate {gate_code} not found."
            elif gate.status == "MET":
                status = "PASS"
                observed = f"Release gate {gate_code} is MET."
                gap = None
                evidence_quality = "Found"
            elif gate.status in ["BLOCKED", "NOT MET", "NOT_MET"]:
                status = "FAIL"
                gap = gate.blocking_reason or f"Gate {gate_code} is blocked."
                observed = f"Gate {gate_code} is {gate.status}."
                evidence_quality = "Conflicting"
                if gate.evidence_doc:
                    citations.append(f"[{gate.evidence_doc}]")
            else:
                status = "PARTIAL"
                gap = f"Gate {gate_code} is {gate.status}."
                observed = f"Gate {gate_code} is {gate.status}."
                
        elif check_type == "RESIDUAL_RISK_ACCEPTED":
            if "risk_threshold" not in rule_params:
                return ("NOT_EVALUABLE", "Missing", 0.0, [], "Rule configuration error: missing risk_threshold in rule_parameters", "Missing risk threshold configuration", severity, "Configure explicit risk_threshold")
            threshold = rule_params["risk_threshold"]
            high_risks = db.query(Risk).filter(
                Risk.system_id == system_id,
                Risk.score >= threshold
            ).all()
            if high_risks:
                status = "FAIL"
                gap = f"Found {len(high_risks)} unmitigated risks at or above threshold {threshold}."
                observed = f"Residual risk is unrated or unapproved for {len(high_risks)} items (threshold={threshold})."
                evidence_quality = "Missing"
                for r in high_risks[:3]:
                    citations.append(f"[{r.id} | score:{r.score} | doc:{r.source_document_id or 'N/A'} | ev:{r.evidence_id or 'N/A'}]")
            else:
                status = "PASS"
                observed = f"All risks below threshold {threshold} or mitigated/accepted."
                gap = None
                evidence_quality = "Found"
                
        elif check_type == "DOCUMENT_EXISTS" or check_type == "DOCUMENT_CURRENT":
            keywords = rule_params.get("keywords", [])
            found = False
            for kw in keywords:
                docs = db.query(Document).filter(
                    Document.system_id == system_id,
                    Document.title.ilike(f"%{kw}%")
                ).first()
                if docs:
                    if check_type == "DOCUMENT_CURRENT" and docs.status == "Overdue":
                        continue
                    found = True
                    citations.append(f"[{docs.id} | {docs.title}]")
            if found:
                status = "PASS"
                observed = "Required documentation exists."
                gap = None
                evidence_quality = "Found"
            else:
                status = "FAIL"
                gap = "Required documentation is missing or not current."
                observed = "No matching documentation found."
                evidence_quality = "Missing"

        elif check_type == "REQUIREMENT_HAS_VERIFICATION":
            from backend.app.models.entities import Requirement
            unverified = db.query(Requirement).filter(
                Requirement.system_id == system_id,
                Requirement.status != "VERIFIED"
            ).all()
            if unverified:
                status = "FAIL"
                gap = f"Found {len(unverified)} unverified requirements."
                observed = f"Verification is missing for {len(unverified)} items."
                evidence_quality = "Missing"
            else:
                status = "PASS"
                observed = "All requirements are verified."
                gap = None
                evidence_quality = "Found"
        
        elif check_type == "TRAINING_COMPLETE":
            from backend.app.models.entities import TrainingRecord
            as_of_date = rule_params.get("as_of_date")
            query = db.query(TrainingRecord).filter(TrainingRecord.system_id == system_id)
            if as_of_date:
                query = query.filter(
                    TrainingRecord.effective_from <= as_of_date,
                    (TrainingRecord.effective_to == None) | (TrainingRecord.effective_to >= as_of_date)
                )
            training_records = query.all()
            
            if not training_records:
                status = "NOT_EVIDENCED"
                observed = "No structured training qualification facts evidenced for system roles."
                gap = "Missing verified training execution records."
                evidence_quality = "Missing"
            else:
                # Group by role_name and curriculum_id to handle duplicates and detect conflicts
                grouped = {}
                for r in training_records:
                    k = (r.role_name, r.curriculum_id)
                    grouped.setdefault(k, []).append(r)
                
                has_conflict = False
                active_records = []
                for k, recs in grouped.items():
                    req_counts = set(r.required_count for r in recs)
                    comp_counts = set(r.completed_count for r in recs)
                    # Conflicting counts across records for same role/curriculum
                    if len(req_counts) > 1 or len(comp_counts) > 1:
                        has_conflict = True
                        break
                    rec = sorted(recs, key=lambda x: x.recorded_at or x.created_at, reverse=True)[0]
                    # Invalid/contradictory counts (e.g. required <= 0 with completions, or negative values)
                    if (rec.required_count <= 0 and rec.completed_count > 0) or rec.required_count < 0 or rec.completed_count < 0:
                        has_conflict = True
                        break
                    if rec.status == "CONFLICT":
                        has_conflict = True
                        break
                    active_records.append(rec)
                
                if has_conflict:
                    status = "CONFLICT"
                    observed = "Contradictory or invalid training metrics detected across qualification records."
                    gap = "Conflicting training facts."
                    evidence_quality = "Conflicting"
                    for r in training_records[:3]:
                        eff = r.effective_from.strftime("%Y-%m-%d") if r.effective_from else "N/A"
                        citations.append(f"[{r.curriculum_id} | role:{r.role_name} | doc:{r.source_document_id or 'N/A'} | ev:{r.evidence_id or 'N/A'} | eff:{eff}]")
                else:
                    total_required = sum(r.required_count for r in active_records)
                    total_completed = sum(r.completed_count for r in active_records)
                    
                    for r in active_records:
                        eff = r.effective_from.strftime("%Y-%m-%d") if r.effective_from else "N/A"
                        citations.append(f"[{r.curriculum_id} | role:{r.role_name} | doc:{r.source_document_id or 'N/A'} | ev:{r.evidence_id or 'N/A'} | loc:{r.locator or 'N/A'} | eff:{eff}]")
                    
                    if total_required > 0:
                        if total_completed >= total_required and all(r.completed_count >= r.required_count for r in active_records):
                            status = "PASS"
                            observed = f"All required personnel qualified ({total_completed}/{total_required} across {len(active_records)} roles)."
                            gap = None
                            evidence_quality = "Found"
                        elif total_completed == 0:
                            status = "FAIL"
                            observed = f"Zero personnel qualified out of {total_required} required across {len(active_records)} roles."
                            gap = "No qualified personnel evidenced for system operation."
                            evidence_quality = "Found"
                        else:
                            status = "PARTIAL"
                            observed = f"Partial training completion evidenced ({total_completed}/{total_required} personnel qualified across {len(active_records)} roles)."
                            gap = f"{total_required - total_completed} personnel pending qualification before independent access."
                            evidence_quality = "Partial"
                    else:
                        status = "NOT_EVIDENCED"
                        observed = "Training records do not define required operational roles."
                        gap = "Undefined role requirements."
                        evidence_quality = "Missing"
            
        else:
            if candidate_evidence:
                status = "PARTIAL"
                observed = f"Candidate evidence found for {check_type} but specific rule not evaluated."
                gap = f"Cannot verify full compliance for {check_type}."
                evidence_quality = "Partial"
            else:
                status = "UNKNOWN"
                observed = "No evidence found to evaluate rule."

        if status == "UNKNOWN":
            status = "NOT_EVIDENCED"
            
        return (status, evidence_quality, confidence, citations, observed, gap, severity, recommendation)

    def cross_document_comparison(self, db: Session, system_id: str = "SYS-MES-001", risk_threshold: Optional[int] = None) -> CrossDocComparisonResponse:
        """
        Compares primary MES PAS-X evidence directly against the high-level Master IT
        System Lifecycle SOP (HACK-IT-SOP-001), citing both documents, maintaining
        first-class generic provenance for both sides, and flagging POTENTIAL LIFECYCLE DEVIATION items.
        """
        comparison_items = []
        
        # 1. Blocked Release Gates
        blocked_gates = db.query(ReleaseGate).filter(
            ReleaseGate.system_id == system_id,
            ReleaseGate.status.in_(["NOT MET", "BLOCKED"])
        ).all()
        for gate in blocked_gates:
            gate_cite = f"[{gate.id} | doc:{gate.evidence_doc or 'N/A'} | ev:{gate.evidence_id or 'N/A'} | sec:{gate.evidence_section or 'N/A'}]"
            item = CrossDocComparisonItem(
                topic=gate.gate_name,
                alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                deviation_type="UNMET_GATE",
                source_entity_id=gate.id,
                source_entity_type="RELEASE_GATE",
                source_document_id=gate.evidence_doc,
                source_evidence_id=gate.evidence_id,
                source_locator=gate.evidence_section,
                source_claim=f"Release Gate {gate.gate_code} ({gate.gate_name})",
                target_entity_id="HACK-IT-SOP-001-GATES",
                target_entity_type="SOP_REQUIREMENT",
                target_document_id="HACK-IT-SOP-001",
                target_evidence_id=None,
                target_locator="Section 4 Phase Gate Governance",
                target_observation=gate.blocking_reason or f"Gate {gate.gate_code} status is {gate.status}",
                master_sop_section="HACK-IT-SOP-001",
                sop_requirement=f"Gate {gate.gate_code} prerequisites must be fulfilled before stage transition.",
                mes_observed=gate.blocking_reason or f"Gate {gate.gate_code} is {gate.status}",
                mes_citations=[gate_cite],
                sop_citations=["[HACK-IT-SOP-001 | Section 4]"],
                impact=f"Failure to meet {gate.gate_code} gate compromises release readiness.",
                recommended_action=f"Resolve blocking prerequisites for {gate.gate_code}: {gate.blocking_reason or 'Verify gate criteria'}."
            )
            comparison_items.append(item)
            
        # 2. Residual Risks Evaluation - strictly using configured threshold
        effective_threshold = risk_threshold
        if effective_threshold is None:
            da03_spec = next((s for s in CORE_25_AUDIT_SPECS if s.get("q_id") == "DA-03-005"), None)
            if da03_spec and "rule_parameters" in da03_spec and "risk_threshold" in da03_spec["rule_parameters"]:
                effective_threshold = da03_spec["rule_parameters"]["risk_threshold"]
        
        if effective_threshold is not None:
            unmitigated_risks = db.query(Risk).filter(
                Risk.system_id == system_id,
                Risk.score >= effective_threshold
            ).all()
            if unmitigated_risks:
                sample_risk = unmitigated_risks[0]
                risk_cites = [f"[{r.id} | score:{r.score} | doc:{r.source_document_id or 'N/A'} | ev:{r.evidence_id or 'N/A'}]" for r in unmitigated_risks[:2]]
                item = CrossDocComparisonItem(
                    topic="Residual Risk",
                    alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                    deviation_type="UNMITIGATED_RISK",
                    source_entity_id=sample_risk.id,
                    source_entity_type="RISK",
                    source_document_id=sample_risk.source_document_id,
                    source_evidence_id=sample_risk.evidence_id,
                    source_locator=sample_risk.control_mapping,
                    source_claim=f"Identified {len(unmitigated_risks)} risks with score >= {effective_threshold}",
                    target_entity_id="HACK-IT-SOP-001-RISK",
                    target_entity_type="SOP_REQUIREMENT",
                    target_document_id="HACK-IT-SOP-001",
                    target_evidence_id=None,
                    target_locator="Section 5 Risk Management",
                    target_observation=f"Found {len(unmitigated_risks)} unmitigated high risks exceeding threshold {effective_threshold}.",
                    master_sop_section="HACK-IT-SOP-001",
                    sop_requirement=f"All risks with score >= {effective_threshold} require verified mitigations or explicit Quality Unit acceptance.",
                    mes_observed=f"Found {len(unmitigated_risks)} unmitigated high risks (e.g. {sample_risk.id}: {sample_risk.rationale}).",
                    mes_citations=risk_cites,
                    sop_citations=["[HACK-IT-SOP-001 | Section 5]"],
                    impact="Unrated residual risk creates unknown regulatory exposure under ICH Q9.",
                    recommended_action="Conduct formal residual risk acceptance evaluation and map verification controls."
                )
                comparison_items.append(item)
        else:
            item = CrossDocComparisonItem(
                topic="Residual Risk Configuration",
                alignment_status="EVIDENCE_GAP",
                deviation_type="UNCONFIGURED_THRESHOLD",
                source_entity_id=None,
                source_entity_type="RISK_CONFIG",
                source_document_id=None,
                source_evidence_id=None,
                source_locator=None,
                source_claim="No risk threshold configured in audit specifications",
                target_entity_id="HACK-IT-SOP-001-RISK",
                target_entity_type="SOP_REQUIREMENT",
                target_document_id="HACK-IT-SOP-001",
                target_evidence_id=None,
                target_locator="Section 5 Risk Management",
                target_observation="Missing explicit risk_threshold configuration",
                master_sop_section="HACK-IT-SOP-001",
                sop_requirement="Risk threshold must be defined before residual risk evaluation.",
                mes_observed="Risk threshold not configured. Residual risk cannot be evaluated without explicit threshold.",
                mes_citations=[],
                sop_citations=["[HACK-IT-SOP-001 | Section 5]"],
                impact="Cannot determine residual risk acceptability.",
                recommended_action="Configure explicit risk_threshold parameter."
            )
            comparison_items.append(item)

        # 3. Unverified Requirements
        from backend.app.models.entities import Requirement
        unverified_reqs = db.query(Requirement).filter(
            Requirement.system_id == system_id,
            Requirement.status != "VERIFIED"
        ).all()
        if unverified_reqs:
            sample_req = unverified_reqs[0]
            req_cites = [f"[{r.requirement_id} | doc:{r.source_document_id or 'N/A'} | ev:{r.evidence_id or 'N/A'}]" for r in unverified_reqs[:2]]
            item = CrossDocComparisonItem(
                topic="Requirement Verification",
                alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                deviation_type="UNVERIFIED_REQ",
                source_entity_id=sample_req.requirement_id,
                source_entity_type="REQUIREMENT",
                source_document_id=sample_req.source_document_id,
                source_evidence_id=sample_req.evidence_id,
                source_locator=f"p.{sample_req.source_page} {sample_req.source_section}" if sample_req.source_page else None,
                source_claim=sample_req.text,
                target_entity_id=sample_req.verification_reference or "VERIFICATION_NOT_EVIDENCED",
                target_entity_type="VERIFICATION_TEST",
                target_document_id="HACK-IT-SOP-001",
                target_evidence_id=None,
                target_locator="Section 6 Qualification & Verification",
                target_observation=f"Requirement status is {sample_req.status} (verification execution records unevidenced)",
                master_sop_section="HACK-IT-SOP-001",
                sop_requirement="All requirements must have verified test execution records prior to operational release.",
                mes_observed=f"Found {len(unverified_reqs)} unverified requirements (e.g. {sample_req.requirement_id} is '{sample_req.status}').",
                mes_citations=req_cites,
                sop_citations=["[HACK-IT-SOP-001 | Section 6]"],
                impact="Unverified requirements compromise intended use confirmation.",
                recommended_action="Complete intended-use qualification test scripts."
            )
            comparison_items.append(item)
            
        aligned_count = 0
        deviations_count = len([it for it in comparison_items if it.alignment_status != "ALIGNED"])
        
        # 4. Aligned Met Gates
        met_gates = db.query(ReleaseGate).filter(
            ReleaseGate.system_id == system_id,
            ReleaseGate.status == "MET"
        ).all()
        for gate in met_gates:
            gate_cite = f"[{gate.id} | doc:{gate.evidence_doc or 'N/A'} | ev:{gate.evidence_id or 'N/A'}]"
            item = CrossDocComparisonItem(
                topic=gate.gate_name,
                alignment_status="ALIGNED",
                deviation_type=None,
                source_entity_id=gate.id,
                source_entity_type="RELEASE_GATE",
                source_document_id=gate.evidence_doc,
                source_evidence_id=gate.evidence_id,
                source_locator=gate.evidence_section,
                source_claim=f"Release Gate {gate.gate_code} ({gate.gate_name})",
                target_entity_id="HACK-IT-SOP-001-GATES",
                target_entity_type="SOP_REQUIREMENT",
                target_document_id="HACK-IT-SOP-001",
                target_evidence_id=None,
                target_locator="Section 4 Phase Gate Governance",
                target_observation=f"Gate {gate.gate_code} is MET with verified objective evidence.",
                master_sop_section="HACK-IT-SOP-001",
                sop_requirement=f"Gate {gate.gate_code} requirements must be fulfilled.",
                mes_observed=f"Gate {gate.gate_code} is MET with evidence in {gate.evidence_doc or 'qualification package'}.",
                mes_citations=[gate_cite],
                sop_citations=["[HACK-IT-SOP-001 | Section 4]"],
                impact="None",
                recommended_action="Maintain qualification baseline."
            )
            comparison_items.append(item)
            aligned_count += 1
            
        return CrossDocComparisonResponse(
            system_id=system_id,
            system_name="SYS-MES-001 (Dynamic)",
            comparison_date=datetime.now(timezone.utc),
            items=comparison_items,
            total_compared=len(comparison_items),
            deviations_count=deviations_count,
            gaps_count=len([it for it in comparison_items if it.alignment_status == "EVIDENCE_GAP"]),
            aligned_count=aligned_count,
        )

    def get_latest_assessment(
        self,
        db: Session,
        system_id: str = "SYS-MES-001",
        checklist_id: Optional[str] = None
    ) -> Optional[AuditAssessmentResponse]:
        """
        Retrieve the most recent stored audit assessment from the database.
        Returns None if no assessments have been run yet.
        """
        query = db.query(AuditAssessment).filter(
            AuditAssessment.system_id == system_id
        )
        if checklist_id:
            query = query.filter(AuditAssessment.checklist_id == checklist_id)

        assessment = query.order_by(AuditAssessment.assessed_at.desc()).first()
        if not assessment:
            return None

        items = []
        for item_data in (assessment.items_json or []):
            try:
                items.append(AuditAssessmentItem(**item_data))
            except Exception:
                pass

        return AuditAssessmentResponse(
            id=assessment.id,
            system_id=assessment.system_id,
            checklist_id=assessment.checklist_id,
            assessed_at=assessment.assessed_at,
            readiness_score=assessment.readiness_score,
            total_questions=assessment.total_questions,
            passed_count=assessment.passed_count,
            partial_count=assessment.partial_count,
            failed_count=assessment.failed_count,
            not_evidenced_count=assessment.not_evidenced_count,
            na_count=assessment.na_count,
            critical_findings_count=assessment.critical_findings_count,
            high_findings_count=assessment.high_findings_count,
            medium_findings_count=assessment.medium_findings_count,
            low_findings_count=assessment.low_findings_count,
            items=items,
            findings=assessment.findings_json or [],
            lifecycle_gaps=assessment.lifecycle_gaps_json or [],
            status=assessment.status
        )


audit_engine = AuditEngine()
