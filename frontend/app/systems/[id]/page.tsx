'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Server, ShieldCheck, ArrowLeft, ArrowRight, FileText, CheckCircle2,
  AlertTriangle, RefreshCw, Cpu
} from 'lucide-react';
import { api } from '@/lib/api';
import { System, Document, ComplianceFinding } from '@/lib/types';

export default function SystemDetailPage() {
  const params = useParams();
  const systemId = (params?.id as string) || 'SYS-LIMS-001';

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

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">{system.name}</h1>
            <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded font-mono">
              {system.id}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">{system.description}</p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/compliance"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold"
          >
            Open Compliance Checklist
          </Link>
          <Link
            href="/chat"
            className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-xs font-semibold"
          >
            Query System in Chat
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Linked Documents */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            Applicable GxP Documentation ({docs.length})
          </h2>
          <div className="divide-y divide-slate-100 text-xs">
            {docs.map((d) => (
              <div key={d.id} className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">{d.title}</span>
                  <span className="text-[10px] text-slate-400">Type: {d.document_type} | v{d.version}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  d.approval_status.includes('Missing') ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {d.approval_status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Identified Gaps */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Active Compliance Gaps ({findings.length})
          </h2>
          <div className="divide-y divide-slate-100 text-xs">
            {findings.map((f) => (
              <div key={f.id} className="py-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{f.title}</span>
                  <span className="text-[10px] bg-rose-100 text-rose-800 px-1.5 py-0.5 rounded font-bold">
                    {f.severity}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 line-clamp-2">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
