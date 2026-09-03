'use client';

import React, { useEffect, useState } from 'react';
import {
  CheckCircle2, XCircle, AlertTriangle, FileText, Sparkles, Download,
  GitPullRequest, RefreshCw, ChevronDown, ChevronRight, ShieldCheck, Check,
  Layers, Lock, ShieldAlert, AlertCircle, ArrowRight
} from 'lucide-react';
import { api } from '@/lib/api';
import { ComplianceFinding, Recommendation, ReleaseGate, TraceabilityItem, TraceabilityGap } from '@/lib/types';

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<'gates' | 'traceability' | 'findings' | 'rules'>('gates');
  const [readinessData, setReadinessData] = useState<any>(null);
  const [gatesData, setGatesData] = useState<any>(null);
  const [traceabilityData, setTraceabilityData] = useState<any>(null);
  const [findings, setFindings] = useState<ComplianceFinding[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  // Draft Section Modal State
  const [draftModalOpen, setDraftModalOpen] = useState(false);
  const [draftContent, setDraftContent] = useState<any>(null);
  const [drafting, setDrafting] = useState(false);
  const [workflowCreated, setWorkflowCreated] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [readinessRes, gatesRes, traceRes, findingsRes, recsRes] = await Promise.all([
        api.getReadiness('SYS-MES-001'),
        api.getReleaseGates('SYS-MES-001'),
        api.getTraceability('SYS-MES-001'),
        api.getFindings('SYS-MES-001'),
        api.getRecommendations('SYS-MES-001')
      ]);
      setReadinessData(readinessRes);
      setGatesData(gatesRes);
      setTraceabilityData(traceRes);
      setFindings(findingsRes);
      setRecommendations(recsRes);
    } catch (err) {
      console.error('Failed to load compliance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDraftSection = async (finding: ComplianceFinding) => {
    setDrafting(true);
    setDraftModalOpen(true);
    try {
      const res = await api.draftMissingSection({
        section_name: '4. Document Approvals & Signatures',
        document_title: 'NL-MES-URS-001.docx',
        system_name: 'Novo Life MES PAS-X',
        finding_context: finding.description
      });
      setDraftContent(res);
    } catch (err) {
      console.error(err);
    } finally {
      setDrafting(false);
    }
  };

  const handleCreateWorkflowFromDraft = async () => {
    if (!draftContent) return;
    try {
      const wf = await api.createWorkflow({
        type: 'DRAFT_REMEDIATION_APPROVAL',
        system_id: 'SYS-MES-001',
        payload: {
          section_name: draftContent.section_name,
          document_title: draftContent.document_title,
          draft_text: draftContent.draft_text,
          watermark: draftContent.watermark,
          remediation_justification: 'Automated remediation proposal to address missing Quality Unit authorization.'
        }
      });
      setWorkflowCreated(wf.id);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && !readinessData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-sm font-medium text-slate-500">Loading GxP Release Readiness & Traceability...</p>
        </div>
      </div>
    );
  }

  const filteredMatrix = traceabilityData?.matrix?.filter((m: TraceabilityItem) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'UNVERIFIED') return m.verification_status === 'NOT_PERFORMED';
    if (filterType === 'FUNCTIONAL') return m.type === 'FUNCTIONAL';
    if (filterType === 'NON-FUNCTIONAL') return m.type === 'NON-FUNCTIONAL';
    return true;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">GxP Release Readiness & Compliance</h1>
            <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded border border-blue-200 font-mono">
              SYS-MES-001
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic evaluation of Lifecycle Phase Gates (G1-G6), 50 URS Requirements, and 26 System Risks.
          </p>
        </div>

        {/* Release Decision Callout */}
        <div className="flex items-center gap-3">
          <div className="bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-lg text-right">
            <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider block">Decision</span>
            <span className="text-xs font-bold text-rose-700">
              {gatesData?.overall_decision || 'HOLD / DEFER - DO NOT RELEASE'}
            </span>
          </div>
          <div className="bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg text-right">
            <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">Lifecycle State</span>
            <span className="text-xs font-bold text-amber-800">
              {gatesData?.lifecycle_status || 'PRE-OPERATIONAL / NOT ACTIVATED'}
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('gates')}
          className={`px-4 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
            activeTab === 'gates'
              ? 'border-blue-600 text-blue-700 bg-blue-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Release Gates (G1 - G6)</span>
          <span className="bg-rose-100 text-rose-700 px-1.5 py-0.2 rounded text-[10px] font-bold">2 Blocked</span>
        </button>

        <button
          onClick={() => setActiveTab('traceability')}
          className={`px-4 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
            activeTab === 'traceability'
              ? 'border-blue-600 text-blue-700 bg-blue-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Traceability Matrix (50 URS)</span>
          <span className="bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded text-[10px] font-bold">
            {traceabilityData?.total_requirements || 50}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('findings')}
          className={`px-4 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
            activeTab === 'findings'
              ? 'border-blue-600 text-blue-700 bg-blue-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Active Findings & Remediation</span>
          <span className="bg-amber-100 text-amber-700 px-1.5 py-0.2 rounded text-[10px] font-bold">
            {findings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
            activeTab === 'rules'
              ? 'border-blue-600 text-blue-700 bg-blue-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Rule Engine (compliance_rules.json)</span>
          <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded text-[10px] font-bold">
            {readinessData?.total_checks || 15}
          </span>
        </button>
      </div>

      {/* TAB 1: Release Gates Evaluation */}
      {activeTab === 'gates' && (
        <div className="space-y-4">
          {/* Critical Blocking Alert */}
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-rose-900">
                System Release Blocked: Gates G5 & G6 are NOT MET
              </h3>
              <p className="text-xs text-rose-700 mt-1">
                Commercial release for batch execution is strictly prohibited. The IT Implementation Report (NL-MES-IREP-001)
                records that intended-use verification was not performed, residual risks are unrated, and operational training is incomplete.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-semibold">
                <span className="bg-white border border-rose-300 text-rose-800 px-2 py-0.5 rounded">
                  • G5 Blocker: Intended-Use Verification (OV/PfV/UAT) Not Performed
                </span>
                <span className="bg-white border border-rose-300 text-rose-800 px-2 py-0.5 rounded">
                  • G5 Blocker: 49 Working High Residual Risks Unaccepted
                </span>
                <span className="bg-white border border-rose-300 text-rose-800 px-2 py-0.5 rounded">
                  • G6 Blocker: Shopfloor Training Incomplete (0 of 250 trained)
                </span>
              </div>
            </div>
          </div>

          {/* Gates List */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {gatesData?.gates?.map((g: ReleaseGate) => {
              const isMet = g.status === 'MET';
              return (
                <div
                  key={g.gate_code}
                  className={`bg-white rounded-xl border p-4 shadow-sm flex flex-col justify-between ${
                    isMet ? 'border-slate-200' : 'border-rose-300 bg-rose-50/20'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-blue-700 font-mono">{g.gate_code}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        isMet ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                      }`}>
                        {g.status}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-900">{g.gate_name}</h4>
                    <p className="text-[11px] text-slate-500 mt-1">
                      Evidence: <span className="font-mono text-slate-700">{g.evidence_doc}</span> ({g.evidence_section})
                    </p>
                    {g.blocking_reason && (
                      <div className="mt-3 bg-rose-50 border border-rose-200 p-2 rounded text-[11px] text-rose-800">
                        <b>Blocking Reason:</b> {g.blocking_reason}
                      </div>
                    )}
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-100 text-[10px] text-slate-400">
                    Grounded in MLGP & IREP Lifecycle Baseline
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: Traceability Matrix */}
      {activeTab === 'traceability' && (
        <div className="space-y-4">
          {/* Summary Gaps Callout */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {traceabilityData?.gaps?.map((gap: TraceabilityGap, idx: number) => (
              <div key={idx} className="bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-rose-600 uppercase font-mono">{gap.gap_code}</span>
                  <span className="text-[9px] bg-rose-100 text-rose-800 px-1.5 py-0.5 rounded font-bold">{gap.severity}</span>
                </div>
                <h5 className="text-xs font-bold text-slate-800">{gap.title}</h5>
                <p className="text-[11px] text-slate-500 mt-1">{gap.description}</p>
                <div className="mt-2 text-[10px] text-blue-600 font-mono">
                  Source: {gap.source_document} (Page {gap.source_page})
                </div>
              </div>
            ))}
          </div>

          {/* Filter Toolbar */}
          <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700">Filter View:</span>
              <button
                onClick={() => setFilterType('ALL')}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  filterType === 'ALL' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'
                }`}
              >
                All 50 Requirements
              </button>
              <button
                onClick={() => setFilterType('UNVERIFIED')}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  filterType === 'UNVERIFIED' ? 'bg-rose-600 text-white' : 'bg-white text-rose-700 border border-rose-200'
                }`}
              >
                Unverified (Open Blockers)
              </button>
              <button
                onClick={() => setFilterType('FUNCTIONAL')}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  filterType === 'FUNCTIONAL' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'
                }`}
              >
                Functional (25)
              </button>
              <button
                onClick={() => setFilterType('NON-FUNCTIONAL')}
                className={`px-2 py-1 rounded text-[11px] font-medium ${
                  filterType === 'NON-FUNCTIONAL' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'
                }`}
              >
                Non-Functional (25)
              </button>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">
              Showing {filteredMatrix.length} of {traceabilityData?.total_requirements || 50}
            </span>
          </div>

          {/* Matrix Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-100 text-slate-700 sticky top-0 z-10 border-b border-slate-200">
                  <tr>
                    <th className="p-2.5 font-bold">URS Code</th>
                    <th className="p-2.5 font-bold">Requirement Description</th>
                    <th className="p-2.5 font-bold">Type</th>
                    <th className="p-2.5 font-bold">FS Module</th>
                    <th className="p-2.5 font-bold">Risk Link</th>
                    <th className="p-2.5 font-bold">Residual Risk</th>
                    <th className="p-2.5 font-bold">Verification Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredMatrix.map((item: TraceabilityItem) => (
                    <tr key={item.requirement_id} className="hover:bg-slate-50">
                      <td className="p-2.5 font-mono font-bold text-blue-700 whitespace-nowrap">{item.requirement_id}</td>
                      <td className="p-2.5 text-slate-800 max-w-xs truncate">{item.requirement_text}</td>
                      <td className="p-2.5 whitespace-nowrap">
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                          item.type === 'FUNCTIONAL' ? 'bg-blue-50 text-blue-800' : 'bg-purple-50 text-purple-800'
                        }`}>
                          {item.type}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono text-slate-600 whitespace-nowrap">{item.fs_module}</td>
                      <td className="p-2.5 whitespace-nowrap">
                        <span className="font-mono text-[11px] text-slate-700">{item.risk_id}</span>
                        <span className={`ml-1 text-[9px] font-bold px-1 rounded ${
                          item.risk_level === 'HIGH' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {item.risk_level}
                        </span>
                      </td>
                      <td className="p-2.5 whitespace-nowrap">
                        <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded font-semibold">
                          {item.residual_risk_state}
                        </span>
                      </td>
                      <td className="p-2.5 whitespace-nowrap">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          item.verification_status === 'COMPLETE' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                        }`}>
                          {item.verification_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Active Findings */}
      {activeTab === 'findings' && (
        <div className="space-y-4">
          <div className="space-y-3">
            {findings.map((f: ComplianceFinding) => {
              const isExpanded = expandedFinding === f.id;
              return (
                <div key={f.id} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                  <div
                    onClick={() => setExpandedFinding(isExpanded ? null : f.id)}
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        f.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                        f.severity === 'HIGH' ? 'bg-orange-100 text-orange-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {f.severity}
                      </span>
                      <h4 className="text-xs font-bold text-slate-900">{f.title}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDraftSection(f);
                        }}
                        className="bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1"
                      >
                        <Sparkles className="w-3 h-3 text-blue-600" />
                        <span>AI Remediation Draft</span>
                      </button>
                      {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 bg-slate-50/50 border-t border-slate-100 text-xs space-y-2">
                      <p className="text-slate-700"><b>Description:</b> {f.description}</p>
                      <p className="text-slate-700"><b>Recommended Action:</b> {f.recommended_action}</p>
                      {f.source_citations?.length > 0 && (
                        <div className="text-[11px] text-blue-600 font-mono">
                          Citation: {f.source_citations[0].document} (Page {f.source_citations[0].page}, Section: {f.source_citations[0].section})
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: Rules Engine */}
      {activeTab === 'rules' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
          <h3 className="text-xs font-bold text-slate-900 mb-3">Configurable Compliance Checklist Results</h3>
          <div className="space-y-2">
            {readinessData?.checks?.map((c: any, idx: number) => {
              const isPass = c.status === 'PASS';
              return (
                <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                  <div className="flex items-center gap-2.5">
                    {isPass ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <XCircle className="w-4 h-4 text-rose-600 shrink-0" />}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-800">{c.check_code}</span>
                        <span className="text-slate-500 font-semibold">[{c.category}]</span>
                      </div>
                      <p className="text-[11px] text-slate-600 mt-0.5">{c.requirement}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5 italic">{c.evidence}</p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      isPass ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {c.status}
                    </span>
                    {!isPass && <span className="block text-[10px] text-rose-600 mt-1 font-bold">-{c.penalty} pts</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Draft Remediation Section Modal with Watermark */}
      {draftModalOpen && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden">
            <div className="bg-[#002B49] text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold">AI Drafted Remediation Proposal</h3>
              </div>
              <button onClick={() => setDraftModalOpen(false)} className="text-white hover:opacity-75 font-bold">✕</button>
            </div>

            <div className="p-6 space-y-4">
              {/* Prominent Red Watermark Warning */}
              <div className="bg-rose-50 border-2 border-dashed border-rose-300 p-3 rounded-lg text-center">
                <span className="text-xs font-extrabold text-rose-700 tracking-wider uppercase block">
                  ⚠️ AI DRAFT - NOT FOR REGULATORY SUBMISSION
                </span>
                <span className="text-[11px] text-rose-600 mt-0.5 block">
                  Must undergo human Quality Assurance review and authorization before inclusion in lifecycle baseline.
                </span>
              </div>

              {drafting ? (
                <div className="py-8 flex flex-col items-center justify-center gap-2">
                  <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
                  <p className="text-xs text-slate-500">Generating grounded remediation section draft...</p>
                </div>
              ) : (
                <>
                  <div className="text-xs space-y-1">
                    <p><b>Target Document:</b> {draftContent?.document_title}</p>
                    <p><b>Target Section:</b> {draftContent?.section_name}</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {draftContent?.draft_text}
                  </div>
                </>
              )}

              {workflowCreated ? (
                <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-lg flex items-center gap-2 text-xs text-emerald-800 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Remediation Workflow Routed to QA Approval (# {workflowCreated.slice(0, 8)})</span>
                </div>
              ) : (
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setDraftModalOpen(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateWorkflowFromDraft}
                    disabled={drafting}
                    className="px-3.5 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 flex items-center gap-1.5 shadow-sm"
                  >
                    <GitPullRequest className="w-3.5 h-3.5" />
                    <span>Route to QA for Approval</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
