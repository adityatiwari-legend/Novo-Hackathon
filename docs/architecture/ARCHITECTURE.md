# Architecture: Agentic AI Co-Pilot for Always-On, Audit-Ready GxP IT System Management

## Executive Summary
This platform transforms fragmented, reactive GxP IT compliance documentation into a continuous, audit-ready AI-driven management ecosystem aligned with **21 CFR Part 11, EU Annex 11, GAMP 5 Category 4, and ALCOA+ principles**.

---

## 1. System Architecture Diagram

```mermaid
graph TD
    User([User / QA Auditor]) -->|Browser / HTTPS| NextFrontend[Next.js 14 Enterprise UI]
    NextFrontend -->|REST API / JSON| FastAPIServer[FastAPI Backend Server]

    subgraph "FastAPI Backend Layer"
        FastAPIServer --> AuthSecurity[RBAC & Security Guardrails]
        FastAPIServer --> IngestionSvc[Document Ingestion & Checksum Engine]
        FastAPIServer --> RAGSvc[Hybrid RAG Engine (BM25 + Dense Vectors)]
        FastAPIServer --> ComplianceEngine[Deterministic Compliance Scoring Engine]
        FastAPIServer --> AuditTrailSvc[Tamper-Evident SHA-256 Chained Audit Trail]
        
        subgraph "LangGraph Agent Mesh"
            Supervisor[Supervisor / Orchestrator Agent]
            SysKnowledge[System Knowledge Agent]
            CompAgent[Compliance Agent]
            RiskAgent[GxP Risk Agent]
            EvAgent[Audit Evidence Agent]
            RecAgent[Recommendation Agent]

            Supervisor --> SysKnowledge
            SysKnowledge --> CompAgent
            CompAgent --> RiskAgent
            RiskAgent --> RecAgent
            RecAgent --> EvAgent
        end

        subgraph "Mock Enterprise Connectors"
            ServiceNowConn[ServiceNow Connector: SNOW-TASK-1001]
            VaultConn[Veeva Vault Quality Connector]
            IAMConn[IAM Access & Entitlements]
            MonitorConn[Continuous Monitoring Simulation]
        end
    end

    subgraph "Persistence Layer"
        FastAPIServer --> SQLitePostgres[(PostgreSQL / SQLite Database)]
        FastAPIServer --> VectorStore[(Hybrid Vector Store: JSON & NumPy Embeddings)]
        FastAPIServer --> FileStorage[(Encrypted File & Evidence Storage)]
    end

    FastAPIServer --> Supervisor
    RecAgent -->|Requires Human Authorization| ApprovalGate[Human-in-the-Loop Workflow Gate]
    ApprovalGate -->|On Human Approval| ServiceNowConn
    ApprovalGate -->|Cryptographic Event| AuditTrailSvc
```

---

## 2. Core Architectural Principles

### 2.1 Deterministic Logic vs. LLM Reasoning Separation
To ensure regulatory credibility in a GxP environment:
- **Deterministic (Non-LLM)**:
  - Compliance readiness scoring: $Score = 100 - \sum \text{penalties}$ (e.g. Critical: 25, High: 12, Medium: 3, Low: 2).
  - Severity calculation & checklist evaluation.
  - Role-Based Access Control (RBAC) permissions.
  - Human approval gating.
  - Append-only audit trail and SHA-256 hash chaining.
- **LLM Reasoning**:
  - Grounded question answering strictly backed by source chunks.
  - Synthesizing natural-language remediation rationales.
  - Drafting missing GxP sections with prominent "NOT APPROVED" watermarks.

### 2.2 Tamper-Evident Audit Trail (SHA-256 Chaining)
Every GxP-relevant action produces an immutable audit record:
$$\text{event\_hash} = \text{SHA256}(\text{previous\_hash} + \text{canonical\_event\_json})$$
- The genesis block begins with 64 zeroes.
- The chain cannot be retroactively modified without invalidating all downstream block hashes.
- Verified on-demand via `/api/v1/audit-log/verify`.

### 2.3 Non-Bypassable Human-in-the-Loop (HITL)
AI recommendations are strictly advisory (`status: PROPOSED`).
- Any state-altering action (e.g., ticket creation in ServiceNow, CAPA initiation, SOP lifecycle change) must be authorized by an authenticated human actor (`QA_COMPLIANCE` or `SYSTEM_OWNER`).
- Rejections require mandatory written justification logged in the audit ledger.

---

## 3. Data Model Hierarchy
1. **Systems**: Root GxP computerized systems (e.g. `SYS-LIMS-001`).
2. **Documents**: Uploaded files with SHA-256 checksums, version metadata, and approval statuses.
3. **DocumentChunks**: Content split by heading sections and pages for citation mapping.
4. **ComplianceChecks**: Rule-by-rule evaluation against `compliance_checklist.json`.
5. **ComplianceFindings**: Concrete deficiencies linked to source citations.
6. **Risks**: ICH Q9 risk matrices (likelihood, severity, impact type).
7. **Recommendations**: Actionable corrective remediation.
8. **EvidencePacks**: Compiled PDF and DOCX dossiers.
9. **Workflows**: Human-gated remediation lifecycle.
10. **AuditLogs**: Cryptographically chained immutable ledger.
