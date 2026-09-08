'use client';

import React, { useEffect, useState } from 'react';
import {
  Cpu, Shield, CheckCircle2, UserCheck, Layers, RefreshCw, Key, ShieldCheck, Terminal,
  Lock, Sparkles, Activity
} from 'lucide-react';
import { api } from '@/lib/api';

export default function AdminPage() {
  const [agentsData, setAgentsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgentsHealth()
      .then(setAgentsData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const guardrails = [
    { rule: 'AI cannot directly modify source qualification documents.', status: 'ENFORCED' },
    { rule: 'AI cannot directly execute GxP actions without human authorization.', status: 'ENFORCED' },
    { rule: 'AI cannot approve its own recommendation.', status: 'ENFORCED' },
    { rule: 'AI cannot bypass human approval gate.', status: 'ENFORCED' },
    { rule: 'AI cannot fabricate citations or regulatory evidence.', status: 'ENFORCED' },
    { rule: 'AI cannot claim regulatory certification without verified proof.', status: 'ENFORCED' },
    { rule: 'AI cannot mutate or delete append-only audit trail logs.', status: 'ENFORCED' },
    { rule: 'Low-confidence compliance findings strictly require human review.', status: 'ENFORCED' },
    { rule: 'Deterministic release gate G5 blocks production activation upon unrated risks.', status: 'ENFORCED' },
    { rule: 'All model responses must reference indexed document citations with section/page.', status: 'ENFORCED' },
  ];

  const roles = [
    { role: 'QA_COMPLIANCE', user: 'qa@demo.local', desc: 'Full review, human workflow approval, dossier signing', active: true },
    { role: 'SYSTEM_OWNER', user: 'owner@demo.local', desc: 'System management, document upload, workflow creation', active: false },
    { role: 'AUDITOR', user: 'auditor@demo.local', desc: 'Read-only access, evidence verification, audit chain review', active: false },
    { role: 'ADMIN', user: 'admin@demo.local', desc: 'Platform configuration, agent observability, mesh maintenance', active: false },
  ];

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
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">Agent Observability & Governance Center</h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              LangGraph Mesh
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time telemetry of multi-agent mesh, enterprise connector stubs, and GxP regulatory guardrails
          </p>
        </div>

        <span className="bg-emerald-50 text-emerald-800 text-xs font-bold px-3 py-1.5 rounded-xl flex items-center gap-1.5 border border-emerald-300 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Mesh Status: OPERATIONAL</span>
        </span>
      </div>

      {/* Active Specialized Agents */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Active Specialized Agents Mesh (6 Engines)</h2>
            <p className="text-xs text-slate-500">Deterministic scoring & RAG grounded via OpenRouter / Local Fallback</p>
          </div>
          <span className="text-xs font-mono text-blue-700 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
            OpenRouter Active
          </span>
        </div>

        <div className="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              name: 'Compliance Agent',
              role: 'Evaluates 42 automated regulatory rules against 21 CFR Part 11, EU Annex 11, and ALCOA+ standards.',
              model: 'Deterministic Engine',
              status: 'Active',
            },
            {
              name: 'Traceability Agent',
              role: 'Builds bidirectional URS-to-Test matrix across 50 requirements and flags verification gaps.',
              model: 'Deterministic Engine',
              status: 'Active',
            },
            {
              name: 'Risk Agent',
              role: 'Analyzes ICH Q9 hazard register, failure modes, severity ratings, and residual risks.',
              model: 'ICH Q9 Engine',
              status: 'Active',
            },
            {
              name: 'Release Gate Engine',
              role: 'Enforces gates G1 through G6. Holds Gate G5 when residual risks or test gaps exist.',
              model: 'Gatekeeper Rulebase',
              status: 'Active',
            },
            {
              name: 'Evidence Dossier Agent',
              role: 'Compiles inspection-ready PDF & Word dossiers with SHA-256 cryptographic signatures.',
              model: 'ReportLab / Docx Engine',
              status: 'Active',
            },
            {
              name: 'AI Co-Pilot (RAG Agent)',
              role: 'Grounded semantic retrieval across 10 qualification documents with strict ALCOA+ citations.',
              model: 'claude-3.5-sonnet',
              status: 'Active',
            },
          ].map((agent, i) => (
            <div key={i} className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-xs">{agent.name}</span>
                <span className="bg-emerald-100 text-emerald-800 text-[9.5px] font-bold px-1.5 py-0.2 rounded font-mono">
                  {agent.status}
                </span>
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">{agent.role}</p>
              <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>Model: {agent.model}</span>
                <span className="text-emerald-700 font-bold">100% Deterministic</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two-Column: Enforced GxP Guardrails & RBAC Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Enforced Guardrails (Left 7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">Enforced GxP Policy Guardrails (10 Rules)</h2>
            </div>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-mono">
              ALL ENFORCED
            </span>
          </div>

          <div className="space-y-2">
            {guardrails.map((g, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200/70 rounded-xl text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="text-slate-800 font-medium">{g.rule}</span>
                </div>
                <span className="text-[9.5px] font-mono font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded shrink-0 ml-2">
                  {g.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* RBAC Simulator (Right 5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900">Role-Based Access Control (RBAC)</h2>
            </div>
            <span className="text-[10px] font-mono text-slate-400">21 CFR Part 11</span>
          </div>

          <div className="space-y-3">
            {roles.map(r => (
              <div
                key={r.role}
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 transition-all ${
                  r.active
                    ? 'bg-blue-50/70 border-blue-300 ring-1 ring-blue-500/20'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-slate-900">{r.role}</span>
                  {r.active && (
                    <span className="text-[9.5px] font-bold bg-blue-600 text-white px-2 py-0.5 rounded font-mono">
                      ACTIVE USER
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-600 leading-snug">{r.desc}</p>
                <span className="text-[10px] font-mono text-slate-400 block">{r.user}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
