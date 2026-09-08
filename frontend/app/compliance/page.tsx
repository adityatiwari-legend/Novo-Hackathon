'use client';

import React, { useEffect, useState } from 'react';
import {
  CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Filter,
  Search, ArrowRight, RefreshCw, Layers, FileText, Lock, Eye
} from 'lucide-react';
import { api } from '@/lib/api';
import { ComplianceFinding, TraceabilityResponse, ReleaseGatesResponse } from '@/lib/types';

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<'checks' | 'traceability' | 'gates'>('checks');
  const [loading, setLoading] = useState(true);

  // Tab 1: Compliance
  const [readiness, setReadiness] = useState<any | null>(null);
  const [findings, setFindings] = useState<ComplianceFinding[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Tab 2: Traceability
  const [traceability, setTraceability] = useState<TraceabilityResponse | null>(null);
  const [traceGapOnly, setTraceGapOnly] = useState(false);

  // Tab 3: Release Gates
  const [releaseGates, setReleaseGates] = useState<ReleaseGatesResponse | null>(null);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [rData, fData, tData, gData] = await Promise.all([
        api.getReadiness('SYS-MES-001'),
        api.getFindings('SYS-MES-001'),
        api.getTraceability('SYS-MES-001').catch(() => null),
        api.getReleaseGates('SYS-MES-001').catch(() => null),
      ]);
      setReadiness(rData);
      setFindings(fData);
      setTraceability(tData);
      setReleaseGates(gData);
    } catch (err) {
      console.error('Failed to load compliance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const filteredFindings = findings.filter(f => {
    const matchesSev = filterSeverity === 'ALL' || f.severity?.toUpperCase() === filterSeverity;
    const matchesSearch =
      !searchQuery ||
      f.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (f.description && f.description.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSev && matchesSearch;
  });

  const traceItems = (traceability?.matrix || []).filter(it => !traceGapOnly || it.verification_status !== 'VERIFIED');

  return (
    <div className="space-y-6">
      {/* Header & Tab Switcher */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">
              Regulatory Compliance & Traceability Center
            </h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              SYS-MES-001
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            21 CFR Part 11, EU Annex 11, and GAMP 5 Continuous Verification
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl text-xs font-semibold self-stretch md:self-auto">
          <button
            onClick={() => setActiveTab('checks')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'checks' ? 'bg-white text-slate-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Compliance Checks ({findings.length})
          </button>
          <button
            onClick={() => setActiveTab('traceability')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'traceability' ? 'bg-white text-slate-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Traceability Matrix ({traceability?.total_requirements || 50})
          </button>
          <button
            onClick={() => setActiveTab('gates')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'gates' ? 'bg-white text-slate-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Release Gates (G1–G6)
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: COMPLIANCE CHECKS */}
      {/* ========================================================================= */}
      {activeTab === 'checks' && (
        <div className="space-y-6">
          {/* Top Score Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase font-mono">Readiness Score</span>
              <p className="text-2xl font-black text-slate-900 mt-1 tabular-nums">
                {readiness?.readiness_score ? Math.round(readiness.readiness_score) : 65}%
              </p>
              <span className="text-[10px] text-rose-600 font-bold uppercase">
                {readiness?.release_recommendation || 'HOLD / DEFER'}
              </span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase font-mono">Evaluated Checks</span>
              <p className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">{readiness?.total_checks || 42}</p>
              <span className="text-[10px] text-slate-500">Automated rules</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs bg-emerald-50/20">
              <span className="text-[11px] font-bold text-emerald-700 uppercase font-mono">Passed Rules</span>
              <p className="text-2xl font-bold text-emerald-700 mt-1 tabular-nums">{readiness?.passed_checks || 35}</p>
              <span className="text-[10px] text-emerald-600">83% compliant</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs bg-rose-50/20">
              <span className="text-[11px] font-bold text-rose-700 uppercase font-mono">Active Blockers</span>
              <p className="text-2xl font-bold text-rose-700 mt-1 tabular-nums">{readiness?.failed_checks || 7}</p>
              <span className="text-[10px] text-rose-600 font-semibold">Requires QA authorization</span>
            </div>
          </div>

          {/* Filters & Search */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-500 font-mono">Severity:</span>
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                    filterSeverity === sev
                      ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>

            <div className="relative md:w-72">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search findings, citations, rules..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Findings Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredFindings.map(f => {
              const isCrit = f.severity?.toUpperCase() === 'CRITICAL';
              const isHigh = f.severity?.toUpperCase() === 'HIGH';

              return (
                <div
                  key={f.id}
                  className={`bg-white rounded-2xl border p-5 shadow-xs flex flex-col justify-between space-y-3 transition-all ${
                    isCrit
                      ? 'border-purple-200 hover:border-purple-300 bg-purple-50/10'
                      : isHigh
                      ? 'border-rose-200 hover:border-rose-300 bg-rose-50/10'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[9.5px] font-bold px-2 py-0.5 rounded font-mono ${
                            isCrit
                              ? 'bg-purple-100 text-purple-800'
                              : isHigh
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {f.severity}
                        </span>
                        <span className="font-mono text-xs font-bold text-slate-900">{f.id}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">
                        {f.title || '21 CFR Part 11'}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-900 leading-relaxed">
                      {f.description || f.title}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span className="font-mono text-[10px] text-blue-800 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded truncate max-w-xs">
                      {f.source_citations?.[0]?.document ? String(f.source_citations[0].document) : 'NL-MES-ITPSE-001'}
                    </span>
                    <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                      Release Blocker
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: BIDIRECTIONAL TRACEABILITY MATRIX */}
      {/* ========================================================================= */}
      {activeTab === 'traceability' && (
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Bidirectional Traceability Matrix (URS ↔ Spec ↔ Risk ↔ Test ↔ Release)
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Continuous verification of {traceability?.total_requirements || 50} lifecycle requirements for Novo Life MES PAS-X (GAMP Category 4)
              </p>
            </div>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={traceGapOnly}
                  onChange={e => setTraceGapOnly(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Show Gaps Only ({traceability?.gaps_count || 9})</span>
              </label>

              <div className="text-xs font-mono font-bold bg-blue-50 text-blue-800 border border-blue-200 px-3 py-1 rounded-lg">
                Verified: {traceability?.verified_count || 41}/{traceability?.total_requirements || 50}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                    <th className="py-3 px-4 w-32">URS ID</th>
                    <th className="py-3 px-4">Requirement Specification</th>
                    <th className="py-3 px-4 w-28">Module</th>
                    <th className="py-3 px-4 w-36">Risk Mapping</th>
                    <th className="py-3 px-4 w-40">Test Case / Script</th>
                    <th className="py-3 px-4 w-32 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {traceItems.map((it, idx) => {
                    const isVerified = it.verification_status === 'VERIFIED';
                    return (
                      <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-slate-800">
                          {it.requirement_id}
                        </td>
                        <td className="py-3 px-4 text-slate-800">
                          <p className="font-semibold">{it.requirement_text}</p>
                          <p className="text-[11px] text-slate-500 mt-0.5">{it.type}</p>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-600">
                          {it.fs_module || 'Cat 4'}
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-purple-700">
                          {it.risk_id} ({it.risk_level})
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          {it.verification_id || (
                            <span className="text-rose-600 font-bold">MISSING EXECUTION</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-bold ${
                              isVerified
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-rose-100 text-rose-800 border border-rose-300'
                            }`}
                          >
                            {it.verification_status}
                          </span>
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
      {/* TAB 3: RELEASE GATES (G1 to G6) */}
      {/* ========================================================================= */}
      {activeTab === 'gates' && (
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <h2 className="text-base font-bold text-slate-900">
              Deterministic GxP Release Gate Architecture (G1–G6)
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Deterministic gates prevent premature production activation. Gate G5 (Release Readiness)
              is actively enforced as BLOCKED until residual risk rating and operational handover are satisfied.
            </p>
          </div>

          <div className="space-y-4">
            {releaseGates?.gates?.map((g) => {
              const isMet = g.status === 'MET';
              const isBlocked = g.status === 'BLOCKED';

              return (
                <div
                  key={g.gate_code}
                  className={`bg-white rounded-2xl border p-5 shadow-xs space-y-3 ${
                    isBlocked
                      ? 'border-rose-300 bg-rose-50/15'
                      : isMet
                      ? 'border-emerald-200 bg-emerald-50/10'
                      : 'border-slate-200'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                        {g.gate_code}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{g.gate_name}</h3>
                    </div>
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded font-mono ${
                        isMet
                          ? 'bg-emerald-100 text-emerald-800'
                          : isBlocked
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {g.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed font-medium">
                    Evidence: {g.evidence_doc || 'GAMP Category 4 Lifecycle Verification'} {g.evidence_section ? `(${g.evidence_section})` : ''}
                  </p>

                  {g.blocking_reason && (
                    <div className="bg-rose-50 border border-rose-200 p-3 rounded-xl text-xs space-y-1">
                      <span className="text-[10px] font-bold text-rose-800 uppercase font-mono block">
                        Identified Gate Blocker:
                      </span>
                      <p className="text-rose-950 font-semibold">{g.blocking_reason}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
