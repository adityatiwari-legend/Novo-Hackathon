'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, MessageSquare, CheckSquare, AlertOctagon,
  FileCheck, GitPullRequest, History, FileText, Server, Cpu,
  ShieldCheck, Lock, ExternalLink
} from 'lucide-react';
import { api } from '@/lib/api';

interface NavSection {
  title: string;
  items: {
    name: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: number | null;
    tag?: string;
    highlight?: boolean;
  }[];
}

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    api.getPendingWorkflows()
      .then(wfs => setPendingCount(wfs.length))
      .catch(() => {});
  }, [pathname]);

  const navSections: NavSection[] = [
    {
      title: 'OVERVIEW',
      items: [
        { name: 'Mission Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Systems Registry', href: '/systems', icon: Server },
      ],
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { name: 'AI Co-Pilot Workspace', href: '/chat', icon: MessageSquare, highlight: true, tag: 'RAG' },
        { name: 'Agent Observability', href: '/admin', icon: Cpu },
      ],
    },
    {
      title: 'ASSURANCE & AUDIT',
      items: [
        { name: 'GxP Audit & Intelligence', href: '/audit', icon: History, tag: 'TOP 25' },
        { name: 'Compliance Checklist', href: '/compliance', icon: CheckSquare },
        { name: 'Risk Register (ICH Q9)', href: '/risk', icon: AlertOctagon },
      ],
    },
    {
      title: 'EVIDENCE & LIFECYCLE',
      items: [
        { name: 'Audit Evidence Dossiers', href: '/evidence', icon: FileCheck },
        { name: 'Document Repository', href: '/documents', icon: FileText },
      ],
    },
    {
      title: 'GOVERNANCE & AUDIT TRAIL',
      items: [
        {
          name: 'Approvals & Workflows',
          href: '/workflows',
          icon: GitPullRequest,
          badge: pendingCount > 0 ? pendingCount : null,
        },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none min-h-[calc(100vh-5.5rem)]">
      <div className="py-4 space-y-5">
        {navSections.map((section) => (
          <div key={section.title} className="px-3">
            <div className="px-3 mb-1.5 text-[10px] font-bold text-slate-400/90 uppercase tracking-widest font-mono">
              {section.title}
            </div>
            <nav className="space-y-0.5">
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== '/dashboard' && pathname?.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`group relative flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                      isActive
                        ? 'bg-blue-600/90 text-white shadow-xs font-semibold'
                        : item.highlight
                        ? 'text-cyan-300 hover:bg-slate-800/80 hover:text-white'
                        : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive
                            ? 'text-white'
                            : item.highlight
                            ? 'text-cyan-400'
                            : 'text-slate-400 group-hover:text-slate-200'
                        }`}
                      />
                      <span className="truncate">{item.name}</span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                      {item.badge !== null && item.badge !== undefined && (
                        <span className="bg-amber-400 text-slate-950 text-[10px] font-bold px-1.5 py-0.2 rounded-full tabular-nums">
                          {item.badge}
                        </span>
                      )}
                      {item.tag && !isActive && (
                        <span className="text-[9px] font-mono font-semibold px-1 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                          {item.tag}
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Regulatory Footprint Footer */}
      <div className="p-3 m-3 bg-slate-950/90 rounded-xl border border-slate-800/90 text-[10.5px] text-slate-400 space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-bold text-slate-200 flex items-center gap-1">
            <Lock className="w-3 h-3 text-emerald-400" />
            <span>GxP Ledger</span>
          </span>
          <span className="font-mono text-[9.5px] text-emerald-300 font-bold bg-emerald-950/80 border border-emerald-800/60 px-1 py-0.2 rounded">
            SHA-256
          </span>
        </div>
        <p className="leading-tight text-slate-400 text-[10px]">
          Deterministic evaluation with mandatory human authorization gate for all GxP lifecycle actions.
        </p>
      </div>
    </aside>
  );
};
