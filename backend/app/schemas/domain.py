from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# ----------------- User & System -----------------
class UserBase(BaseModel):
    name: str
    email: str
    role: str
    department: Optional[str] = None
    permissions: List[str] = []

class UserResponse(UserBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SystemBase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    criticality: str = "GxP-Critical"
    gxp_status: str = "GxP"
    business_owner: Optional[str] = None

class SystemResponse(SystemBase):
    last_assessed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    readiness_score: Optional[int] = 82
    high_risks_count: Optional[int] = 1
    open_findings_count: Optional[int] = 3
    class Config:
        from_attributes = True

# ----------------- Document & Chunks -----------------
class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    title: str
    document_type: str
    system_id: Optional[str] = None
    version: str
    owner_id: Optional[str] = None
    status: str
    review_date: Optional[str] = None
    approval_status: str
    source_system: str
    file_path: str
    checksum: str
    metadata_json: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = 0
    class Config:
        from_attributes = True

# ----------------- Compliance -----------------
class ComplianceCheckResponse(BaseModel):
    id: str
    system_id: str
    document_id: Optional[str] = None
    check_code: str
    requirement: str
    description: Optional[str] = None
    status: str
    severity: str
    evidence: Optional[str] = None
    citation_json: Dict[str, Any] = {}
    created_at: datetime
    class Config:
        from_attributes = True

class ComplianceFindingResponse(BaseModel):
    id: str
    system_id: str
    document_id: Optional[str] = None
    title: str
    description: str
    severity: str
    status: str
    confidence: float
    source_citations: List[Dict[str, Any]] = []
    recommended_action: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Risk -----------------
class RiskResponse(BaseModel):
    id: str
    system_id: str
    finding_id: Optional[str] = None
    risk_level: str
    impact_type: str
    likelihood: str
    impact: str
    score: int
    rationale: str
    control_mapping: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Recommendation -----------------
class RecommendationResponse(BaseModel):
    id: str
    system_id: str
    finding_id: Optional[str] = None
    source_agent: str
    title: str
    description: str
    priority: str
    rationale: str
    suggested_owner: Optional[str] = None
    status: str
    confidence: float
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Evidence Pack -----------------
class EvidencePackResponse(BaseModel):
    id: str
    system_id: str
    title: str
    version: str
    scope: str
    file_path: Optional[str] = None
    docx_file_path: Optional[str] = None
    citations_json: List[Dict[str, Any]] = []
    status: str
    generated_by: str
    approved_by: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Workflow -----------------
class WorkflowCreateRequest(BaseModel):
    system_id: str
    recommendation_id: Optional[str] = None
    type: str = "REMEDIATION_TASK"
    payload: Dict[str, Any] = {}

class WorkflowApprovalRequest(BaseModel):
    actor: str = "qa@demo.local"
    comment: Optional[str] = "Approved after review of evidence and mitigation plan."

class WorkflowRejectionRequest(BaseModel):
    actor: str = "qa@demo.local"
    reason: str

class WorkflowResponse(BaseModel):
    id: str
    type: str
    system_id: str
    recommendation_id: Optional[str] = None
    status: str
    requires_approval: bool
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    payload_json: Dict[str, Any] = {}
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Audit Trail -----------------
class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    actor_type: str
    actor_id: str
    user_id: Optional[str] = None
    agent_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    request_id: Optional[str] = None
    details_json: Dict[str, Any] = {}
    previous_hash: str
    event_hash: str
    class Config:
        from_attributes = True

class AuditChainVerificationResponse(BaseModel):
    is_valid: bool
    records_checked: int
    message: str

# ----------------- RAG & Query -----------------
class SourceCitation(BaseModel):
    document: str
    page: Optional[int] = None
    section: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None

class QueryRequest(BaseModel):
    question: str
    system_id: Optional[str] = "SYS-MES-001"
    mode: Optional[str] = "General Q&A"
    top_k: int = 6

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceCitation] = []
    citations: List[str] = []
    retrieved_chunks: List[Dict[str, Any]] = []
    warnings: List[str] = []
    agent_execution: List[Dict[str, str]] = []

# ----------------- Agent Output Schema -----------------
class AgentResult(BaseModel):
    agent: str
    status: str = "completed"
    confidence: float
    findings: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

