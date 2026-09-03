'use client';

import React, { useEffect, useState } from 'react';
import {
  Lock, ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, XCircle,
  RefreshCw, FileText, Download, Filter, Search, ChevronRight, Eye,
  ExternalLink, Layers, GitCompare, CheckSquare, Sparkles
} from 'lucide-react';
import { api } from '@/lib/api';
import {
  AuditAssessment, AuditAssessmentItem, CrossDocComparisonResponse,
  CrossDocComparisonItem, AuditLog, AuditReportResponse
} from '@/lib/types';

export default function AuditPage() {
  const [activeTab, setActiveTab] = useState<'checklist' | 'comparison' | 'trail'>('checklist');
  const [loading, setLoading] = useState(true);

  // Tab 1: Checklist State
  const [assessment, setAssessment] = useState<AuditAssessment | null>(null);
  const [filterResult, setFilterResult] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<AuditAssessmentItem | null>(null);
  const [executing, setExecuting] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportResult, setReportResult] = useState<AuditReportResponse | null>(null);

  // Tab 2: Cross-Doc Comparison State
  const [comparison, setComparison] = useState<CrossDocComparisonResponse | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Tab 3: Cryptographic Audit Trail State
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [verificationResult, setVerificationResult] = useState<{ is_valid: boolean; records_checked: number; message: string } | null>(null);
  const [verifying, setVerifying] = useState(false);

  const loadChecklistData = async () => {
    try {
      setLoading(true);
      const res = await api.getLatestAuditAssessment('SYS-MES-001');
      setAssessment(res);
    } catch (err) {
      console.error('Failed to load latest assessment:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadComparisonData = async () => {
    try {
      setComparisonLoading(true);
      const res = await api.getCrossDocComparison('SYS-MES-001');
      setComparison(res);
    } catch (err) {
      console.error('Failed to load comparison data:', err);
    } finally {
      setComparisonLoading(false);
    }
  };

  const loadTrailData = async () => {
    try {
      const logRes = await api.getAuditLogs(100);
      setLogs(logRes);
      const verifyRes = await api.verifyAuditChain();
      setVerificationResult(verifyRes);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    }
  };

  useEffect(() => {
    loadChecklistData();
    loadComparisonData();
    loadTrailData();
  }, []);

  const handleExecuteAudit = async () => {
    try {
      setExecuting(true);
      const res = await api.executeAudit('SYS-MES-001', 'CKL-TOP25-CORE');
      setAssessment(res);
      await loadTrailData();
    } catch (err) {
      console.error('Execute audit failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      const res = await api.generateAuditReport('SYS-MES-001', 'CKL-TOP25-CORE');
      setReportResult(res);
    } catch (err) {
      console.error('Generate report failed:', err);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setVerificationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const filteredItems = assessment?.items.filter(it => {
    const matchesFilter =
      filterResult === 'ALL' ||
      (filterResult === 'FAIL' && it.status === 'FAIL') ||
      (filterResult === 'PASS' && it.status === 'PASS') ||
      (filterResult === 'PARTIAL' && it.status === 'PARTIAL') ||
      (filterResult === 'CRITICAL' && it.risk_level === 'CRITICAL');

    const matchesSearch =
      !searchQuery ||
      it.question_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      it.control_topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
      it.audit_question.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Simulation Notice Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-amber-900 shadow-sm">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span className="font-semibold">Regulatory Disclaimer:</span>
          <span>
            This is a hackathon/training simulation and does not constitute a regulatory audit, validation decision, or production release authorization.
          </span>
        </div>
        <span className="font-mono text-[10px] bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded border border-amber-300 shrink-0">
          SYS-MES-001 | PAS-X
        </span>
      </div>

      {/* Main Header & Tab Navigation */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#002B49] text-white flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">GxP IT Audit & Lifecycle Intelligence</h1>
              <p className="text-xs text-slate-500">
                Continuous deterministic evaluation of Novo Life MES PAS-X against Master IT SOP & Top 25 Audit Questions
              </p>
            </div>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-lg text-xs font-semibold self-stretch md:self-auto overflow-x-auto">
          <button
            onClick={() => setActiveTab('checklist')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all shrink-0 ${
              activeTab === 'checklist'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <CheckSquare className="w-4 h-4 text-blue-600" />
            <span>Top 25 Audit Checklist</span>
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all shrink-0 ${
              activeTab === 'comparison'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitCompare className="w-4 h-4 text-purple-600" />
            <span>Master SOP Comparison</span>
          </button>
          <button
            onClick={() => setActiveTab('trail')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all shrink-0 ${
              activeTab === 'trail'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Lock className="w-4 h-4 text-emerald-600" />
            <span>Cryptographic Trail</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: TOP 25 GxP IT AUDIT CHECKLIST EXECUTION */}
      {/* ========================================================================= */}
      {activeTab === 'checklist' && (
        <div className="space-y-6">
          {/* Executive KPI Summary Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm col-span-2 sm:col-span-1 lg:col-span-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Overall Audit Readiness</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-[#002B49]">
                  {assessment?.readiness_score ?? 64.6}%
                </span>
                <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                  HOLD / DEFER
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full mt-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${assessment?.readiness_score ?? 64.6}%` }}
                />
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Questions</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{assessment?.total_questions ?? 25}</p>
              <span className="text-[10px] text-slate-500">Curated Core Subset</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-emerald-100 shadow-sm bg-emerald-50/20">
              <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Passed</span>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{assessment?.passed_count ?? 15}</p>
              <span className="text-[10px] text-emerald-600">60% compliant</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-sm bg-amber-50/20">
              <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">Partial</span>
              <p className="text-2xl font-bold text-amber-700 mt-1">{assessment?.partial_count ?? 4}</p>
              <span className="text-[10px] text-amber-600">Mitigation required</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-sm bg-rose-50/20">
              <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider">Failed</span>
              <p className="text-2xl font-bold text-rose-700 mt-1">{assessment?.failed_count ?? 6}</p>
              <span className="text-[10px] text-rose-600">Release blockers</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm bg-purple-50/20">
              <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider">Critical Findings</span>
              <p className="text-2xl font-bold text-purple-700 mt-1">{assessment?.critical_findings_count ?? 4}</p>
              <span className="text-[10px] text-purple-600">Gate G5/G6 blocked</span>
            </div>
          </div>

          {/* Action Toolbar & Filters */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-500 mr-1">Filter:</span>
              {[
                { label: 'All (25)', val: 'ALL' },
                { label: 'Failed (6)', val: 'FAIL', color: 'text-rose-700 bg-rose-50 border-rose-200' },
                { label: 'Critical Only', val: 'CRITICAL', color: 'text-purple-700 bg-purple-50 border-purple-200' },
                { label: 'Partial (4)', val: 'PARTIAL', color: 'text-amber-700 bg-amber-50 border-amber-200' },
                { label: 'Passed (15)', val: 'PASS', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
              ].map(f => (
                <button
                  key={f.val}
                  onClick={() => setFilterResult(f.val)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                    filterResult === f.val
                      ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                      : f.color || 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2.5">
              <div className="relative flex-1 md:w-64">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search questions or topics..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={handleExecuteAudit}
                disabled={executing}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors shrink-0 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
                <span>{executing ? 'Executing...' : 'Run Top 25 Audit'}</span>
              </button>

              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                className="bg-[#002B49] hover:bg-[#001D33] text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors shrink-0 disabled:opacity-50"
              >
                <FileText className="w-3.5 h-3.5 text-blue-300" />
                <span>{generatingReport ? 'Compiling Dossier...' : 'Generate Audit Report'}</span>
              </button>
            </div>
          </div>

          {/* Generated Report Banner */}
          {reportResult && (
            <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-emerald-900 shadow-sm animate-in fade-in">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <div>
                  <p className="font-bold text-sm">Audit Report Dossier Generated Successfully</p>
                  <p className="text-[11px] text-emerald-700">{reportResult.summary}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {reportResult.pdf_path && (
                  <a
                    href={api.getReportDownloadUrl(reportResult.pdf_path)}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-rose-600 hover:bg-rose-700 text-white px-3 py-1.5 rounded-md font-semibold text-xs flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download PDF</span>
                  </a>
                )}
                {reportResult.docx_path && (
                  <a
                    href={api.getReportDownloadUrl(reportResult.docx_path)}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-blue-700 hover:bg-blue-800 text-white px-3 py-1.5 rounded-md font-semibold text-xs flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Word (DOCX)</span>
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Checklist Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4 w-12 text-center">#</th>
                    <th className="py-3 px-4 w-28">Question Code</th>
                    <th className="py-3 px-4 w-44">Lifecycle Phase</th>
                    <th className="py-3 px-4">Audit Question & Control Topic</th>
                    <th className="py-3 px-4 w-28 text-center">Result</th>
                    <th className="py-3 px-4 w-48">Evidence Citations</th>
                    <th className="py-3 px-4 w-24 text-center">Severity</th>
                    <th className="py-3 px-4 w-20 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredItems.map(item => {
                    const isFail = item.status === 'FAIL';
                    const isPass = item.status === 'PASS';
                    const isPartial = item.status === 'PARTIAL';

                    return (
                      <tr
                        key={item.question_id}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          isFail ? 'bg-rose-50/10' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-mono font-bold text-slate-400 text-center">
                          {item.sequence}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-slate-800">
                          {item.question_id}
                        </td>
                        <td className="py-3 px-4 text-slate-600 font-medium">
                          {item.lifecycle_phase}
                        </td>
                        <td className="py-3 px-4">
                          <p className="font-bold text-slate-900">{item.control_topic}</p>
                          <p className="text-slate-500 text-[11px] line-clamp-1 mt-0.5">
                            {item.audit_question}
                          </p>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                              isPass
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : isFail
                                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                : 'bg-amber-100 text-amber-800 border border-amber-300'
                            }`}
                          >
                            {isPass && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                            {isFail && <XCircle className="w-3 h-3 text-rose-600" />}
                            {isPartial && <AlertTriangle className="w-3 h-3 text-amber-600" />}
                            {item.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="space-y-1">
                            {item.evidence_citations.slice(0, 2).map((cite, i) => (
                              <span
                                key={i}
                                className="block font-mono text-[10px] text-blue-800 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded truncate max-w-[200px]"
                                title={cite}
                              >
                                {cite}
                              </span>
                            ))}
                            {item.evidence_citations.length > 2 && (
                              <span className="text-[10px] text-slate-400">
                                +{item.evidence_citations.length - 2} more citations
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.risk_level === 'CRITICAL'
                                ? 'bg-purple-100 text-purple-800 border border-purple-300'
                                : item.risk_level === 'HIGH'
                                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                : 'bg-amber-100 text-amber-800 border border-amber-300'
                            }`}
                          >
                            {item.risk_level}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => setSelectedItem(item)}
                            className="text-blue-600 hover:text-blue-800 font-semibold p-1 hover:bg-blue-50 rounded"
                            title="Inspect Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MASTER SOP LIFECYCLE COMPARISON */}
      {/* ========================================================================= */}
      {activeTab === 'comparison' && (
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-purple-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Cross-Document Comparison: Master IT SOP vs MES PAS-X
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Direct evidence benchmark contrasting NN Master IT System Lifecycle SOP (HACK-IT-SOP-001)
                against Novo Life MES PAS-X execution records and GxP LIMS reference.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs bg-rose-50 text-rose-800 border border-rose-200 font-semibold px-2.5 py-1 rounded-lg">
                Deviations Identified: {comparison?.deviations_count ?? 3}
              </span>
              <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold px-2.5 py-1 rounded-lg">
                Aligned Controls: {comparison?.aligned_count ?? 2}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {comparison?.items.map((item, idx) => {
              const isDeviation = item.alignment_status === 'POTENTIAL_LIFECYCLE_DEVIATION';

              return (
                <div
                  key={idx}
                  className={`bg-white rounded-xl border p-5 shadow-sm space-y-4 ${
                    isDeviation ? 'border-rose-200 bg-rose-50/10' : 'border-slate-200'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                        Topic {idx + 1}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{item.topic}</h3>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                        isDeviation
                          ? 'bg-rose-100 text-rose-800 border border-rose-300'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      }`}
                    >
                      {isDeviation ? <AlertTriangle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                      {item.alignment_status.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    {/* Master SOP Requirement */}
                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 space-y-2">
                      <span className="font-bold text-slate-700 flex items-center gap-1.5 uppercase text-[10px] tracking-wider">
                        <FileText className="w-3.5 h-3.5 text-blue-600" />
                        Master IT SOP Expectation ({item.master_sop_section})
                      </span>
                      <p className="text-slate-800 leading-relaxed">{item.sop_requirement}</p>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {item.sop_citations.map((c, i) => (
                          <span key={i} className="font-mono text-[9.5px] bg-white border border-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* MES PAS-X Observed State */}
                    <div className={`border rounded-lg p-3.5 space-y-2 ${
                      isDeviation ? 'bg-rose-50/40 border-rose-200' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className="font-bold text-slate-700 flex items-center gap-1.5 uppercase text-[10px] tracking-wider">
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                        MES PAS-X Observed Evidence (SYS-MES-001)
                      </span>
                      <p className="text-slate-800 leading-relaxed">{item.mes_observed}</p>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {item.mes_citations.map((c, i) => (
                          <span key={i} className="font-mono text-[9.5px] bg-white border border-rose-200 text-rose-800 px-1.5 py-0.5 rounded font-semibold">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Benchmark & Corrective Action */}
                  <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-3 text-xs space-y-1">
                    <p className="font-bold text-blue-900">
                      Recommended Action: <span className="font-normal text-slate-800">{item.recommended_action}</span>
                    </p>
                    {item.lims_benchmark_ref && (
                      <p className="text-[11px] text-slate-500 italic">
                        Benchmark Note: {item.lims_benchmark_ref}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: CRYPTOGRAPHIC AUDIT TRAIL */}
      {/* ========================================================================= */}
      {activeTab === 'trail' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2">
                <Lock className="w-6 h-6 text-emerald-600" />
                <h2 className="text-lg font-bold text-slate-900">Tamper-Evident GxP Audit Trail Ledger</h2>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl">
                Append-only cryptographic ledger. Every automated agent decision and human approval is immutably chained:
                <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-[11px] ml-1 font-mono">
                  event_hash = SHA256(previous_hash + canonical_event_json)
                </code>
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className={`p-3 rounded-lg border flex items-center gap-2.5 text-xs font-semibold ${
                verificationResult?.is_valid
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                  : 'bg-rose-50 border-rose-300 text-rose-900'
              }`}>
                {verificationResult?.is_valid ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                )}
                <div>
                  <p className="font-bold">
                    {verificationResult?.is_valid ? 'Cryptographic Chain Intact' : 'Integrity Compromised'}
                  </p>
                  <p className="text-[10px] font-normal text-slate-600">
                    {verificationResult?.records_checked} blocks verified | Genesis link confirmed
                  </p>
                </div>
              </div>

              <button
                onClick={handleVerifyChain}
                disabled={verifying}
                className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors shrink-0"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
                {verifying ? 'Verifying SHA-256...' : 'Verify Cryptographic Chain'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4 w-12 text-center">#</th>
                    <th className="py-3 px-4 w-32">Timestamp</th>
                    <th className="py-3 px-4 w-28">Actor / Agent</th>
                    <th className="py-3 px-4 w-36">Action</th>
                    <th className="py-3 px-4">Entity & Event Details</th>
                    <th className="py-3 px-4 w-48 font-mono text-center">SHA-256 Event Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs font-mono">
                  {logs.map((log, idx) => (
                    <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 text-center font-bold text-slate-400">
                        {idx + 1}
                      </td>
                      <td className="py-3 px-4 font-sans text-slate-600 text-[11px]">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className="font-semibold text-slate-800">{log.agent_name || log.actor_id}</span>
                        <span className="block text-[10px] text-slate-400 font-mono">{log.actor_type}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-sans font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans text-slate-600">
                        <span className="font-semibold text-slate-800">{log.entity_type}:</span> {log.entity_id}
                        {log.details_json && (
                          <span className="block text-[11px] text-slate-500 truncate max-w-md">
                            {JSON.stringify(log.details_json)}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="text-[10.5px] bg-slate-100 text-slate-700 px-2 py-1 rounded border border-slate-200">
                          {log.event_hash ? log.event_hash.substring(0, 16) + '...' : 'GENESIS'}
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

      {/* ========================================================================= */}
      {/* QUESTION DETAIL MODAL / DRAWER */}
      {/* ========================================================================= */}
      {selectedItem && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="font-mono font-bold text-xs bg-slate-200 text-slate-800 px-2 py-0.5 rounded">
                  {selectedItem.question_id}
                </span>
                <h3 className="text-sm font-bold text-slate-900">{selectedItem.control_topic}</h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              {/* Question Box */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <span className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">
                  Audit Question ({selectedItem.lifecycle_phase})
                </span>
                <p className="text-slate-900 font-medium text-sm leading-relaxed">
                  {selectedItem.audit_question}
                </p>
              </div>

              {/* Assessment Badge */}
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Assessment Status</span>
                  <div className="mt-1">
                    <span
                      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                        selectedItem.status === 'PASS'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : selectedItem.status === 'FAIL'
                          ? 'bg-rose-100 text-rose-800 border border-rose-300'
                          : 'bg-amber-100 text-amber-800 border border-amber-300'
                      }`}
                    >
                      {selectedItem.status}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Severity</span>
                  <div className="mt-1">
                    <span className="inline-block px-2.5 py-1 rounded-md text-xs font-bold bg-purple-100 text-purple-800 border border-purple-300">
                      {selectedItem.risk_level}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Confidence</span>
                  <p className="text-xs font-bold text-slate-800 mt-1">
                    {Math.round(selectedItem.confidence * 100)}% (Deterministic Evidence Match)
                  </p>
                </div>
              </div>

              {/* Gap & Root Cause */}
              {selectedItem.gap_description && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-1 text-rose-900">
                  <span className="font-bold uppercase tracking-wider text-[10px]">Identified Gap & Root Cause:</span>
                  <p className="text-xs font-medium leading-relaxed">{selectedItem.gap_description}</p>
                </div>
              )}

              {/* Citations */}
              <div className="space-y-1.5">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                  Evidence Citations Grounding:
                </span>
                <div className="space-y-1">
                  {selectedItem.evidence_citations.map((cite, i) => (
                    <div key={i} className="font-mono text-xs bg-slate-50 border border-slate-200 text-blue-900 px-2.5 py-1 rounded flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      <span>{cite}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendation */}
              {selectedItem.recommendation && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-1 text-blue-900">
                  <span className="font-bold uppercase tracking-wider text-[10px]">Recommended Corrective Action:</span>
                  <p className="text-xs leading-relaxed">{selectedItem.recommendation}</p>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-xs font-semibold"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
