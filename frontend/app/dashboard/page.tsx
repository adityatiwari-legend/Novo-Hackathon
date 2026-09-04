'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2, Clock,
  FileCheck, ArrowRight, RefreshCw, Cpu, Layers, Sparkles,
  ChevronRight, ExternalLink, Filter, HelpCircle, Activity, Lock
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import { api } from '@/lib/api';
import { DashboardOverview, ReleaseGatesResponse, ComplianceFinding } from '@/lib/types';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [releaseGates, setReleaseGates] = useState<ReleaseGatesResponse | null>(null);
  const [findings, setFindings] = useState<ComplianceFinding[]>([]);
  const [selectedGate, setSelectedGate] = useState<any | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadAll = async () => {
    try {
      setRefreshing(true);
      const [dash, gates, fList] = await Promise.all([
        api.getDashboard(),
        api.getReleaseGates('SYS-MES-001').catch(() => null),
        api.getFindings('SYS-MES-001').catch(() => [])
      ]);
      setData(dash);
      setReleaseGates(gates);
      setFindings(fList);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-3">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-xs font-semibold text-slate-500 font-mono">
          Evaluating GxP IT system telemetry & release gates...
        </p>
      </div>
    );
  }

  const score = data?.readiness_score ?? 64.6;
  const isHold = data?.release_recommendation?.includes('HOLD') || score < 95;
  const filteredFindings = findings.filter(f =>
    severityFilter === 'ALL' || f.severity?.toUpperCase() === severityFilter
  );

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <span>Validated Systems</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-800 font-semibold font-mono">SYS-MES-001</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-blue-700 font-semibold">Continuous Assurance Dashboard</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">
            {data?.system_name || 'Novo Life MES PAS-X'}
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadAll}
            disabled={refreshing}
            className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
            <span>{refreshing ? 'Evaluating...' : 'Refresh Telemetry'}</span>
          </button>

          <Link
            href="/audit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Top 25 Audit Checklist</span>
          </Link>
        </div>
      </div>

      {/* Hero Section: Executive Readiness & Posture Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
          {/* Readiness Score Dial (Left 4 cols) */}
          <div className="lg:col-span-4 p-6 flex flex-col justify-between bg-gradient-to-b from-slate-50/70 to-white">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                  Overall Release Readiness
                </span>
                <span className="text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
                  ALCOA+ Grounded
                </span>
              </div>

              {/* Radial Dial Simulation */}
              <div className="mt-4 flex items-center gap-4">
                <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-100"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={score >= 80 ? 'text-amber-500' : 'text-rose-600'}
                      strokeDasharray={`${score}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-2xl font-black text-slate-900 tabular-nums leading-none">
                      {Math.round(score)}%
                    </span>
                    <span className="text-[9px] text-slate-400 font-mono mt-0.5">SCORE</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-rose-700 uppercase tracking-wide">
                      {data?.release_recommendation || 'HOLD / DEFER - DO NOT RELEASE'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    Deterministic gate G5 blocks production release until residual risks and verification gaps are resolved.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
              <span>Lifecycle: <b className="text-slate-700">{data?.lifecycle_status || 'PRE-OPERATIONAL'}</b></span>
              <span className="font-mono text-[10px]">Conf: 95%</span>
            </div>
          </div>

          {/* Release Posture & Primary Blockers (Right 8 cols) */}
          <div className="lg:col-span-8 p-6 flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                  Primary Release Blocker Analysis
                </span>
                <span className="text-xs text-rose-700 bg-rose-50 border border-rose-200 font-semibold px-2 py-0.5 rounded">
                  4 Critical Gate Findings
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-rose-50/50 border border-rose-200/80 rounded-xl p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    <span>Gate G5 Blocked</span>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-snug">
                    Release Readiness gate failed due to incomplete operational handover and unmitigated high risks.
                  </p>
                </div>

                <div className="bg-amber-50/50 border border-amber-200/80 rounded-xl p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs">
                    <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>Verification Gaps</span>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-snug">
                    9 of 50 URS requirements lack direct test script execution records in PAS-X qualification package.
                  </p>
                </div>

                <div className="bg-purple-50/50 border border-purple-200/80 rounded-xl p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-purple-800 font-bold text-xs">
                    <ShieldAlert className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                    <span>Residual Risks Open</span>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-snug">
                    25 high working risks in ICH Q9 register require verified mitigation before Gate G6 approval.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Requirements</span>
                <span className="text-lg font-bold text-slate-900 tabular-nums">50 Traced</span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Hazards Evaluated</span>
                <span className="text-lg font-bold text-slate-900 tabular-nums">26 Risks</span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                <span className="text-[10px] uppercase font-bold text-rose-600 font-mono block">Open Findings</span>
                <span className="text-lg font-bold text-rose-700 tabular-nums">{data?.open_findings ?? 7} Blockers</span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Pending QA</span>
                <span className="text-lg font-bold text-amber-600 tabular-nums">{data?.pending_approvals ?? 1} Approvals</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Horizontal Interactive Release Gates Pipeline (G1 to G6) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Deterministic GxP Release Gates Pipeline (G1–G6)
            </h2>
          </div>
          <span className="text-xs text-slate-500">Click any gate to inspect validation criteria & evidence</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {releaseGates?.gates && releaseGates.gates.length > 0 ? (
            releaseGates.gates.map((g) => {
              const isMet = g.status === 'MET';
              const isBlocked = g.status === 'BLOCKED';
              const isPending = g.status === 'PENDING';

              return (
                <div
                  key={g.gate_code}
                  onClick={() => setSelectedGate(g)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer text-xs flex flex-col justify-between space-y-2 ${
                    isMet
                      ? 'bg-emerald-50/50 border-emerald-200 hover:border-emerald-300'
                      : isBlocked
                      ? 'bg-rose-50/70 border-rose-300 hover:border-rose-400 shadow-xs'
                      : 'bg-slate-50 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-[11px] text-slate-700">{g.gate_code}</span>
                    <span
                      className={`text-[9.5px] font-bold px-1.5 py-0.2 rounded font-mono ${
                        isMet
                          ? 'bg-emerald-100 text-emerald-800'
                          : isBlocked
                          ? 'bg-rose-100 text-rose-800 animate-pulse'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {g.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-900 text-xs truncate" title={g.gate_name}>
                      {g.gate_name}
                    </h3>
                    <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">
                      {g.blocking_reason || (g.evidence_doc ? `Evidence: ${g.evidence_doc}` : 'GAMP 5 Gate Verification')}
                    </p>
                  </div>

                  <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-[9.5px] text-slate-400">
                    <span>Inspect</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                  </div>
                </div>
              );
            })
          ) : (
            ['G1: Requirement Baseline', 'G2: Traceability Completeness', 'G3: Verification Evidence', 'G4: Deviation Resolution', 'G5: Release Readiness', 'G6: Operational Activation'].map((name, i) => (
              <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs">
                <span className="font-mono font-bold text-[11px] text-slate-600 block">G{i + 1}</span>
                <span className="font-semibold text-slate-800 text-[11px]">{name}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Two-Column Workspace: Critical Release Blockers & AI Multi-Agent Mesh */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Critical Release Blockers Table (Left 7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between overflow-hidden">
          <div>
            <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Release Blockers & Compliance Findings ({findings.length})
                </h2>
                <p className="text-xs text-slate-500">Grounded against 21 CFR Part 11 and EU Annex 11</p>
              </div>

              {/* Severity Filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setSeverityFilter(sev)}
                    className={`px-2 py-0.5 rounded text-[10.5px] font-bold transition-all ${
                      severityFilter === sev
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>

            <div className="divide-y divide-slate-100 max-h-[480px] overflow-y-auto">
              {filteredFindings.map((f) => {
                const isCrit = f.severity?.toUpperCase() === 'CRITICAL';
                const isHigh = f.severity?.toUpperCase() === 'HIGH';

                return (
                  <div key={f.id} className="p-4 hover:bg-slate-50/80 transition-colors space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[9.5px] font-bold px-2 py-0.5 rounded font-mono ${
                            isCrit
                              ? 'bg-purple-100 text-purple-800 border border-purple-200'
                              : isHigh
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}
                        >
                          {f.severity}
                        </span>
                        <span className="font-mono text-xs font-bold text-slate-800">{f.id}</span>
                      </div>
                      <span className="text-[10.5px] text-slate-400 font-mono">
                        {f.title || '21 CFR Part 11'}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-900 leading-snug">
                      {f.description || f.title}
                    </p>

                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs pt-1">
                      <span className="font-mono text-[10px] text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded truncate max-w-xs">
                        {f.source_citations?.[0]?.document ? String(f.source_citations[0].document) : 'NL-MES-ITPSE-001'}
                      </span>
                      <Link
                        href="/compliance"
                        className="text-blue-600 hover:text-blue-800 font-semibold text-xs flex items-center gap-1 transition-colors"
                      >
                        <span>Remediate in Checklist</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {filteredFindings.length} findings</span>
            <Link href="/compliance" className="text-blue-600 font-semibold hover:underline">
              View All Compliance Rules →
            </Link>
          </div>
        </div>

        {/* Right 5 cols: Readiness Trend Chart & AI Telemetry */}
        <div className="lg:col-span-5 space-y-6">
          {/* Historical Readiness Trend */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Assurance Readiness Trajectory</h2>
                <p className="text-xs text-slate-500">Continuous evaluation telemetry trend</p>
              </div>
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                +14.6% Trend
              </span>
            </div>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.readiness_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      color: '#FFF',
                      borderRadius: '8px',
                      fontSize: '11px',
                      border: 'none',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#2563EB"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#scoreGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Multi-Agent Mesh Telemetry */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-600" />
                <h3 className="text-sm font-bold text-slate-900">Multi-Agent Assurance Mesh Status</h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                OPERATIONAL
              </span>
            </div>

            <div className="space-y-2 text-xs">
              {[
                { name: 'Compliance Engine', status: 'Evaluated 42 Rules', state: 'Passed', icon: ShieldCheck },
                { name: 'Traceability Agent', status: '50 Requirements Traced', state: 'Active', icon: Layers },
                { name: 'Risk Agent', status: 'ICH Q9 Matrix Evaluated', state: 'Active', icon: AlertTriangle },
                { name: 'Release Gate Engine', status: 'G1–G6 Evaluated (G5 Blocked)', state: 'Enforced', icon: Lock },
                { name: 'Evidence Agent', status: 'PDF/DOCX Dossier Ready', state: 'Ready', icon: FileCheck },
              ].map((agent, i) => {
                const Icon = agent.icon;
                return (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2">
                      <Icon className="w-3.5 h-3.5 text-blue-600" />
                      <div>
                        <span className="font-semibold text-slate-800 text-xs block">{agent.name}</span>
                        <span className="text-[10px] text-slate-400">{agent.status}</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/60 px-2 py-0.5 rounded font-mono">
                      {agent.state}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Release Gate Detail Modal */}
      {selectedGate && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                  {selectedGate.gate_code}
                </span>
                <h3 className="text-base font-bold text-slate-900">{selectedGate.gate_name}</h3>
              </div>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded font-mono ${
                  selectedGate.status === 'MET'
                    ? 'bg-emerald-100 text-emerald-800'
                    : selectedGate.status === 'BLOCKED'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-slate-100 text-slate-700'
                }`}
              >
                {selectedGate.status}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Evidence Reference</span>
                <p className="text-slate-800 mt-1 font-medium bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  {selectedGate.evidence_doc || 'GAMP Category 4 Lifecycle Verification'} {selectedGate.evidence_section ? `(${selectedGate.evidence_section})` : ''}
                </p>
              </div>

              {selectedGate.blocking_reason && (
                <div className="bg-rose-50 border border-rose-200 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold uppercase text-rose-800 block">Identified Blocker:</span>
                  <p className="text-rose-900 leading-snug">{selectedGate.blocking_reason}</p>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
              <button
                onClick={() => setSelectedGate(null)}
                className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-xs font-semibold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
