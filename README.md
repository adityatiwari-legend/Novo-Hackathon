# Agentic AI Co-Pilot for Always-On, Audit-Ready GxP IT System Management

> **Novo Nordisk Hackathon 2026 Project**  
> *Transforming fragmented GxP IT compliance documentation into a continuous, audit-ready AI workflow aligned with ALCOA+, 21 CFR Part 11, EU Annex 11, and GAMP 5.*

---

## 1. Executive Summary & Vision

Today, pharmaceutical IT and Quality Assurance teams manually chase compliance across fragmented systems—ServiceNow, Veeva Vault Quality, SharePoint, IAM, and static validation binders. Audit preparation is typically an emergency point-in-time panic.

This **Agentic AI Co-Pilot** converts reactive audit preparation into an **always-on continuous compliance mesh**:
- **Continuous Ingestion**: Upload GxP documents (PDF, DOCX, XLSX, TXT) with automated SHA-256 checksums and section parsing.
- **Hybrid RAG Knowledge Mesh**: Answers compliance queries grounded strictly in source documents with page- and section-level citations and bounded confidence scoring.
- **Deterministic Compliance Scoring**: Uses an external `compliance_checklist.json` to compute deterministic readiness indices ($100 - \sum \text{penalties}$)—never asking an LLM to hallucinate regulatory scores.
- **Non-Negotiable Human-in-the-Loop**: AI synthesizes corrective actions and remediation drafts, but **authenticated humans must authorize all state-altering GxP workflows**.
- **Enterprise Integrations**: Execution of approved workflows automatically provisions realistic ServiceNow remediation tasks (`SNOW-TASK-1001`).
- **Cryptographic Audit Ledger**: Append-only audit trail with SHA-256 hash chaining ($\text{event\_hash} = \text{SHA256}(\text{previous\_hash} + \text{canonical\_event\_json})$).
- **Automated Evidence Dossiers**: Compiles complete audit evidence packs exportable in **ReportLab PDF** and **python-docx Word**.
- **Always-On Simulation**: Built-in "Continuous Compliance Monitor" simulates background document review expiration, dynamically updating system readiness from 82% to 76%.

---

## 2. Regulatory Compliance Notice

