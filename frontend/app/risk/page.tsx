'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ShieldAlert, AlertTriangle, CheckCircle2, FileText, ArrowRight,
  Sparkles, RefreshCw, Shield, ChevronDown, ChevronRight
} from 'lucide-react';
import { api } from '@/lib/api';
import { Risk } from '@/lib/types';

export default function RiskPage() {
  const [risks, setRisks] = useState<Risk[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);

  useEffect(() => {
    api.getRisks('SYS-LIMS-001')
      .then(res => {
        setRisks(res);
        if (res.length > 0) setSelectedRisk(res[0]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  const highCount = risks.filter(r => r.risk_level === 'HIGH' || r.risk_level === 'CRITICAL').length;
  const medCount = risks.filter(r => r.risk_level === 'MEDIUM').length;
  const lowCount = risks.filter(r => r.risk_level === 'LOW').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">GxP IT Risk Assessment Register</h1>
          <p className="text-xs text-slate-500 mt-1">
            ICH Q9 Quality Risk Management matrix evaluating GxP patient safety, data integrity, and operational impact.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-1 rounded">
            {highCount} High Risk
          </span>
          <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded">
            {medCount} Moderate
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Register Table (Left 2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200">
            <h2 className="text-sm font-bold text-slate-900">Active Hazards & Risk Matrix</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 font-semibold">Hazard / Finding</th>
                  <th className="py-3 px-4 font-semibold">Risk Level</th>
                  <th className="py-3 px-4 font-semibold">Impact Type</th>
                  <th className="py-3 px-4 font-semibold">Score</th>
                  <th className="py-3 px-4 font-semibold text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {risks.map((r) => {
                  const isSelected = selectedRisk?.id === r.id;
                  return (
                    <tr
                      key={r.id}
                      onClick={() => setSelectedRisk(r)}
                      className={`cursor-pointer transition-colors ${isSelected ? 'bg-blue-50/60 font-semibold' : 'hover:bg-slate-50/70'}`}
                    >
                      <td className="py-3 px-4">
                        <div className="text-slate-900 font-medium">{r.rationale.slice(0, 50)}...</div>
                        <div className="text-[10px] text-slate-400 font-mono">Control: {r.control_mapping || 'ICH Q9'}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.risk_level === 'HIGH'
                            ? 'bg-rose-100 text-rose-800'
                            : r.risk_level === 'MEDIUM'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {r.risk_level}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{r.impact_type}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">{r.score} / 25</td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-blue-600 text-xs font-semibold">Inspect →</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Risk Inspection Card (Right 1 Col) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Hazard Breakdown</span>
            {selectedRisk && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                selectedRisk.risk_level === 'HIGH' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {selectedRisk.risk_level} IMPACT
              </span>
            )}
          </div>

          {selectedRisk ? (
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">GxP Risk Rationale:</span>
                <p className="text-slate-800 mt-1 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                  {selectedRisk.rationale}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Likelihood</span>
                  <span className="font-bold text-slate-800 text-xs">{selectedRisk.likelihood}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Impact</span>
                  <span className="font-bold text-slate-800 text-xs">{selectedRisk.impact}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Matrix Score</span>
                  <span className="font-bold text-rose-600 text-xs">{selectedRisk.score}/25</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">Regulatory Control Standard:</span>
                <p className="text-slate-700 mt-1 font-mono text-[11px] bg-slate-50 p-2 rounded border border-slate-200">
                  {selectedRisk.control_mapping || 'ICH Q9 Quality Risk Management'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <Link
                  href="/compliance"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span>Remediate in Compliance Screen</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 text-center py-8">Select a risk to inspect details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
