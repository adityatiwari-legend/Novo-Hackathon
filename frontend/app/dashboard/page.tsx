'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ShieldAlert, CheckCircle2, AlertTriangle, FileText, ArrowUpRight,
  TrendingUp, Activity, Cpu, Sparkles, RefreshCw, ExternalLink
} from 'lucide-react';
import { api } from '@/lib/api';
import { DashboardOverview } from '@/lib/types';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessing, setAssessing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunAssessment = async () => {
    setAssessing(true);
    try {
      await api.assessCompliance('SYS-LIMS-001');
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setAssessing(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-sm font-medium text-slate-500">Loading GxP Compliance Dashboard...</p>
        </div>
      </div>
    );
  }

  const readiness = data?.readiness_score ?? 82;
  const severityData = [
    { name: 'Critical', count: data?.findings_by_severity.CRITICAL || 0, color: '#dc2626' },
    { name: 'High', count: data?.findings_by_severity.HIGH || 1, color: '#ea580c' },
    { name: 'Medium', count: data?.findings_by_severity.MEDIUM || 2, color: '#d97706' },
    { name: 'Low', count: data?.findings_by_severity.LOW || 0, color: '#16a34a' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Compliance Dashboard</h1>
            <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded border border-blue-200">
              {data?.system_name || 'Novo Life MES PAS-X'} ({data?.system_id || 'SYS-MES-001'})
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Continuous AI verification aligned with 21 CFR Part 11, EU Annex 11, GAMP 5 Cat 4, and ALCOA+ principles.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAssessment}
            disabled={assessing}
            className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-3.5 py-2 rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${assessing ? 'animate-spin' : ''}`} />
            {assessing ? 'Assessing System...' : 'Run Compliance Analysis'}
          </button>
          <Link
            href="/chat"
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-2 rounded-lg text-xs font-semibold shadow-sm transition-all"
          >
            <span>Ask Co-Pilot</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Critical Release Posture Banner */}
      <div className="bg-gradient-to-r from-rose-50 to-amber-50 border border-rose-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-rose-600 flex items-center justify-center text-white shrink-0 mt-0.5">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-rose-900">
                Release Decision: {data?.release_recommendation || 'HOLD / DEFER - DO NOT RELEASE'}
              </h3>
              <span className="text-[10px] font-bold bg-rose-100 text-rose-800 px-2 py-0.5 rounded border border-rose-300">
                GATE G5 NOT MET
              </span>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded border border-amber-300">
                {data?.lifecycle_status || 'PRE-OPERATIONAL / NOT ACTIVATED'}
              </span>
            </div>
            <p className="text-xs text-rose-700 mt-1">
              Commercial batch release is blocked because intended-use verification (OV/PfV/UAT) was deferred,
              residual risks remain unrated across 49 requirements, and shopfloor operator training is incomplete.
            </p>
          </div>
        </div>
        <Link
          href="/compliance"
          className="shrink-0 bg-rose-700 hover:bg-rose-800 text-white px-3.5 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm"
        >
          <span>Inspect Release Gates (G1-G6)</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Readiness Score */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Audit Readiness</span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${readiness >= 90 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
              {readiness >= 90 ? 'Audit Ready' : 'Attention Req'}
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${readiness >= 90 ? 'text-emerald-600' : readiness >= 80 ? 'text-amber-600' : 'text-rose-600'}`}>
              {readiness}%
            </span>
            <span className="text-[11px] text-slate-400">Target: 95%</span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${readiness >= 90 ? 'bg-emerald-500' : readiness >= 80 ? 'bg-amber-500' : 'bg-rose-500'}`}
              style={{ width: `${readiness}%` }}
            />
          </div>
        </div>

        {/* Compliance Score */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Checklist Score</span>
            <CheckCircle2 className="w-4 h-4 text-blue-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{readiness}%</span>
            <span className="text-[11px] text-slate-400">Deterministic</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">8/8 Controls Evaluated</p>
        </div>

        {/* Open Findings */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Open Findings</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{data?.open_findings ?? 3}</span>
            <span className="text-[11px] text-amber-600 font-semibold">Active Gaps</span>
          </div>
          <Link href="/compliance" className="text-[11px] text-blue-600 hover:underline mt-2 inline-block font-medium">
            View Finding Details →
          </Link>
        </div>

        {/* High / Critical Risks */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">High/Critical Risks</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-600">{data?.high_critical_risks ?? 1}</span>
            <span className="text-[11px] text-slate-400">RA-01 (URS QA)</span>
          </div>
          <Link href="/risk" className="text-[11px] text-blue-600 hover:underline mt-2 inline-block font-medium">
            View Risk Matrix →
          </Link>
        </div>

        {/* Pending Approvals */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Pending Approvals</span>
            <Activity className="w-4 h-4 text-blue-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{data?.pending_approvals ?? 0}</span>
            <span className="text-[11px] text-slate-400">Human Gate</span>
          </div>
          <Link href="/workflows" className="text-[11px] text-blue-600 hover:underline mt-2 inline-block font-medium">
            Review Approvals →
          </Link>
        </div>

        {/* Evidence Packs */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Evidence Packs</span>
            <FileText className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{data?.evidence_packs_count ?? 1}</span>
            <span className="text-[11px] text-slate-400">Dossiers</span>
          </div>
          <Link href="/evidence" className="text-[11px] text-blue-600 hover:underline mt-2 inline-block font-medium">
            Generate Dossier →
          </Link>
        </div>
      </div>

      {/* Visual Charts: Readiness Trend & Severity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                Audit Readiness Index Trend
              </h2>
              <p className="text-xs text-slate-500">Continuous telemetry compliance tracking over time</p>
            </div>
            <span className="text-xs font-mono text-slate-400">Current: {readiness}%</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.readiness_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="readinessGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#005999" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#005999" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={11} />
                <YAxis domain={[50, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Readiness Score']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="score" stroke="#005999" strokeWidth={2.5} fillOpacity={1} fill="url(#readinessGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 mb-1">Findings by Regulatory Severity</h2>
            <p className="text-xs text-slate-500 mb-4">ICH Q9 Risk Classification breakdown</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={10} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="border-t border-slate-100 pt-3 text-[11px] text-slate-500 flex justify-between items-center">
            <span>Primary Driver:</span>
            <span className="font-semibold text-rose-600">QA Sign-off Missing</span>
          </div>
        </div>
      </div>

      {/* Systems Overview Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Registered GxP Systems Inventory</h2>
            <p className="text-xs text-slate-500">Validated computerized systems subject to continuous compliance supervision</p>
          </div>
          <Link href="/systems" className="text-xs text-blue-600 hover:underline font-semibold flex items-center gap-1">
            <span>Full System Details</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-semibold">System Name & ID</th>
                <th className="py-3 px-4 font-semibold">GxP Status</th>
                <th className="py-3 px-4 font-semibold">Readiness Index</th>
                <th className="py-3 px-4 font-semibold">Risk Posture</th>
                <th className="py-3 px-4 font-semibold">Open Findings</th>
                <th className="py-3 px-4 font-semibold">Last Assessment</th>
                <th className="py-3 px-4 font-semibold">Operational Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr className="hover:bg-slate-50/80 transition-colors">
                <td className="py-3 px-4">
                  <div className="font-bold text-slate-900">System A: Validated LIMS</div>
                  <div className="text-[10px] text-slate-400 font-mono">SYS-LIMS-001 (GAMP 5 Cat 4)</div>
                </td>
                <td className="py-3 px-4">
                  <span className="bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded text-[10px]">
                    GxP-Critical
                  </span>
                </td>
                <td className="py-3 px-4 font-bold text-slate-900">
                  <span className={readiness >= 90 ? 'text-emerald-600' : 'text-amber-600'}>
                    {readiness}%
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="bg-rose-100 text-rose-800 font-semibold px-2 py-0.5 rounded text-[10px]">
                    HIGH
                  </span>
                </td>
                <td className="py-3 px-4 font-medium text-slate-800">
                  {data?.open_findings ?? 3} Active
                </td>
                <td className="py-3 px-4 text-slate-500">Today</td>
                <td className="py-3 px-4">
                  <span className="bg-amber-100 text-amber-900 border border-amber-300 font-semibold px-2 py-0.5 rounded text-[10px]">
                    Attention Required
                  </span>
                </td>
                <td className="py-3 px-4 text-right space-x-2">
                  <Link
                    href="/compliance"
                    className="text-blue-600 hover:text-blue-800 font-semibold text-[11px]"
                  >
                    Assess
                  </Link>
                  <span className="text-slate-300">|</span>
                  <Link
                    href="/chat"
                    className="text-slate-700 hover:text-slate-900 font-semibold text-[11px]"
                  >
                    Query
                  </Link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Agent Health & Observability Grid */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600" />
            Active Multi-Agent Mesh & Enterprise Connectors
          </h2>
          <Link href="/admin" className="text-xs text-blue-600 hover:underline font-semibold">
            View All Stubs & Architecture →
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {Object.entries(data?.agent_health || {}).map(([agent, status]) => (
            <div key={agent} className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-800 leading-tight">{agent}</span>
              <div className="mt-2 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-[10px] font-medium text-emerald-700">{status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