# ----------------- Dashboard -----------------
class DashboardOverview(BaseModel):
    system_name: str
    system_id: str
    readiness_score: int
    compliance_score: int
    open_findings: int
    high_critical_risks: int
    pending_approvals: int
    evidence_packs_count: int
    gxp_status: str
    release_recommendation: Optional[str] = "HOLD / DEFER - DO NOT RELEASE"
    lifecycle_status: Optional[str] = "PRE-OPERATIONAL / NOT ACTIVATED"
    readiness_trend: List[Dict[str, Any]]
    findings_by_severity: Dict[str, int]
    systems_summary: List[Dict[str, Any]]
    agent_health: Dict[str, str]

# ----------------- Audit Checklist & Assessment -----------------
class AuditQuestionResponse(BaseModel):
    id: str
    checklist_id: str
    sequence: int
    phase_no: Optional[str] = None
    lifecycle_phase: Optional[str] = None
    audit_domain: Optional[str] = None
    control_topic: Optional[str] = None
    priority: str
    audit_question: str
    follow_up_probe: Optional[str] = None
    audit_rationale: Optional[str] = None
    expected_evidence: Optional[str] = None
    sampling_triangulation: Optional[str] = None
    primary_roles: Optional[str] = None
    regulatory_alignment: Optional[str] = None
    source_urls: Optional[str] = None
    red_flags: Optional[str] = None
    sheet_name: Optional[str] = None
    row_number: Optional[int] = None
    weight: int = 10
    class Config:
        from_attributes = True

class AuditChecklistResponse(BaseModel):
    id: str
    title: str
    version: str
    source_file: str
    description: Optional[str] = None
    questions_count: Optional[int] = 0
    questions: Optional[List[AuditQuestionResponse]] = None
    class Config:
        from_attributes = True

class AuditAssessmentItem(BaseModel):
    sequence: int
    question_id: str
    priority: str
    lifecycle_phase: str
    control_topic: str
    audit_question: str
    status: str  # PASS, PARTIAL, FAIL, NOT_EVIDENCED, NOT_APPLICABLE
    evidence_quality: str  # Found, Partial, Missing, Conflicting
    confidence: float
    evidence_citations: List[str] = []
    expected_controls: Optional[str] = None
    observed_evidence: Optional[str] = None
    gap_description: Optional[str] = None
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation: Optional[str] = None
    benchmark_note: Optional[str] = None

class AuditAssessmentResponse(BaseModel):
    id: str
    system_id: str
    checklist_id: str
    assessed_at: datetime
    readiness_score: float
    total_questions: int
    passed_count: int
    partial_count: int
    failed_count: int
    not_evidenced_count: int
    na_count: int
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    items: List[AuditAssessmentItem] = []
    findings: List[Dict[str, Any]] = []
    lifecycle_gaps: List[Dict[str, Any]] = []
    status: str
    class Config:
        from_attributes = True

class AuditExecuteRequest(BaseModel):
    system_id: Optional[str] = "SYS-MES-001"
    checklist_id: Optional[str] = "CKL-TOP25-CORE"
    scoring_weights: Optional[Dict[str, float]] = None

class CrossDocComparisonItem(BaseModel):
    topic: str
    master_sop_section: str
    sop_requirement: str
    mes_observed: str
    mes_citations: List[str]
    sop_citations: List[str]
    lims_benchmark_ref: Optional[str] = None
    alignment_status: str  # ALIGNED, POTENTIAL_LIFECYCLE_DEVIATION, EVIDENCE_GAP
    impact: str
    recommended_action: str

class CrossDocComparisonResponse(BaseModel):
    system_id: str
    system_name: str
    comparison_date: datetime
    items: List[CrossDocComparisonItem]
    total_compared: int
    deviations_count: int
    gaps_count: int
    aligned_count: int

class AuditReportRequest(BaseModel):
    system_id: Optional[str] = "SYS-MES-001"
    checklist_id: Optional[str] = "CKL-TOP25-CORE"
    format: Optional[str] = "BOTH"  # PDF, DOCX, BOTH

class AuditReportResponse(BaseModel):
    success: bool
    pdf_path: Optional[str] = None
    docx_path: Optional[str] = None
    summary: str
    readiness_score: float
    disclaimer: str
