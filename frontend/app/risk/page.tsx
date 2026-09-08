'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertOctagon, AlertTriangle, ShieldCheck, ShieldAlert,
  Filter, Search, ArrowRight, RefreshCw, CheckCircle2,
  FileText, ExternalLink, HelpCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import { Risk } from '@/lib/types';

export default function RiskPage() {
  const [risks, setRisks] = useState<Risk[]>([]);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const loadRisks = async () => {
    try {
      setLoading(true);
      const data = await api.getRisks('SYS-MES-001');
      setRisks(data);
      if (data.length > 0) setSelectedRisk(data[0]);
    } catch (err) {
      console.error('Failed to load risks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRisks();
  }, []);

  const filteredRisks = risks.filter(r => {
    const matchesSev = filterSeverity === 'ALL' || r.risk_level?.toUpperCase() === filterSeverity;
    const matchesSearch =
      !searchQuery ||
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.impact_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.rationale && r.rationale.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSev && matchesSearch;
  });

  const highCount = risks.filter(r => r.risk_level?.toUpperCase() === 'HIGH' || r.risk_level?.toUpperCase() === 'CRITICAL').length;
  const medCount = risks.filter(r => r.risk_level?.toUpperCase() === 'MEDIUM').length;
  const lowCount = risks.filter(r => r.risk_level?.toUpperCase() === 'LOW').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-600" />
            <h1 className="text-lg font-bold text-slate-900">
              ICH Q9 Quality Risk Management Register
            </h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              SYS-MES-001
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Hazard evaluation and residual risk assessment for Novo Life MES PAS-X (GAMP Category 4)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadRisks}
            disabled={loading}
            className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Reload Hazards</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase font-mono">Total Hazards</span>
          <p className="text-2xl font-black text-slate-900 mt-1 tabular-nums">{risks.length}</p>
          <span className="text-[10px] text-slate-500">ICH Q9 cataloged</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-rose-200 shadow-xs bg-rose-50/20">
          <span className="text-[11px] font-bold text-rose-700 uppercase font-mono">High / Critical</span>
          <p className="text-2xl font-bold text-rose-700 mt-1 tabular-nums">{highCount}</p>
          <span className="text-[10px] text-rose-600 font-semibold">Requires formal verification</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-xs bg-amber-50/20">
          <span className="text-[11px] font-bold text-amber-700 uppercase font-mono">Medium Hazards</span>
          <p className="text-2xl font-bold text-amber-700 mt-1 tabular-nums">{medCount}</p>
          <span className="text-[10px] text-amber-600">SOP control mapped</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-emerald-200 shadow-xs bg-emerald-50/20">
          <span className="text-[11px] font-bold text-emerald-700 uppercase font-mono">Low Hazards</span>
          <p className="text-2xl font-bold text-emerald-700 mt-1 tabular-nums">{lowCount}</p>
          <span className="text-[10px] text-emerald-600">Acceptable residual risk</span>
        </div>
      </div>

      {/* Split View: Hazard Register Table & Deep-Dive Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 cols: Hazard List */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between overflow-hidden">
          <div>
            <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
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

              <div className="relative sm:w-60">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter hazards..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="divide-y divide-slate-100 max-h-[560px] overflow-y-auto">
              {filteredRisks.map(r => {
                const isSelected = selectedRisk?.id === r.id;
                const isHigh = r.risk_level?.toUpperCase() === 'HIGH' || r.risk_level?.toUpperCase() === 'CRITICAL';

                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRisk(r)}
                    className={`p-4 cursor-pointer transition-all space-y-1.5 ${
                      isSelected
                        ? 'bg-blue-50/70 border-l-4 border-blue-600'
                        : 'hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[9.5px] font-bold px-2 py-0.5 rounded font-mono ${
                            isHigh
                              ? 'bg-rose-100 text-rose-800 border border-rose-300'
                              : 'bg-amber-100 text-amber-800 border border-amber-300'
                          }`}
                        >
                          {r.risk_level}
                        </span>
                        <span className="font-mono text-xs font-bold text-slate-800">{r.id}</span>
                      </div>
                      <span className="text-[10.5px] font-mono text-slate-400">
                        Score: <b className="text-slate-800">{r.score || 16}/25</b>
                      </span>
                    </div>

                    <h3 className="text-xs font-bold text-slate-900 leading-snug">{r.impact_type || 'Hazard Scenario'}</h3>
                    <p className="text-[11px] text-slate-500 line-clamp-1">{r.rationale}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
            Showing {filteredRisks.length} of {risks.length} recorded hazards
          </div>
        </div>

        {/* Right 5 cols: Hazard Deep-Dive Inspector */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
          {selectedRisk ? (
            <>
              <div className="border-b border-slate-100 pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                    {selectedRisk.id}
                  </span>
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded font-mono ${
                      selectedRisk.risk_level?.toUpperCase() === 'HIGH' || selectedRisk.risk_level?.toUpperCase() === 'CRITICAL'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {selectedRisk.risk_level} RISK
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 leading-tight">
                  {selectedRisk.impact_type || 'System Hazard Assessment'}
                </h2>
              </div>

              {/* 5x5 Matrix Assessment */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
                <span className="text-[10.5px] font-bold uppercase tracking-wider text-slate-500 font-mono block">
                  ICH Q9 Matrix Rating
                </span>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-white p-2 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 font-mono block">LIKELIHOOD</span>
                    <span className="text-xs font-bold text-slate-800">
                      {selectedRisk.likelihood || 'Possible (3/5)'}
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 font-mono block">SEVERITY</span>
                    <span className="text-xs font-bold text-slate-800">
                      {selectedRisk.impact || 'Critical (4/5)'}
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 font-mono block">RPN SCORE</span>
                    <span className="text-xs font-black text-rose-700 tabular-nums">
                      {selectedRisk.score || 16}/25
                    </span>
                  </div>
                </div>
              </div>

              {/* Rationale */}
              <div className="space-y-1 text-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono block">
                  Failure Mode & Clinical Impact:
                </span>
                <p className="text-slate-800 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200">
                  {selectedRisk.rationale}
                </p>
              </div>

              {/* Mitigations */}
              {selectedRisk.control_mapping && (
                <div className="space-y-1 text-xs">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono block">
                    Established Regulatory Control & Mitigation:
                  </span>
                  <div className="bg-emerald-50/60 border border-emerald-200 p-3.5 rounded-xl text-emerald-950 space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mitigation Strategy</span>
                    </div>
                    <p className="text-xs leading-relaxed">{selectedRisk.control_mapping}</p>
                  </div>
                </div>
              )}

              {/* Release Blocker Note */}
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block">Gate G5 Hold Condition:</span>
                  <p className="text-[11px] text-rose-800">
                    Residual risk ratings must be signed off by QA_COMPLIANCE before Gate G6 Operational Activation.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="h-96 flex flex-col items-center justify-center text-center text-slate-400 space-y-2">
              <AlertOctagon className="w-8 h-8 text-slate-300" />
              <p className="text-xs font-semibold text-slate-600">No Hazard Selected</p>
              <p className="text-[11px] text-slate-400">Select any hazard on the left to inspect its ICH Q9 matrix assessment.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
