import re
import os

engine_file = r"c:\Users\Yash Sharma\Desktop\novo nordisk\Novo-Hackathon\backend\app\services\audit_engine.py"

with open(engine_file, "r") as f:
    content = f.read()

# Replace the CORE_25_AUDIT_SPECS assignment
new_specs_str = """CORE_25_AUDIT_SPECS = [
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
        "target_document_type": "System Scope",
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["ALCOA", "Data Lifecycle", "URS"],
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
        "check_type": "DOCUMENT_APPROVED",
        "target_document_type": "URS",
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
        "check_type": "DOCUMENT_APPROVED",
        "target_document_type": "Risk Assessment",
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
        "check_type": "RESIDUAL_RISK_ACCEPTED",
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Supplier", "Werum", "SLA"],
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
        "check_type": "DOCUMENT_APPROVED",
        "target_document_type": "Implementation Report",
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Implementation Report", "OQ", "Functional"],
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
        "check_type": "RELEASE_GATE_MET",
        "gate_code": "G5",
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
        "check_type": "RELEASE_GATE_MET",
        "gate_code": "G6",
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
        "check_type": "TRAINING_COMPLETE",
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
        "check_type": "RELEASE_GATE_MET",
        "gate_code": "G5",
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Periodic System Evaluation", "ITPSE"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Disaster", "Backup", "Restore", "Implementation Report"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Lifecycle Governance", "Change Management"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Emergency Change", "Lifecycle Governance"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Incident Triage", "SLA"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["CAPA Management"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Audit Trail", "Signature", "URS"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Functional", "URS"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Lifecycle Governance"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Archival", "Retention", "Lifecycle"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Role-Based Access", "URS-009"],
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
        "check_type": "DOCUMENT_EXISTS",
        "keywords": ["Interface Testing", "Implementation Report"],
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
        "check_type": "RELEASE_GATE_MET",
        "gate_code": "G5",
        "benchmark": "Master SOP HACK-IT-SOP-001 p.34 mandates all gate deliverables before system activation."
    }
]"""

# Substitute the existing list using regex
pattern = r"CORE_25_AUDIT_SPECS\s*=\s*\[.*?\]\n\n\nclass AuditEngine:"
replacement = new_specs_str + "\n\n\nclass AuditEngine:"
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(engine_file, "w") as f:
    f.write(content)
