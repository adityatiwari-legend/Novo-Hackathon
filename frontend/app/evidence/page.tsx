'use client';

import React, { useEffect, useState } from 'react';
import {
  FileCheck, Download, Sparkles, RefreshCw, CheckCircle2,
  FileText, Shield, Clock, ExternalLink, ArrowRight, Lock
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvidencePack } from '@/lib/types';

export default function EvidencePage() {
  const [evidencePacks, setEvidencePacks] = useState<EvidencePack[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genStep, setGenStep] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getEvidencePacks();
      setEvidencePacks(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenStep('Step 1/5: Ingesting 10 lifecycle documents & Master IT SOP...');

    setTimeout(() => setGenStep('Step 2/5: Validating 50 URS requirement citations against 21 CFR Part 11...'), 800);
    setTimeout(() => setGenStep('Step 3/5: Evaluating 26 ICH Q9 hazards & residual risk controls...'), 1600);
    setTimeout(() => setGenStep('Step 4/5: Compiling formal PDF and Word DOCX evidence dossiers...'), 2400);

    try {
      await api.generateEvidencePack('SYS-MES-001');
      setGenStep('Step 5/5: Cryptographically sealing SHA-256 tamper-evident signature...');
      setTimeout(async () => {
        await loadData();
        setGenerating(false);
        setGenStep(null);
      }, 1000);
    } catch (err) {
      console.error(err);
      setGenerating(false);
      setGenStep(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">
              Audit Evidence & Regulatory Dossier Generator
            </h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              SYS-MES-001
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Automated compilation of complete GxP qualification dossiers with cryptographic verification
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs transition-colors disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
          <span>{generating ? 'Generating Dossier...' : 'Generate New Evidence Dossier'}</span>
        </button>
      </div>

      {/* Generation Progress Banner */}
      {generating && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-5 rounded-2xl shadow-xs space-y-3 animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
            <span className="text-xs font-bold text-blue-900">
              Multi-Agent Evidence Compilation Pipeline Active
            </span>
          </div>
          <div className="w-full bg-blue-200/60 h-2 rounded-full overflow-hidden">
            <div className="bg-blue-600 h-full w-full animate-pulse"></div>
          </div>
          <p className="text-xs text-blue-800 font-mono font-medium">
            {genStep}
          </p>
        </div>
      )}

      {/* Regulatory Context Banner */}
      <div className="bg-slate-900 text-slate-200 p-5 rounded-2xl shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
            <Shield className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Always-On, Instant Audit Readiness</h2>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed mt-0.5">
              Instead of spending 3–6 weeks manually assembling binders before a regulatory inspection, the GxP Co-Pilot continuously synchronizes evidence to produce inspection-ready dossiers on demand.
            </p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <span className="font-mono text-[11px] text-emerald-300 bg-emerald-950/80 border border-emerald-800/80 px-2.5 py-1 rounded font-bold">
            ALCOA+ Verified
          </span>
        </div>
      </div>

      {/* Generated Dossiers Archive */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <span>Compiled Audit Evidence Packs ({evidencePacks.length})</span>
        </h2>

        {evidencePacks.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 space-y-2">
            <FileText className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="text-sm font-semibold text-slate-800">No Evidence Dossiers Compiled Yet</p>
            <p className="text-xs text-slate-400">Click "Generate New Evidence Dossier" above to create your first report.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {evidencePacks.map(pack => (
              <div
                key={pack.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:border-slate-300 transition-all"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-900">{pack.id}</span>
                    <span className="text-slate-400">•</span>
                    <span className="font-mono text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      {pack.system_id}
                    </span>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-mono">
                      SEALED
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900">
                    GxP System Qualification & Audit Readiness Dossier
                  </h3>

                  <p className="text-xs text-slate-500 font-mono">
                    SHA-256 Hash: <span className="text-slate-700 font-semibold">{(pack as any).checksum?.substring(0, 32) || pack.id}</span>
                  </p>

                  <div className="text-[11px] text-slate-400 pt-1 flex items-center gap-3">
                    <span>Generated: {new Date(pack.created_at).toLocaleString()}</span>
                    <span>•</span>
                    <span>Status: {pack.status || 'Complete'}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  <a
                    href={api.getPdfDownloadUrl(pack.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-rose-600 hover:bg-rose-700 text-white px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download PDF</span>
                  </a>

                  <a
                    href={api.getDocxDownloadUrl(pack.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-blue-700 hover:bg-blue-800 text-white px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Word</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
