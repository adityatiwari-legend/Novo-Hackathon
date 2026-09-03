import {
  DashboardOverview, System, Document, DocumentChunk, ComplianceFinding,
  Risk, Recommendation, EvidencePack, Workflow, AuditLog, QueryResponse
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error ${res.status}: ${errorBody || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Dashboard & Systems
  getDashboard: () => fetchJson<DashboardOverview>('/dashboard'),
  getSystems: () => fetchJson<System[]>('/systems'),
  getSystem: (id: string) => fetchJson<System>(`/systems/${id}`),

  // Documents
  getDocuments: (systemId?: string) =>
    fetchJson<Document[]>(`/documents${systemId ? `?system_id=${systemId}` : ''}`),
  getDocument: (id: string) => fetchJson<Document>(`/documents/${id}`),
  getDocumentChunks: (id: string) => fetchJson<DocumentChunk[]>(`/documents/${id}/chunks`),
  uploadDocument: async (file: File, systemId: string = 'SYS-LIMS-001') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('system_id', systemId);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${await res.text()}`);
    return res.json() as Promise<Document>;
  },
  draftMissingSection: (data: { section_name: string; document_title: string; system_name: string; finding_context: string }) =>
    fetchJson<{ section_name: string; document_title: string; draft_text: string; watermark: string }>('/documents/draft-section', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getDraftExportUrl: () => `${API_BASE}/documents/draft-section/export`,

  // Traceability & Release Gates
  getReleaseGates: (systemId: string = 'SYS-MES-001') =>
    fetchJson<import('./types').ReleaseGatesResponse>(`/compliance/release-gates?system_id=${systemId}`),
  getTraceability: (systemId: string = 'SYS-MES-001') =>
    fetchJson<import('./types').TraceabilityResponse>(`/compliance/traceability?system_id=${systemId}`),
  getConsistency: (systemId: string = 'SYS-MES-001') =>
    fetchJson<any>(`/compliance/consistency?system_id=${systemId}`),
  getAiHealth: () =>
    fetchJson<any>('/ai/health'),

  // RAG Query
  queryRAG: (question: string, systemId: string = 'SYS-MES-001', top_k: number = 6, mode: string = 'General Q&A') =>
    fetchJson<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify({ question, system_id: systemId, top_k, mode }),
    }),

  // GxP Audit Checklist & Cross-Doc Comparison
  getAuditChecklists: () =>
    fetchJson<import('./types').AuditChecklist[]>('/audit/checklists'),
  getChecklistQuestions: (checklistId: string = 'CKL-TOP25-CORE') =>
    fetchJson<import('./types').AuditQuestion[]>(`/audit/checklists/${checklistId}/questions`),
  executeAudit: (systemId: string = 'SYS-MES-001', checklistId: string = 'CKL-TOP25-CORE', scoringWeights?: Record<string, number>) =>
    fetchJson<import('./types').AuditAssessment>('/audit/execute', {
      method: 'POST',
      body: JSON.stringify({ system_id: systemId, checklist_id: checklistId, scoring_weights: scoringWeights }),
    }),
  getLatestAuditAssessment: (systemId: string = 'SYS-MES-001') =>
    fetchJson<import('./types').AuditAssessment>(`/audit/assessments/latest?system_id=${systemId}`),
  getCrossDocComparison: (systemId: string = 'SYS-MES-001') =>
    fetchJson<import('./types').CrossDocComparisonResponse>(`/audit/comparison?system_id=${systemId}`),
  generateAuditReport: (systemId: string = 'SYS-MES-001', checklistId: string = 'CKL-TOP25-CORE') =>
    fetchJson<import('./types').AuditReportResponse>('/audit/report', {
      method: 'POST',
      body: JSON.stringify({ system_id: systemId, checklist_id: checklistId }),
    }),
  getReportDownloadUrl: (filePath: string) =>
    `${API_BASE}/audit/download?file_path=${encodeURIComponent(filePath)}`,

  // Compliance & Findings
  getReadiness: (systemId: string = 'SYS-MES-001') =>
    fetchJson<{ system_id: string; readiness_score: number; checks: any[]; total_checks: number; passed_checks: number; failed_checks: number; release_recommendation?: string; lifecycle_status?: string }>(`/compliance/readiness/${systemId}`),
  getFindings: (systemId: string = 'SYS-MES-001') =>
    fetchJson<ComplianceFinding[]>(`/compliance/findings?system_id=${systemId}`),
  assessCompliance: (systemId: string = 'SYS-MES-001', generateEvidence: boolean = false) =>
    fetchJson<any>('/compliance/assess', {
      method: 'POST',
      body: JSON.stringify({ system_id: systemId, generate_evidence: generateEvidence }),
    }),

  // Risks & Recommendations
  getRisks: (systemId: string = 'SYS-LIMS-001') =>
    fetchJson<Risk[]>(`/risk?system_id=${systemId}`),
  getRecommendations: (systemId: string = 'SYS-LIMS-001') =>
    fetchJson<Recommendation[]>(`/recommendations?system_id=${systemId}`),

  // Evidence Packs
  getEvidencePacks: (systemId?: string) =>
    fetchJson<EvidencePack[]>(`/evidence${systemId ? `?system_id=${systemId}` : ''}`),
  generateEvidencePack: (systemId: string = 'SYS-LIMS-001') =>
    fetchJson<any>('/evidence/generate', {
      method: 'POST',
      body: JSON.stringify({ system_id: systemId }),
    }),
  getPdfDownloadUrl: (id: string) => `${API_BASE}/evidence/download/${id}/pdf`,
  getDocxDownloadUrl: (id: string) => `${API_BASE}/evidence/download/${id}/docx`,

  // Workflows
  getPendingWorkflows: (systemId?: string) =>
    fetchJson<Workflow[]>(`/workflows/pending${systemId ? `?system_id=${systemId}` : ''}`),
  getAllWorkflows: (systemId?: string) =>
    fetchJson<Workflow[]>(`/workflows${systemId ? `?system_id=${systemId}` : ''}`),
  createWorkflow: (data: { system_id: string; recommendation_id?: string; type?: string; payload?: Record<string, any> }) =>
    fetchJson<Workflow>('/workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  approveWorkflow: (id: string, comment?: string, actor: string = 'qa@demo.local') =>
    fetchJson<Workflow>(`/workflows/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ actor, comment }),
    }),
  rejectWorkflow: (id: string, reason: string, actor: string = 'qa@demo.local') =>
    fetchJson<Workflow>(`/workflows/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ actor, reason }),
    }),

  // Audit Log
  getAuditLogs: (limit: number = 50) =>
    fetchJson<AuditLog[]>(`/audit-log?limit=${limit}`),
  verifyAuditChain: () =>
    fetchJson<{ is_valid: boolean; records_checked: number; message: string }>('/audit-log/verify'),

  // Agents & Simulation
  getAgentsHealth: () => fetchJson<any>('/agents/health'),
  triggerSimulation: (systemId: string = 'SYS-LIMS-001') =>
    fetchJson<any>(`/simulation/trigger?system_id=${systemId}`, { method: 'POST' }),
  resetSimulation: (systemId: string = 'SYS-LIMS-001') =>
    fetchJson<any>(`/simulation/reset?system_id=${systemId}`, { method: 'POST' }),
  getSimulationStatus: () => fetchJson<any>('/simulation/status'),
};
