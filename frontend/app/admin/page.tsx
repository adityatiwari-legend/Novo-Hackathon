'use client';

import React, { useEffect, useState } from 'react';
import {
  Cpu, Shield, CheckCircle2, UserCheck, Layers, RefreshCw, Key, ShieldCheck, Terminal
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
    { rule: 'AI cannot directly modify source documents.', status: 'ENFORCED' },
    { rule: 'AI cannot directly execute GxP actions without human authorization.', status: 'ENFORCED' },
    { rule: 'AI cannot approve its own recommendation.', status: 'ENFORCED' },
    { rule: 'AI cannot bypass human approval gate.', status: 'ENFORCED' },
    { rule: 'AI cannot fabricate citations or regulatory evidence.', status: 'ENFORCED' },
    { rule: 'AI cannot claim regulatory certification without verified proof.', status: 'ENFORCED' },
    { rule: 'AI cannot mutate or delete append-only audit trail logs.', status: 'ENFORCED' },
    { rule: 'Low-confidence compliance findings strictly require human review.', status: 'ENFORCED' },
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
      <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-900">Agent Observability & Governance Center</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time telemetry of LangGraph multi-agent mesh, enterprise connector stubs, and GxP regulatory guardrails.
          </p>
        </div>
        <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5 border border-emerald-300">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Mesh Status: OPERATIONAL</span>
        </span>
      </div>

      {/* Active Specialized Agents */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-900">Active Specialized Agents Mesh (6 Implemented)</h2>
          <p className="text-xs text-slate-500">Orchestrated via LangGraph StateGraph with deterministic scoring gates</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-5">
          {(agentsData?.active_agents || []).map((a: any) => (
            <div key={a.name} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900">{a.display_name}</span>
                  <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded">
                    {a.status}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono block mt-0.5">{a.framework}</span>
                <p className="text-[11px] text-slate-600 mt-2 leading-relaxed">{a.description}</p>
              </div>
              <div className="pt-2 border-t border-slate-200/80 flex items-center justify-between text-[10px] text-slate-500">
                <span>Avg Latency: <b className="text-slate-700">{a.average_latency_ms}ms</b></span>
                <span>Confidence: <b className="text-emerald-700">{Math.round(a.confidence * 100)}%</b></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Registered Enterprise Stubs */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-900">Registered Enterprise Stubs (Clean Future Interfaces)</h2>
          <p className="text-xs text-slate-500">Stubbed behind standardized AgentResult interfaces for future enterprise connectors</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-5">
          {(agentsData?.enterprise_stubs || []).map((s: any) => (
            <div key={s.name} className="bg-slate-50/70 p-4 rounded-xl border border-dashed border-slate-300 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-800">{s.display_name}</span>
                <span className="bg-slate-200 text-slate-700 text-[9px] font-semibold px-1.5 py-0.5 rounded">
                  Enterprise Stub
                </span>
              </div>
              <span className="text-[10px] text-blue-600 font-semibold block">{s.category}</span>
              <p className="text-[11px] text-slate-500 leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* GxP Guardrails & RBAC */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regulatory Guardrails */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">Enforced GxP Policy Guardrails (10 Rules)</h2>
          </div>
          <div className="space-y-2 text-xs">
            {guardrails.map((g, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-700 font-medium">{g.rule}</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded shrink-0 ml-2">
                  {g.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* RBAC Role Simulator */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <UserCheck className="w-5 h-5 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900">Role-Based Access Control (RBAC) Simulator</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            {roles.map((r) => (
              <div key={r.role} className={`p-3 rounded-lg border ${r.active ? 'bg-blue-50/60 border-blue-300' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 font-mono text-xs">{r.role}</span>
                  {r.active && (
                    <span className="text-[10px] bg-blue-600 text-white font-bold px-2 py-0.5 rounded">
                      Active User Session
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-600 mt-1">{r.desc}</p>
                <span className="text-[10px] text-slate-400 font-mono block mt-1">Simulated User: {r.user}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