> **Prototype Regulatory Disclaimer**:
> This prototype is designed to align with GxP and ALCOA+ data integrity principles (Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available). All automated actions are gated by human authorization and cryptographic audit logging. Production deployment in a pharmaceutical environment would require formal validation (IQ/OQ/PQ), computerized system qualification, and organizational standard operating procedures.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14+ (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, Recharts, TanStack Query |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn |
| **AI / Orchestration** | OpenRouter (`nvidia/nemotron-3.5-lightning:free`), LangGraph StateGraph, Deterministic Claim Verification |
| **RAG & Vector Store** | Hybrid Keyword (BM25-style) + Dense Vector Embeddings with NumPy Cosine Similarity |
| **Document Processing**| PyPDF, python-docx, openpyxl, hashlib SHA-256 |
| **Dossier Exports** | ReportLab (PDF), python-docx (Word) |
| **Infrastructure** | Docker, docker-compose, Cloud PaaS (Vercel / Render), NGINX ([See DEPLOYMENT.md](DEPLOYMENT.md)) |

---

## 4. Repository Structure

```
gxp-ai-copilot/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API route handlers
│   │   │   ├── documents.py     # Upload, metadata, chunking, draft section
│   │   │   ├── query.py         # RAG Q&A with citations & confidence
│   │   │   ├── compliance.py    # Readiness score, findings, risks, recommendations
│   │   │   ├── evidence.py      # PDF/DOCX evidence pack generation & downloads
│   │   │   ├── workflows.py     # Human-in-the-loop approvals & ServiceNow execution
│   │   │   ├── dashboard.py     # Executive KPI cards, systems inventory
│   │   │   ├── audit_log.py     # Append-only SHA-256 chained audit ledger
│   │   │   ├── agents.py        # Agent observability & telemetry
│   │   │   └── simulation.py    # Continuous compliance monitor trigger & reset
│   │   ├── agents/              # LangGraph multi-agent mesh
│   │   │   ├── supervisor.py    # StateGraph orchestrator
│   │   │   ├── system_knowledge.py # Ownership & applicable SOP retrieval
│   │   │   ├── compliance_agent.py # Checklist evaluator
│   │   │   ├── risk_agent.py    # ICH Q9 risk matrix & GxP impact
│   │   │   ├── evidence_agent.py# PDF & Word evidence pack compiler
│   │   │   ├── recommendation_agent.py # Actionable remediation planner
│   │   │   └── stubs.py         # Enterprise stubs (Change, Incident, IAM, Healing)
│   │   ├── core/                # Config, Security (RBAC), Database session
│   │   ├── integrations/        # Mock enterprise connectors (ServiceNow, Vault, IAM, Monitor)
│   │   ├── models/              # SQLAlchemy entities & SHA-256 hash chaining
│   │   ├── schemas/             # Pydantic v2 domain schemas
│   │   ├── services/            # Document parser, vector store, RAG, compliance engine
│   │   └── main.py              # FastAPI application entrypoint
│   ├── tests/                   # Pytest test suites (unit + end-to-end)
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── app/                     # Next.js App Router screens
│   │   ├── dashboard/           # Executive KPI dashboard & trend charts
│   │   ├── chat/                # Dual-pane AI Copilot & live evidence panel
│   │   ├── compliance/          # Checklist table, findings, draft missing content
│   │   ├── risk/                # ICH Q9 risk register & hazard breakdown
│   │   ├── evidence/            # Dossier generator with live pipeline & PDF/Word downloads
│   │   ├── workflows/           # Pending approvals modal & ServiceNow task confirmation
│   │   ├── audit/               # Cryptographically chained audit ledger & verification
│   │   ├── documents/           # Document uploader & chunk inspector
│   │   ├── systems/             # GxP systems catalog & system detail
│   │   └── admin/               # Multi-agent mesh telemetry & guardrail status
│   ├── components/              # Navbar, Sidebar, modals
│   └── lib/                     # API client & TypeScript interfaces
├── data/
│   ├── mock_enterprise/        # ServiceNow incidents/changes, Vault docs, IAM users
│   ├── sample_documents/       # Real GxP docs (URS with intentional gap, Risk Assessment, SOPs)
│   ├── seed/                    # compliance_checklist.json
│   └── vector_store/            # Hybrid embedding storage
├── docs/                        # Architecture diagrams, API specs, Demo walkthrough
├── infra/                       # docker-compose.yml
└── scripts/
    ├── seed_database.py         # Initial database setup & document ingestion
    └── create_sample_documents.py # Generates GxP sample Word documents
```

---

## 5. Quickstart & Local Setup

### Prerequisites
- Python 3.11 or 3.13
- Node.js v18+ (tested on Node v24) and npm
- Optional: Docker & Docker Desktop

### 1. Backend Setup
```bash
# From workspace root
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r backend/requirements.txt

# Generate sample GxP documents and seed database:
python scripts/seed_database.py

# Run FastAPI backend:
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs on `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`).*

### 2. Frontend Setup
```bash
# In a new terminal:
cd frontend
npm install
npm run dev
```
*Frontend opens at `http://localhost:3000`.*

### 3. Docker One-Click Setup (Alternative)
```bash
cd infra
docker compose up --build
```

---

## 6. Demo Credentials & User Roles

| User Email | Name | Department | Role | Entitlements |
| :--- | :--- | :--- | :--- | :--- |
| `qa@demo.local` | Dr. Elena Rostova | Global Quality Assurance | **QA_COMPLIANCE** | Full review, approve/reject workflows, sign evidence packs |
| `owner@demo.local` | Sarah Jenkins | IT Quality & Validated Systems | **SYSTEM_OWNER** | System management, upload documents, create workflows |
| `auditor@demo.local`| Henrik Lindqvist | Regulatory Affairs & Audit | **AUDITOR** | Read-only inspection, audit ledger verification |
| `admin@demo.local` | System Admin | GxP IT Operations | **ADMIN** | Full platform administration & agent observability |

---

## 7. The 11-Step Primary Demo Scenario

1. **Open Dashboard (`/dashboard`)**:
   - Inspect **System A: Validated LIMS** | Readiness: **82%** | High Risk: **1** | Open Findings: **3**.
2. **Open AI Co-Pilot Chat (`/chat`)**:
   - Ask: *"Is System A audit ready?"*
   - Watch the right-hand **Agent Execution Pipeline** dynamically orchestrate:
     *Supervisor → System Knowledge → Compliance → Risk → Evidence → Recommendation*.
3. **Inspect Grounded Answer**:
   - Copilot answers: *"System A is currently 82% audit ready with 3 active compliance gaps (1 High-Risk finding: Missing formal QA Approval in System_A_URS.docx)..."*
   - Right panel displays **94% Confidence** and citations to `System_A_URS.docx (Section 6, Page 2)`.
4. **Inspect Findings & Citations (`/compliance`)**:
   - View Finding: *"QA Approval Missing from System_A_URS.docx"*.
   - Expand to see exact citation: *"QA Compliance Unit: MISSING - NOT APPROVED"*.
5. **Test Hallucination Protection**:
   - In Chat, ask: *"What is the approval date?"*
   - Copilot honestly answers: *"The QA approval date could not be found in the indexed evidence..."* with **Low Confidence (42%)** and a guardrail warning badge.
6. **Draft Missing Section (`/compliance`)**:
   - Click **"Draft Missing Section"**.
   - Preview the AI-generated 21 CFR Part 11 approval template with prominent watermark:
     `⚠️ AI GENERATED DRAFT — NOT APPROVED — REQUIRES HUMAN REVIEW`.
   - Click **"Export to Word (.docx)"** to download.
7. **Generate Evidence Pack (`/evidence`)**:
   - Click **"Generate New Evidence Pack"**.
   - Watch the live progress pipeline: *Collecting evidence → Validating citations → Traceability matrix → Generating dossier*.
   - Download **PDF Dossier** (ReportLab) and **Word Dossier** (DOCX).
8. **Create Approval Workflow (`/compliance` or `/chat`)**:
   - Click **"Create Approval Workflow"** on the QA sign-off recommendation.
9. **Review in Approvals Center (`/workflows`)**:
   - Review pending card: *Route URS for QA sign-off (CRITICAL)*.
   - Click **"Approve"**.
   - Read the regulatory confirmation modal and submit authorization.
10. **Enterprise ServiceNow Execution**:
    - Workflow executes instantly and displays:
      ✓ Workflow Executed  
      ✓ ServiceNow Task Provisioned: **`SNOW-TASK-1001`** (Assigned to *Sarah Jenkins*).
11. **Verify Tamper-Evident Audit Trail (`/audit`)**:
    - View append-only records with SHA-256 `event_hash` and `previous_hash`.
    - Click **"Verify Cryptographic Chain"** → Green badge: **"All audit trail records cryptographically verified."**
12. **Bonus: Continuous Compliance Monitor Simulation (`/dashboard`)**:
    - Click **"Simulate SOP Expiration"**.
    - `SOP_Document_Management.docx` periodic review window passes.
    - System detects: *"Documentation review overdue."*
    - Readiness dynamically drops: **82% → 76%**!

---

## 8. Verification & Test Suite

Run the full automated pytest suite:
```bash
.venv\Scripts\python.exe -m pytest
```
*All 13 unit and end-to-end integration tests pass, validating document ingestion, hybrid RAG retrieval, deterministic scoring, human approval state machine, ServiceNow ticket creation, and SHA-256 chain integrity.*

---

## 9. Security & Guardrails

1. **Append-Only Audit Ledger**: Zero `DELETE` or `UPDATE` routes exist for audit records.
2. **Non-Bypassable Human Gates**: AI cannot alter compliance records, execute GxP tickets, or sign off on its own recommendations.
3. **No Hallucinated Citations**: Every finding must map to an indexed document chunk. If context is missing, the engine returns an honest "not found" response with low confidence.
4. **Path Traversal Protection**: File uploads are strictly sanitized with filename cleaning and extension whitelisting (`.pdf`, `.docx`, `.xlsx`, `.txt`).
5. **No Committed Secrets**: All configurations read from `.env` with fallback to local demo modes.
