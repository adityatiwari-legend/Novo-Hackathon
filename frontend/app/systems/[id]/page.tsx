'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Server, ShieldCheck, ArrowLeft, ArrowRight, FileText, CheckCircle2,
  AlertTriangle, RefreshCw, Cpu, Layers
} from 'lucide-react';
import { api } from '@/lib/api';
import { System, Document, ComplianceFinding } from '@/lib/types';

export default function SystemDetailPage() {
  const params = useParams();
  const systemId = (params?.id as string) || 'SYS-MES-001';

  const [system, setSystem] = useState<System | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [findings, setFindings] = useState<ComplianceFinding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getSystem(systemId),
      api.getDocuments(systemId),
      api.getFindings(systemId)
    ])
      .then(([s, d, f]) => {
        setSystem(s);
        setDocs(d);
        setFindings(f);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [systemId]);

  if (loading || !system) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link href="/systems" className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-semibold">
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Systems Registry</span>
      </Link>

      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">{system.name}</h1>
            <span className="bg-blue-50 text-blue-800 border border-blue-200 text-xs font-bold px-2 py-0.5 rounded font-mono">
              {system.id}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">{system.description}</p>
        </div>

        <Link
          href={`/dashboard`}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors shrink-0"
        >
          <span>Open Mission Control</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Classification</span>
          <span className="text-base font-bold text-slate-900">GAMP Cat 4</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">GxP Criticality</span>
          <span className="text-base font-bold text-blue-700">{system.criticality}</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">Lifecycle State</span>
          <span className="text-base font-bold text-amber-700">{system.gxp_status}</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">System Owner</span>
          <span className="text-base font-bold text-slate-900">{system.business_owner}</span>
        </div>
      </div>

      {/* Linked Documents & Findings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Linked Documents */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <span>Associated Lifecycle Documents ({docs.length})</span>
          </h2>

          <div className="space-y-2 max-h-72 overflow-y-auto">
            {docs.map(d => (
              <div key={d.id} className="bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block truncate max-w-xs">{d.title}</span>
                  <span className="font-mono text-[10px] text-slate-400">{d.id} • v{d.version}</span>
                </div>
                <Link href="/documents" className="text-blue-600 hover:text-blue-800 font-semibold text-xs">
                  Inspect
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* Linked Findings */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span>Active Release Blockers ({findings.length})</span>
          </h2>

          <div className="space-y-2 max-h-72 overflow-y-auto">
            {findings.map(f => (
              <div key={f.id} className="bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-rose-700">{f.id}</span>
                  <span className="text-[10px] font-bold bg-rose-100 text-rose-800 px-1.5 py-0.2 rounded font-mono">
                    {f.severity}
                  </span>
                </div>
                <p className="text-slate-800 font-medium line-clamp-2">{f.description || f.title}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
