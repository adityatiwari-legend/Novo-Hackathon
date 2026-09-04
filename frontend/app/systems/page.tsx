'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Server, ShieldCheck, ArrowRight, RefreshCw, ExternalLink,
  Layers, CheckCircle2, AlertTriangle
} from 'lucide-react';
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
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">
              Validated GxP IT Systems Registry
            </h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              {systems.length} Registered
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Enterprise computerized systems categorized by GAMP 5 classification and GxP criticality
          </p>
        </div>
      </div>

      {/* Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {systems.map((s) => {
          const isPrimary = s.id === 'SYS-MES-001';

          return (
            <div
              key={s.id}
              className={`bg-white rounded-2xl border p-6 space-y-4 shadow-xs flex flex-col justify-between transition-all ${
                isPrimary
                  ? 'border-blue-300 ring-2 ring-blue-600/20 bg-gradient-to-br from-white to-blue-50/20'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                      isPrimary
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      <Server className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-slate-900">{s.name}</h2>
                        {isPrimary && (
                          <span className="text-[9.5px] font-bold bg-blue-600 text-white px-1.5 py-0.2 rounded font-mono">
                            PRIMARY
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-mono text-slate-400">{s.id}</span>
                    </div>
                  </div>

                  <span className="bg-blue-50 text-blue-800 border border-blue-200 text-[11px] font-bold px-2.5 py-0.5 rounded font-mono">
                    {s.criticality}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  {s.description}
                </p>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
                  <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/80">
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Classification</span>
                    <span className="font-semibold text-slate-800">GAMP Cat 4</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/80">
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Status</span>
                    <span className={`font-semibold ${
                      isPrimary ? 'text-amber-700' : 'text-emerald-700'
                    }`}>
                      {s.gxp_status}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-400 font-mono">
                  Owner: {s.business_owner}
                </span>
                <Link
                  href={`/systems/${s.id}`}
                  className="bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
                >
                  <span>System Dossier</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
