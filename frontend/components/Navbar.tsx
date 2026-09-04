'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ShieldCheck, Activity, RefreshCw, AlertTriangle, CheckCircle2,
  UserCheck, Server, Sparkles, Cpu, ChevronRight, X
} from 'lucide-react';
import { api } from '@/lib/api';

interface NavbarProps {
  onSimulationTriggered?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onSimulationTriggered }) => {
  const [simulationActive, setSimulationActive] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<{ provider: string; status: string; model?: string }>({
    provider: 'OpenRouter',
    status: 'ACTIVE',
    model: 'claude-3.5-sonnet'
  });

  useEffect(() => {
    api.getSimulationStatus()
      .then(res => setSimulationActive(res.simulation_active))
      .catch(() => {});

    api.getAiHealth()
      .then(res => {
        if (res?.provider) {
          setAiStatus({
            provider: res.provider,
            status: res.status || 'ACTIVE',
            model: res.model || 'claude-3.5-sonnet'
          });
        }
      })
      .catch(() => {});
  }, []);

  const handleToggleSimulation = async () => {
    setIsTriggering(true);
    try {
      if (simulationActive) {
        await api.resetSimulation();
        setSimulationActive(false);
        setNotification('Telemetry reset: Baseline readiness restored to 82% (SYS-MES-001).');
      } else {
        const res = await api.triggerSimulation();
        setSimulationActive(true);
        setNotification(res.notification || 'SOP Review Expired: Readiness dropped from 82% to 76% due to annual cycle expiration.');
      }
      if (onSimulationTriggered) {
        onSimulationTriggered();
      }
    } catch (err: any) {
      console.error('Failed to toggle simulation:', err);
    } finally {
      setIsTriggering(false);
      setTimeout(() => setNotification(null), 8000);
    }
  };

  return (
    <header className="sticky top-0 z-50 flex flex-col shrink-0 bg-[#002B49] text-white border-b border-slate-800 shadow-sm">
      {/* Slim Professional Regulatory Environment Banner */}
      <div className="bg-slate-950/80 border-b border-slate-800/80 px-4 py-1 text-[11px] text-slate-300">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 truncate">
            <span className="inline-flex items-center gap-1 font-mono font-bold text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.2 rounded shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
              SIMULATION ENVIRONMENT
            </span>
            <span className="text-slate-300 truncate">
              Training & Hackathon Validation Sandbox | <b className="text-white">Novo Life MES PAS-X</b> (SYS-MES-001) | Not a regulatory authorization decision
            </span>
          </div>
          <div className="hidden md:flex items-center gap-3 text-[10px] font-mono text-slate-400 shrink-0">
            <span>21 CFR Part 11</span>
            <span>•</span>
            <span>EU Annex 11</span>
            <span>•</span>
            <span>GAMP 5 Cat 4</span>
          </div>
        </div>
      </div>

      {/* Main Mission-Control Nav Header */}
      <div className="max-w-[1600px] mx-auto w-full px-4 sm:px-6 h-13 flex items-center justify-between gap-4">
        {/* Left: Brand / System Identity */}
        <div className="flex items-center gap-4 shrink-0">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-700 to-blue-500 flex items-center justify-center font-bold text-white shadow-sm ring-1 ring-white/20 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-sm tracking-tight text-white">GxP AI Co-Pilot</span>
                <span className="text-[9.5px] font-semibold tracking-wider uppercase bg-blue-500/20 text-blue-200 border border-blue-400/30 px-1.5 py-0.2 rounded font-mono">
                  ALCOA+
                </span>
              </div>
              <p className="text-[10px] text-slate-300/80 -mt-0.5">Continuous GxP IT Assurance</p>
            </div>
          </Link>

          {/* Active System Pill */}
          <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-slate-700/80 text-xs">
            <div className="flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-md transition-colors">
              <Server className="w-3.5 h-3.5 text-blue-400" />
              <span className="font-mono font-bold text-white text-[11px]">SYS-MES-001</span>
              <span className="text-slate-400 text-[11px]">|</span>
              <span className="text-slate-200 font-medium text-[11px]">Novo Life MES PAS-X</span>
              <span className="text-[9.5px] text-amber-300 font-semibold bg-amber-400/10 px-1 rounded border border-amber-400/20">
                Pre-Operational
              </span>
            </div>
          </div>
        </div>

        {/* Center/Right: AI Telemetry & Simulation Action Button */}
        <div className="flex items-center gap-3">
          {/* AI Mesh Telemetry Pill */}
          <div className="hidden sm:flex items-center gap-2 bg-slate-800/60 border border-slate-700/80 px-2.5 py-1 rounded-md text-[11px]">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span className="text-slate-400">Mesh:</span>
              <span className="font-mono text-slate-200 font-semibold">{aiStatus.provider}</span>
            </div>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[10px] text-emerald-300 font-bold">95% Conf</span>
          </div>

          {/* Simulation Toggle Trigger */}
          <button
            onClick={handleToggleSimulation}
            disabled={isTriggering}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border transition-all shadow-xs shrink-0 ${
              simulationActive
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 border-amber-400 font-bold'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-100 border-slate-600 hover:border-slate-500'
            }`}
            title="Simulate continuous document expiration telemetry without waiting for real calendar dates"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">
              {simulationActive ? 'Reset Simulation (82%)' : 'Simulate Telemetry Event (82% → 76%)'}
            </span>
            <span className="sm:hidden">
              {simulationActive ? 'Reset' : 'Simulate'}
            </span>
          </button>

          {/* Authenticated User Profile */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-700/80 shrink-0">
            <div className="w-7 h-7 rounded-full bg-blue-900 border border-blue-400/40 text-blue-200 flex items-center justify-center font-bold text-xs">
              ER
            </div>
            <div className="text-right hidden md:block leading-tight">
              <div className="text-xs font-semibold text-white flex items-center justify-end gap-1">
                <span>Dr. Elena Rostova</span>
              </div>
              <div className="flex items-center justify-end gap-1 text-[9.5px]">
                <span className="text-slate-300 font-mono">qa@demo.local</span>
                <span className="text-emerald-300 font-bold uppercase font-mono">QA_COMPLIANCE</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Notification Banner */}
      {notification && (
        <div className="bg-amber-400 text-slate-950 px-4 py-2 text-xs font-semibold flex items-center justify-between border-t border-amber-500 shadow-md animate-fadeIn">
          <div className="max-w-[1600px] mx-auto w-full flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-slate-950 shrink-0" />
              <span>{notification}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="p-1 hover:bg-amber-500/50 rounded text-slate-950 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
