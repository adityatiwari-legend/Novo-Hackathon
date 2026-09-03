'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Server, ShieldCheck, ArrowRight, RefreshCw, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import { System } from '@/lib/types';

export default function SystemsPage() {
  const [systems, setSystems] = useState<System[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSystems()
      .then(setSystems)
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

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Validated GxP IT Systems Registry</h1>
          <p className="text-xs text-slate-500 mt-1">
            Enterprise computerized systems categorized by GAMP 5 classification and GxP criticality.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {systems.map((s) => (
          <div key={s.id} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4 hover:border-blue-300 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">{s.name}</h2>
                  <span className="text-xs font-mono text-slate-400">{s.id}</span>
                </div>
              </div>
              <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                {s.criticality}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {s.description}
            </p>

            <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-100 text-center">
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-[10px] text-slate-400 block font-semibold">Readiness</span>
                <span className="text-sm font-bold text-amber-600">{s.readiness_score}%</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-[10px] text-slate-400 block font-semibold">Risk Posture</span>
                <span className="text-sm font-bold text-rose-600">HIGH</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-[10px] text-slate-400 block font-semibold">Open Findings</span>
                <span className="text-sm font-bold text-slate-900">{s.open_findings_count}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-400">
                Business Owner: <b className="text-slate-700">{s.business_owner || 'Dr. Marcus Vance'}</b>
              </span>
              <Link
                href={`/systems/${s.id}`}
                className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
              >
                <span>System Dossier</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
