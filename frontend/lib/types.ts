export interface System {
  id: string;
  name: string;
  description: string;
  owner_id?: string;
  criticality: string;
  gxp_status: string;
  business_owner?: string;
  last_assessed_at?: string;
  created_at?: string;
  readiness_score: number;
  high_risks_count: number;
  open_findings_count: number;
}

export interface Document {
  id: string;
  title: string;
  document_type: string;
  system_id: string;
  version: string;
  owner_id: string;
  status: string;
  review_date: string;
  approval_status: string;
  source_system: string;
  file_path: string;
  checksum: string;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  chunk_count?: number;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  page_number?: number;
  section?: string;
  metadata_json: Record<string, any>;
}

export interface ComplianceCheck {
  id: string;
  system_id: string;
  check_code: string;
  requirement: string;
  description?: string;
  status: 'PASS' | 'FAIL' | 'WARNING';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  evidence?: string;
  citation_json: Record<string, any>;
  created_at: string;
}

export interface ComplianceFinding {
  id: string;
  system_id: string;
  document_id?: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'IN_REVIEW' | 'REMEDIATED' | 'ACCEPTED';
  confidence: number;
  source_citations: Array<Record<string, any>>;
  recommended_action?: string;
  created_at: string;
}

export interface Risk {
  id: string;
  system_id: string;
  finding_id?: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  impact_type: string;
  likelihood: string;
  impact: string;
  score: number;
  rationale: string;
  control_mapping?: string;
  created_at: string;
}

export interface Recommendation {
  id: string;
  system_id: string;
  finding_id?: string;
  source_agent: string;
  title: string;
  description: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  rationale: string;
  suggested_owner?: string;
  related_finding?: string;
  status: 'PROPOSED' | 'IN_WORKFLOW' | 'APPROVED' | 'REJECTED' | 'COMPLETED';
  confidence: number;
  created_at: string;
}

export interface EvidencePack {
  id: string;
  system_id: string;
  title: string;
  version: string;
  scope: string;
  file_path?: string;
  docx_file_path?: string;
  citations_json: Array<Record<string, any>>;
  status: string;
  generated_by: string;
  approved_by?: string;
  created_at: string;
}

export interface Workflow {
  id: string;
  type: string;
  system_id: string;
  recommendation_id?: string;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXECUTED';
  requires_approval: boolean;
  approved_by?: string;
  rejection_reason?: string;
  approved_at?: string;
  executed_at?: string;
  payload_json: Record<string, any>;
  created_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  actor_type: string;
  actor_id: string;
  user_id?: string;
  agent_name?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  request_id?: string;
  details_json: Record<string, any>;
  previous_hash: string;
  event_hash: string;
}

export interface SourceCitation {
  document: string;
  page?: number;
  section?: string;
  snippet?: string;
  relevance_score?: number;
}

export interface QueryResponse {
  answer: string;
  confidence: number;
  sources: SourceCitation[];
  citations: string[];
  retrieved_chunks: Array<Record<string, any>>;
  warnings: string[];
  agent_execution: Array<{ agent: string; status: string }>;
}

export interface DashboardOverview {
  system_name: string;
  system_id: string;
  readiness_score: number;
  compliance_score: number;
  open_findings: number;
  high_critical_risks: number;
  pending_approvals: number;
  evidence_packs_count: number;
  gxp_status: string;
  release_recommendation?: string;
  lifecycle_status?: string;
  readiness_trend: Array<{ timestamp: string; score: number }>;
  findings_by_severity: Record<string, number>;
  systems_summary: Array<Record<string, any>>;
  agent_health: Record<string, string>;
}

export interface ReleaseGate {
  gate_code: string;
  gate_name: string;
  status: string;
  evidence_doc?: string;
  evidence_section?: string;
  blocking_reason?: string;
  critical?: boolean;
}

export interface ReleaseGatesResponse {
  system_id: string;
  overall_decision: string;
  lifecycle_status: string;
  gates_evaluated: number;
  met_gates_count: number;
  blocked_gates_count: number;
  gates: ReleaseGate[];
  blocking_reasons: string[];
}

export interface TraceabilityItem {
  requirement_id: string;
  requirement_text: string;
  type: string;
  fs_module: string;
  risk_id: string;
  risk_level: string;
  residual_risk_state: string;
  verification_id: string;
  verification_status: string;
  implementation_status: string;
  release_blocker: boolean;
}

export interface TraceabilityGap {
  gap_code: string;
  title: string;
  description: string;
  severity: string;
  source_document: string;
  source_section: string;
  source_page: number;
  affected_count: number;
}

export interface TraceabilityResponse {
  system_id: string;
  total_requirements: number;
  verified_count: number;
  unverified_count: number;
  gaps_count: number;
  gaps: TraceabilityGap[];
  matrix: TraceabilityItem[];
}

export interface AuditQuestion {
  id: string;
  checklist_id: string;
  sequence: number;
  phase_no?: string;
  lifecycle_phase?: string;
  audit_domain?: string;
  control_topic?: string;
  priority: string;
  audit_question: string;
  follow_up_probe?: string;
  audit_rationale?: string;
  expected_evidence?: string;
  sampling_triangulation?: string;
  primary_roles?: string;
  regulatory_alignment?: string;
  source_urls?: string;
  red_flags?: string;
  sheet_name?: string;
  row_number?: number;
  weight: number;
}

export interface AuditChecklist {
  id: string;
  title: string;
  version: string;
  source_file: string;
  description?: string;
  questions_count?: number;
}

export interface AuditAssessmentItem {
  sequence: number;
  question_id: string;
  priority: string;
  lifecycle_phase: string;
  control_topic: string;
  audit_question: string;
  status: 'PASS' | 'PARTIAL' | 'FAIL' | 'NOT_EVIDENCED' | 'NOT_APPLICABLE';
  evidence_quality: string;
  confidence: number;
  evidence_citations: string[];
  expected_controls?: string;
  observed_evidence?: string;
  gap_description?: string;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  recommendation?: string;
  benchmark_note?: string;
}

export interface AuditAssessment {
  id: string;
  system_id: string;
  checklist_id: string;
  assessed_at: string;
  readiness_score: number;
  total_questions: number;
  passed_count: number;
  partial_count: number;
  failed_count: number;
  not_evidenced_count: number;
  na_count: number;
  critical_findings_count: number;
  high_findings_count: number;
  medium_findings_count: number;
  low_findings_count: number;
  items: AuditAssessmentItem[];
  findings: Array<Record<string, any>>;
  lifecycle_gaps: Array<Record<string, any>>;
  status: string;
}

export interface CrossDocComparisonItem {
  topic: string;
  master_sop_section: string;
  sop_requirement: string;
  mes_observed: string;
  mes_citations: string[];
  sop_citations: string[];
  lims_benchmark_ref?: string;
  alignment_status: 'ALIGNED' | 'POTENTIAL_LIFECYCLE_DEVIATION' | 'EVIDENCE_GAP';
  impact: string;
  recommended_action: string;
}

export interface CrossDocComparisonResponse {
  system_id: string;
  system_name: string;
  comparison_date: string;
  items: CrossDocComparisonItem[];
  total_compared: number;
  deviations_count: number;
  gaps_count: number;
  aligned_count: number;
}

export interface AuditReportResponse {
  success: boolean;
  pdf_path?: string;
  docx_path?: string;
  summary: string;
  readiness_score: number;
  disclaimer: string;
}

