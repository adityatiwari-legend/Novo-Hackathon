'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ShieldCheck, Bell, Activity, RefreshCw, AlertTriangle, CheckCircle2, UserCheck } from 'lucide-react';
import { api } from '@/lib/api';

interface NavbarProps {
  onSimulationTriggered?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onSimulationTriggered }) => {
  const [simulationActive, setSimulationActive] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    api.getSimulationStatus()
      .then(res => setSimulationActive(res.simulation_active))
      .catch(() => {});
  }, []);

  const handleToggleSimulation = async () => {
    setIsTriggering(true);
    try {
      if (simulationActive) {
        await api.resetSimulation();
        setSimulationActive(false);
        setNotification('Simulation reset: Baseline readiness restored to 82%.');
      } else {
        const res = await api.triggerSimulation();
        setSimulationActive(true);
        setNotification(res.notification || 'SOP Review Expired: Readiness dropped from 82% to 76%.');
      }
      if (onSimulationTriggered) {
        onSimulationTriggered();
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsTriggering(false);
      setTimeout(() => setNotification(null), 7000);
    }
  };

  return (
    <header className="bg-[#002B49] text-white border-b border-slate-700 sticky top-0 z-40">
      {/* Prominent Regulatory Simulation Notice Bar */}
      <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-1 text-[11px] font-semibold text-amber-300 flex items-center justify-between">
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="bg-amber-500 text-slate-950 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
              Simulation Mode
            </span>
            <span>
              ⚠️ <b>DUMMY / HACKATHON / TRAINING SIMULATION</b> — Novo Life MES PAS-X (Pre-Operational). Not an operational release.
            </span>
          </div>
          <div className="hidden lg:flex items-center gap-3 text-[10px] text-amber-200/80 font-mono">
            <span>Framework: 21 CFR Part 11 | EU Annex 11 | GAMP 5 Cat 4</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Brand / Logo */}
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-lg text-white shadow-md">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-wide text-white">GxP AI Co-Pilot</span>
                <span className="text-[10px] font-semibold bg-blue-500/30 text-blue-200 border border-blue-400/40 px-1.5 py-0.5 rounded">
                  ALCOA+
                </span>
                <span className="text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.5 rounded">
                  MES PAS-X
                </span>
              </div>
              <p className="text-xs text-slate-300 font-medium">Always-On, Audit-Ready IT System Management</p>
            </div>
          </Link>
        </div>

        {/* Center: Live Simulation Button & Alert */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={handleToggleSimulation}
            disabled={isTriggering}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md border transition-all ${
              simulationActive
                ? 'bg-amber-600 hover:bg-amber-700 text-white border-amber-500 shadow-sm'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-600'
            }`}
            title="Simulate continuous document expiration telemetry without waiting for real calendar dates"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
            {simulationActive ? 'Reset Simulation (82%)' : 'Simulate SOP Expiration (82% → 76%)'}
          </button>
          
          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Agent Mesh: Active</span>
          </div>
        </div>

        {/* Right: User / Role Profile */}
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-semibold text-white flex items-center justify-end gap-1.5">
              <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Dr. Elena Rostova</span>
            </div>
            <div className="flex items-center justify-end gap-1.5">
              <span className="text-[10px] text-slate-300 font-mono">qa@demo.local</span>
              <span className="text-[9px] bg-emerald-950 text-emerald-300 border border-emerald-700 px-1.5 py-0.2 rounded font-semibold uppercase">
                QA_COMPLIANCE
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Notification Banner */}
      {notification && (
        <div className="bg-amber-500 text-slate-950 px-4 py-2 text-xs font-semibold flex items-center justify-between border-t border-amber-600 animate-fadeIn">
          <div className="flex items-center gap-2 max-w-5xl mx-auto">
            <AlertTriangle className="w-4 h-4 text-slate-950 flex-shrink-0" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-slate-950 hover:opacity-75 font-bold">✕</button>
        </div>
      )}
    </header>
  );
};
