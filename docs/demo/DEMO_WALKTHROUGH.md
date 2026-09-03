# Primary Demo Scenario: 11-Step Walkthrough

This document outlines the exact, end-to-end hackathon demo script for the **Agentic AI Co-Pilot for GxP IT System Management** (Novo Nordisk Hackathon 2026).

---

### Step 1: Open Executive Dashboard
- **URL**: `http://localhost:3000/dashboard`
- **What the Judges See**:
  - Top KPI cards:
    - Audit Readiness Index: **82%**
    - Compliance Score: **82%**
    - Open Findings: **3** (1 High, 2 Medium)
    - High/Critical Risks: **1**
    - Pending Approvals: **0** (or pending workflows)
    - Evidence Packs: **1+**
  - Systems Table:
    - **System A: Validated LIMS** | GxP | **82%** | **HIGH** | **3 Findings** | Status: **Attention Required**
  - Readiness Trend chart showing historic progression.

---

### Step 2: Open Copilot Chat
- **URL**: `http://localhost:3000/chat`
- **User Prompt**:
  > *"Is System A audit ready?"*
- **Visual Feedback**:
  - Right-hand **Agent Execution Pipeline** lights up dynamically:
    1. ✓ Supervisor analyzed request and routed tasks
    2. ✓ System Knowledge retrieved 8 grounded chunks
    3. ✓ Compliance evaluated 8 checklist requirements
    4. ✓ Risk matrix completed (High GxP impact)
    5. ✓ Recommendations synthesized

---

### Step 3: Inspect Grounded Assessment
- **AI Response**:
  > *"System A (Validated LIMS) is currently 82% audit ready. While business and technical approvals, 21 CFR Part 11 requirements, and initial risk assessments are documented, System A has 3 active compliance gaps (1 High-Risk finding: Missing formal QA Approval in System_A_URS.docx, and 2 Medium-Risk findings: traceability matrix gap and document review cycle alert). Human QA approval is required prior to operational qualification."*
- **Right Panel Evidence**:
  - Confidence: **94% (High)**
  - Sources:
    - `System_A_URS.docx` — Section: *Document Approvals & Signatures*, Page 2
    - `System_A_Risk_Assessment.docx` — Section: *Risk Evaluation Matrix*, Page 1
    - `SOP_Change_Control.docx` — Section: *Change Classification & Severity*, Page 1

---

### Step 4: Click "View Findings" & Citation Jump
- Navigate to `/compliance`.
- Expand **Finding 1**: *"QA Approval Missing from System_A_URS.docx"*
  - Severity: **HIGH**
  - Citation: Click citation to view exact source context:
    > *"QA Compliance Unit: MISSING - NOT APPROVED (Date: Not found)"*

---

### Step 5: Test Hallucination Protection
- In Chat (`/chat`), ask:
  > *"What is the approval date?"*
- **AI Response**:
  > *"The QA approval date could not be found in the indexed evidence. In System_A_URS.docx (Section 6: Document Approvals & Signatures), the QA Compliance signature is marked as 'MISSING - NOT APPROVED' with date 'Not found'."*
- **Confidence**: **42% (Low)**
- **Warning Badge**: *"Information explicitly missing or not found in source documentation."*
- *Judge takeaway*: AI never fabricates regulatory records or dates.

---

### Step 6: Draft Missing Content
- On the Compliance Screen (`/compliance`) under the unapproved URS finding, click **"Draft Missing Section"**.
- View interactive preview:
  - Header: `⚠️ AI-GENERATED DRAFT — NOT APPROVED — REQUIRES HUMAN REVIEW`
  - Body: Complete 21 CFR Part 11 compliant approval section template.
- Click **"Export DOCX"** to download the standalone Word document.

---

### Step 7: Generate Audit Evidence Pack
- Navigate to `/evidence`.
- Click **"Generate Evidence Pack"**.
- Watch real-time compilation:
  - Collecting evidence → Validating citations → Traceability matrix → Generating dossier.
- Download **PDF Dossier** (ReportLab) and **Word Dossier** (DOCX).
- Show the cover page, executive summary, verified citations, and SHA-256 audit summary.

---

### Step 8: Create Human Approval Workflow
- In Chat or Compliance screen, locate Recommendation:
  > *"Route URS to QA/System Owner for formal approval"*
- Click **"Create Approval Workflow"**.

---

### Step 9: Open Approvals Screen
- Navigate to `/workflows`.
- See pending card:
  - System: `SYS-LIMS-001`
  - Action: *Route URS for QA sign-off*
  - Priority: `CRITICAL`
- Click **"Approve"**.
- Modal displays:
  > *"You are approving an AI-generated workflow. The AI recommendation will not become effective until this approval is recorded."*
- Confirm approval.

---

### Step 10: Mock ServiceNow Ticket Created
- Immediately shows:
  - ✓ Workflow Executed
  - ✓ ServiceNow Task Created: **`SNOW-TASK-1001`**
  - State: *Work in Progress*
  - Assigned To: *Sarah Jenkins (Technical System Owner)*

---

### Step 11: Tamper-Evident Audit Trail
- Navigate to `/audit`.
- See immutable log ledger:
  - Human Approved GxP Workflow (`qa@demo.local`)
  - Executed ServiceNow Task (`SNOW-TASK-1001`)
  - Each row shows SHA-256 `event_hash` and `previous_hash`.
- Click **"Verify Hash Chain Integrity"**:
  - Green checkmark: **"All audit trail records cryptographically verified."**

---

### Bonus: Continuous Compliance Monitor Simulation
- On Dashboard (`/dashboard`), click **"Trigger SOP Expiration Simulation"**.
- System simulates `SOP_Document_Management.docx` periodic review expiring.
- Banner alert: *"New compliance gap detected: SOP_Document_Management.docx is overdue for periodic review."*
- Dashboard dynamically recalculates: **Readiness drops from 82% → 76%**.
- Demonstrates always-on compliance rather than periodic panic!
