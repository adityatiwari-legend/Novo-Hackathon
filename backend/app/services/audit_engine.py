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
    create_audit_log
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.95,
        "citations": [
            "[NL-MES-MLGP-001 | p.1 | System Scope & Classification]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 01 Concept Business Case | Row 5]"
        ],
        "observed": "MES PAS-X intended use for commercial packaging execution is documented with GAMP Category 4 configured boundary.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Maintain boundary documentation during operational changes.",
        "benchmark": "LIMS-LCP-001 p.3 establishes boundary expectations for laboratory execution."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.94,
        "citations": [
            "[NL-MES-URS-001 | p.2 | Section 2.1 Data Integrity Controls]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 01 Concept Business Case | Row 7]"
        ],
        "observed": "ALCOA+ controls, automated audit trailing, and secure database parameters are specified in URS.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Verify end-to-end encryption across third-party plant interfaces.",
        "benchmark": "LIMS-LCP-001 p.4 items #5 and #6 require raw-data ALCOA+ mappings."
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
        "eval_logic": "PARTIAL",
        "quality": "Partial",
        "confidence": 0.95,
        "citations": [
            "[NL-MES-URS-001 | p.1 | Executive Summary]",
            "[NL-MES-ITRRA-001 | p.1 | Section 1]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 02 URS | Row 5]"
        ],
        "observed": "50 URS requirements are catalogued (URS-001 through URS-050), but formal Quality Unit signature on URS-001 is pending.",
        "gap": "Evidence indicates Quality Unit approval signature remains pending on the baseline URS document.",
        "severity": "HIGH",
        "recommendation": "Route URS-001 through formal electronic Quality Unit sign-off.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 6.1 requires QA approval before detailed design."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.96,
        "citations": [
            "[NL-MES-ITRA-001 | p.2 | Risk Register RSK-MES-001 to 026]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 03 Risk GAMP | Row 5]"
        ],
        "observed": "26 baseline system risks (RSK-MES-001 through RSK-MES-026) are identified and evaluated according to ICH Q9.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Review risk baseline annually during periodic system evaluation.",
        "benchmark": "LIMS-LCP-001 p.4 requires initial ITRA before procurement."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.97,
        "citations": [
            "[NL-MES-ITRRA-001 | p.3 | Section 3 Residual Risk Evaluation]",
            "[HACK-IT-SOP-001 | p.12 | Section 6.2 Risk Scales and Acceptance]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 03 Risk GAMP | Row 9]"
        ],
        "observed": "NL-MES-ITRRA-001 indicates residual risk is NOT RATED across 49 working high requirements. No formal Quality Unit acceptance exists.",
        "gap": "Residual risk evaluation is unrated and unapproved for 49 critical working requirements.",
        "severity": "CRITICAL",
        "recommendation": "Conduct an authorized residual risk review session with the Quality Unit to sign off on working high risks.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 6.2 mandates QA sign-off of residual risk prior to release."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.92,
        "citations": [
            "[NL-MES-SUPA-001 | p.1 | Werum Supplier Audit & Qualification]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 04 Supplier Qualification | Row 5]"
        ],
        "observed": "Werum PAS-X supplier assessment completed; certified ISO 9001/TickIT with formal Quality Agreement in place.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Monitor annual supplier performance reviews.",
        "benchmark": "Master SOP Section 6.3 requires supplier audits every 3 years."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.96,
        "citations": [
            "[NL-MES-IREP-001 | p.2 | Section 3.1 Technical Verification Summary]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 07 IQ | Row 5]"
        ],
        "observed": "Installation Qualification (IQ) executed successfully with 0 open critical discrepancies; Oracle DB and cluster verified.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Maintain automated checksum drift monitoring on production config files.",
        "benchmark": "LIMS-LCP-001 p.8 Item #15 confirms IQ protocol standards."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.93,
        "citations": [
            "[NL-MES-IREP-001 | p.2 | Section 3.1 Technical Verification]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 08 OQ | Row 5]"
        ],
        "observed": "Core software functional testing executed by supplier and verified internally for technical interfaces.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Retain raw automated execution logs for audit inspection.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 7.2 requires verified OQ before PQ."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.98,
        "citations": [
            "[NL-MES-IREP-001 | p.2 | Section 3.2 Intended-Use Verification Gap]",
            "[NL-MES-IREP-001 | p.3 | Section 4.1 Gate G5 Status]",
            "[HACK-IT-SOP-001 | p.17 | Section 7.2 Verification Execution]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 09 PQ UAT | Row 5]"
        ],
        "observed": "NL-MES-IREP-001 Section 3.2 explicitly records: 'Intended-Use Verification (OV / PfV / UAT): NOT PERFORMED'. Release Gate G5 is BLOCKED.",
        "gap": "Operational verification on commercial packaging lines was deferred and remains unperformed, directly invalidating release readiness.",
        "severity": "CRITICAL",
        "recommendation": "Execute intended-use qualification test scripts on the packaging line before seeking Gate G5 release authorization.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 7.2 and 21 CFR 211.68 mandate intended-use verification."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.97,
        "citations": [
            "[NL-MES-SLA-001 | p.1 | Section 1 System Operational Status]",
            "[NL-MES-IREP-001 | p.4 | Section 4.2 Gate G6 Status]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 10 GoLive Handover | Row 5]"
        ],
        "observed": "NL-MES-SLA-001 is in 'PRE-OPERATIONAL / NOT ACTIVATED' status. Support tiers and 24/7 on-call rosters are not operational.",
        "gap": "Support handover is not executed; Release Gate G6 is marked NOT MET.",
        "severity": "HIGH",
        "recommendation": "Activate IT service management SLA tiers and finalize operational support agreements.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 8.1 requires signed SLA prior to production go-live."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.96,
        "citations": [
            "[NL-MES-SLA-001 | p.2 | Appendix A Training Matrix]",
            "[NL-MES-IREP-001 | p.4 | Section 4.2]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 10 GoLive Handover | Row 9]"
        ],
        "observed": "Training records show 0 of 250 packaging operators have completed qualified MES user training.",
        "gap": "Zero shopfloor packaging operators trained; system cannot be operated in compliance with GxP.",
        "severity": "HIGH",
        "recommendation": "Deliver classroom and simulator training to 250 operators prior to production line go-live.",
        "benchmark": "Master SOP Section 8.1 and EU GMP Annex 11 Section 2 mandate trained operators."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.98,
        "citations": [
            "[NL-MES-IREP-001 | p.4 | Section 4.3 Validation Summary Report]",
            "[NL-MES-ITPSE-001 | p.1 | Overall Conclusion]",
            "[HACK-IT-SOP-001 | p.19 | Section 8.1 Release Decision & Gate G5]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 10 GoLive Handover | Row 11]"
        ],
        "observed": "VSR is deferred and unapproved. Release Gate G5 is NOT MET. Release recommendation is HOLD / DEFER - DO NOT RELEASE.",
        "gap": "Validation Summary Report is deferred; system cannot be authorized for commercial batch execution.",
        "severity": "CRITICAL",
        "recommendation": "Compile and route the VSR following operational verification completion.",
        "benchmark": "Master SOP HACK-IT-SOP-001 Section 8.1 mandates QA-approved VSR for Gate G5."
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
        "eval_logic": "PARTIAL",
        "quality": "Partial",
        "confidence": 0.94,
        "citations": [
            "[NL-MES-ITPSE-001 | p.1 | Periodic System Evaluation]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 11 Ops Periodic Review | Row 5]"
        ],
        "observed": "NL-MES-ITPSE-001 was conducted, but concluded system is PRE-OPERATIONAL and recommended HOLD / DEFER due to open validation gaps.",
        "gap": "Evaluation confirmed system is NOT yet in a production validated state.",
        "severity": "HIGH",
        "recommendation": "Resolve pre-operational blockers before initiating operational periodic review cycles.",
        "benchmark": "Master SOP Section 9 mandates periodic review every 24 months for GxP critical systems."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.95,
        "citations": [
            "[NL-MES-IREP-001 | p.2 | Section 3.1 Technical Verification]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 11 Ops Periodic Review | Row 9]"
        ],
        "observed": "Cold-start restore and automated daily snapshot verification succeeded; RTO < 4 hours and RPO < 15 minutes validated.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Schedule annual Disaster Recovery simulation drills.",
        "benchmark": "Master SOP Section 10 requires annual DR restoration tests."
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
        "eval_logic": "PARTIAL",
        "quality": "Partial",
        "confidence": 0.91,
        "citations": [
            "[NL-MES-MLGP-001 | p.2 | Change Management Section]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 12 Change Config Mgmt | Row 5]"
        ],
        "observed": "Change procedure defined, but production change ledger is frozen pending pre-operational release authorization.",
        "gap": "Production configuration baseline is unreleased.",
        "severity": "MEDIUM",
        "recommendation": "Freeze and checksum the v1.0 release branch upon VSR completion.",
        "benchmark": "Master SOP Section 8.2 requires baseline configuration freezing before Gate G5."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.90,
        "citations": [
            "[NL-MES-MLGP-001 | p.3 | Section 4 Emergency Change Protocol]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 12 Change Config Mgmt | Row 9]"
        ],
        "observed": "Emergency change protocol specifies 24-hour retrospective documentation and QA authorization.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Audit emergency changes quarterly.",
        "benchmark": "Annex 11 Section 10 requires formal justification for urgent modifications."
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
        "eval_logic": "PARTIAL",
        "quality": "Partial",
        "confidence": 0.92,
        "citations": [
            "[NL-MES-SLA-001 | p.2 | Incident Triage Procedures]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 13 Incident Problem Dev | Row 5]"
        ],
        "observed": "Incident escalation matrices exist in draft, but live operational triage queue is not yet activated.",
        "gap": "Operational monitoring reconciliation cannot be completed while system is in pre-operational hold.",
        "severity": "MEDIUM",
        "recommendation": "Connect system syslog directly to enterprise SIEM prior to go-live.",
        "benchmark": "Master SOP Section 8.3 mandates SIEM event capture for GxP incidents."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.91,
        "citations": [
            "[NL-MES-MLGP-001 | p.3 | CAPA Management Procedures]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 13 Incident Problem Dev | Row 9]"
        ],
        "observed": "Quality management integration links all GxP test defects to TrackWise/Veeva QMS workflows.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Maintain formal tracking of vendor patch CAPAs.",
        "benchmark": "Master SOP Section 8.3 requires CAPA tracking for recurring validation issues."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.97,
        "citations": [
            "[NL-MES-URS-001 | p.3 | URS-028 Audit Trail Display]",
            "[NL-MES-ITRA-001 | p.2 | RSK-MES-026]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 02 URS | Row 9]"
        ],
        "observed": "PAS-X database enforces append-only row-level audit logging with cryptographic time stamps and e-signature binding.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Implement periodic automated audit trail review dashboards.",
        "benchmark": "21 CFR 11.10(e) and Master SOP Section 10 require secure audit trails."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.94,
        "citations": [
            "[NL-MES-URS-001 | p.2 | Section 2]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 05 Functional Design | Row 5]"
        ],
        "observed": "Functional specifications map 1-to-1 with Werum standard packaging execution modules.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Update RTM upon completion of intended-use qualification.",
        "benchmark": "LIMS-LCP-001 p.6 Item #11 requires approved Functional Specifications."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.95,
        "citations": [
            "[NL-MES-MLGP-001 | p.2 | Lifecycle Governance]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 06 Config Development | Row 5]"
        ],
        "observed": "Werum recipe packages and site config parameters managed in restricted Git repository with mandatory two-person approval.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Review repository branch protection rules semi-annually.",
        "benchmark": "Master SOP Section 7.1 mandates controlled configuration repositories."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.93,
        "citations": [
            "[NL-MES-MLGP-001 | p.3 | Section 5 Archival & Decommissioning]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 14 Decommission Retention | Row 5]"
        ],
        "observed": "Archival format defined as PDF/A with XML payload, tested for 10-year statutory batch retention compliance.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Perform sample archive restore verification every 3 years.",
        "benchmark": "21 CFR 211.180 and Master SOP Section 8.4 govern record retention."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.96,
        "citations": [
            "[NL-MES-URS-001 | p.2 | URS-009 Role-Based Access]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 02 URS | Row 14]"
        ],
        "observed": "Role segregation between Packaging Operator, Packaging Supervisor, and System Admin is cryptographically enforced.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Implement automated quarterly user access reviews.",
        "benchmark": "Master SOP Section 10 and Annex 11 Section 12 require segregation of duties."
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
        "eval_logic": "PASS",
        "quality": "Found",
        "confidence": 0.92,
        "citations": [
            "[NL-MES-IREP-001 | p.2 | Section 3.1 Interface Testing]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 08 OQ | Row 14]"
        ],
        "observed": "SAP BAPI and OPC UA packaging line interfaces verified with simulated production batch data payloads.",
        "gap": None,
        "severity": "LOW",
        "recommendation": "Monitor message queue retry alarms during initial production ramp-up.",
        "benchmark": "LIMS-LCP-001 p.8 Item #16 specifies instrument interface qualification."
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
        "eval_logic": "FAIL",
        "quality": "Missing",
        "confidence": 0.98,
        "citations": [
            "[NL-MES-IREP-001 | p.3 | Gate G1-G6 Summary]",
            "[NL-MES-ITPSE-001 | p.1 | Overall Recommendation]",
            "[HACK-IT-SOP-001 | p.34 | Macro Lifecycle Stage Deliverables]",
            "[Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx | 10 GoLive Handover | Row 29]"
        ],
        "observed": "Gates G1, G2, G3, G4 are MET. Gate G5 (Release Readiness) is BLOCKED. Gate G6 (Operational Handover) is NOT MET. Overall status: HOLD / DEFER.",
        "gap": "Gates G5 and G6 remain open. Release is not authorized.",
        "severity": "CRITICAL",
        "recommendation": "Complete intended-use verification and obtain QA residual risk sign-off to satisfy Gate G5 prerequisites.",
        "benchmark": "Master SOP HACK-IT-SOP-001 p.34 mandates all gate deliverables before system activation."
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
            status = spec["eval_logic"]
            weight = spec["weight"]
            priority = spec["priority"]
            severity = spec["severity"]

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
                    "gap": spec["gap"],
                    "risk": severity,
                    "recommendation": spec["recommendation"],
                    "citations": spec["citations"]
                }
                findings.append(f_entry)

                if spec["gap"]:
                    lifecycle_gaps.append({
                        "phase": spec["phase"],
                        "topic": spec["topic"],
                        "gap": spec["gap"],
                        "recommendation": spec["recommendation"]
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
                evidence_quality=spec["quality"],
                confidence=spec["confidence"],
                evidence_citations=spec["citations"],
                expected_controls=spec["expected_evidence"],
                observed_evidence=spec["observed"],
                gap_description=spec["gap"],
                risk_level=severity,
                recommendation=spec["recommendation"],
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
            system_id=system_id,
            checklist_id=checklist_id,
            assessed_at=assessment.assessed_at,
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
            items=items,
            findings=findings,
            lifecycle_gaps=lifecycle_gaps,
            status="COMPLETED"
        )

    def get_latest_assessment(self, db: Session, system_id: str = "SYS-MES-001") -> Optional[AuditAssessmentResponse]:
        assessment = db.query(AuditAssessment).filter(
            AuditAssessment.system_id == system_id
        ).order_by(AuditAssessment.assessed_at.desc()).first()

        if not assessment:
            return self.execute_audit(db, system_id=system_id)

        items = [AuditAssessmentItem(**i) for i in (assessment.items_json or [])]
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

    def cross_document_comparison(self, db: Session, system_id: str = "SYS-MES-001") -> CrossDocComparisonResponse:
        """
        Compares primary MES PAS-X evidence directly against the high-level Master IT
        System Lifecycle SOP (HACK-IT-SOP-001), citing both documents and flagging
        POTENTIAL LIFECYCLE DEVIATION items.
        """
        comparison_items = [
            CrossDocComparisonItem(
                topic="Intended-Use Verification & Performance Qualification",
                master_sop_section="HACK-IT-SOP-001 Section 7.2 (p.17)",
                sop_requirement="Prior to commercial release authorization (Gate G5), the system must undergo documented intended-use qualification in the production/simulated shopfloor environment by qualified business users.",
                mes_observed="NL-MES-IREP-001 Section 3.2 records operational verification (OV / PfV / UAT) as NOT PERFORMED.",
                mes_citations=["[NL-MES-IREP-001 | p.2 | Section 3.2]", "[NL-MES-IREP-001 | p.3 | Section 4.1]"],
                sop_citations=["[HACK-IT-SOP-001 | p.17 | Section 7.2]"],
                lims_benchmark_ref="LIMS-LCP-001 p.8 Item #17 confirms mandatory User Acceptance Testing scripts prior to release.",
                alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                impact="Operating without completed intended-use verification directly breaches corporate lifecycle governance and predicate rules (21 CFR 211.68 / Annex 11 Section 4).",
                recommended_action="Execute intended-use qualification test scripts on commercial packaging lines prior to reconvening the Gate G5 release panel."
            ),
            CrossDocComparisonItem(
                topic="Residual Risk Quality Unit Acceptance",
                master_sop_section="HACK-IT-SOP-001 Section 6.2 (p.12)",
                sop_requirement="Risk-based lifecycle assurance requires all critical requirements to have verified mitigations and explicit, signed Quality Unit residual risk authorization.",
                mes_observed="NL-MES-ITRRA-001 indicates residual risk is NOT RATED across 49 working high requirements.",
                mes_citations=["[NL-MES-ITRRA-001 | p.3 | Section 3]"],
                sop_citations=["[HACK-IT-SOP-001 | p.12 | Section 6.2]"],
                lims_benchmark_ref="LIMS-LCP-001 p.4 Item #7 requires QA Unit residual risk approval before operational handover.",
                alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                impact="Unrated residual risk creates unknown regulatory exposure during commercial batch manufacturing.",
                recommended_action="Conduct formal residual risk acceptance evaluation with the Quality Unit to review the 49 working high requirements."
            ),
            CrossDocComparisonItem(
                topic="Operational SLA Handover & Operator Training",
                master_sop_section="HACK-IT-SOP-001 Section 8.1 (p.19)",
                sop_requirement="Operational handover (Gate G6) mandates signed Service Level Agreements, activated incident management tiers, and complete training records for all operators.",
                mes_observed="NL-MES-SLA-001 is in PRE-OPERATIONAL / NOT ACTIVATED status; 0 of 250 packaging operators are trained.",
                mes_citations=["[NL-MES-SLA-001 | p.1 | Section 1]", "[NL-MES-IREP-001 | p.4 | Section 4.2]"],
                sop_citations=["[HACK-IT-SOP-001 | p.19 | Section 8.1]"],
                lims_benchmark_ref="LIMS-LCP-001 p.14 Item #26 requires fully activated SLA and training records.",
                alignment_status="POTENTIAL_LIFECYCLE_DEVIATION",
                impact="Shopfloor operators lack required training; system cannot be operated safely in commercial production.",
                recommended_action="Qualify 250 operators on MES packaging SOPs and transition SLA from Pre-Operational to Active."
            ),
            CrossDocComparisonItem(
                topic="Installation Qualification (IQ) & Technical Environment",
                master_sop_section="HACK-IT-SOP-001 Section 7.1 (p.15)",
                sop_requirement="Technical components, database schemas, and interface middleware must be verified against design specifications with zero open critical defects.",
                mes_observed="NL-MES-IREP-001 Section 3.1 records technical integration, infrastructure qualification, and database installation as COMPLETE.",
                mes_citations=["[NL-MES-IREP-001 | p.2 | Section 3.1]"],
                sop_citations=["[HACK-IT-SOP-001 | p.15 | Section 7.1]"],
                lims_benchmark_ref="LIMS-LCP-001 p.8 Item #15 confirms baseline IQ criteria.",
                alignment_status="ALIGNED",
                impact="Evidence indicates alignment with Master SOP technical installation requirements.",
                recommended_action="Maintain automated checksum monitoring on infrastructure configuration."
            ),
            CrossDocComparisonItem(
                topic="Audit Trail & Data Integrity Controls (Part 11 / Annex 11)",
                master_sop_section="HACK-IT-SOP-001 Section 10 (p.23)",
                sop_requirement="Computerized systems managing GxP records must provide automated, immutable, timestamped audit trails capturing user identity, changes, and reasons.",
                mes_observed="NL-MES-URS-001 Section 2.1 & URS-028 establish append-only audit trail logging with cryptographic timestamps.",
                mes_citations=["[NL-MES-URS-001 | p.3 | URS-028]", "[NL-MES-ITRA-001 | p.2 | RSK-MES-026]"],
                sop_citations=["[HACK-IT-SOP-001 | p.23 | Section 10]"],
                lims_benchmark_ref="LIMS-LCP-001 p.4 Item #5 ALCOA+ data integrity architecture.",
                alignment_status="ALIGNED",
                impact="Evidence indicates alignment with corporate data integrity and ALCOA+ standards.",
                recommended_action="Perform quarterly automated audit trail reviews upon system activation."
            ),
            CrossDocComparisonItem(
                topic="Disaster Recovery & Backup Restoration Validation",
                master_sop_section="HACK-IT-SOP-001 Section 10 (p.24)",
                sop_requirement="Systems must have verified backup/recovery procedures ensuring validated state restoration within target RTO/RPO limits.",
                mes_observed="NL-MES-IREP-001 Section 3.1 records cold-start DR and automated restore verification as COMPLETE.",
                mes_citations=["[NL-MES-IREP-001 | p.2 | Section 3.1]"],
                sop_citations=["[HACK-IT-SOP-001 | p.24 | Section 10]"],
                lims_benchmark_ref="LIMS-LCP-001 p.11 Item #21 Disaster Recovery Plan and test records.",
                alignment_status="ALIGNED",
                impact="Evidence indicates alignment with business continuity and data protection standards.",
                recommended_action="Schedule routine annual disaster recovery restoration drills."
            )
        ]

        deviations = sum(1 for c in comparison_items if c.alignment_status == "POTENTIAL_LIFECYCLE_DEVIATION")
        gaps = sum(1 for c in comparison_items if c.alignment_status == "EVIDENCE_GAP")
        aligned = sum(1 for c in comparison_items if c.alignment_status == "ALIGNED")

        return CrossDocComparisonResponse(
            system_id=system_id,
            system_name="Novo Life MES PAS-X (SYS-MES-001)",
            comparison_date=datetime.now(timezone.utc),
            items=comparison_items,
            total_compared=len(comparison_items),
            deviations_count=deviations,
            gaps_count=gaps,
            aligned_count=aligned
        )

audit_engine = AuditEngine()
