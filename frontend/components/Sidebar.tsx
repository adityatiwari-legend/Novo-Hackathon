'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, MessageSquare, CheckSquare, AlertOctagon,
  FileCheck, GitPullRequest, History, FileText, Server, Cpu
} from 'lucide-react';
import { api } from '@/lib/api';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    api.getPendingWorkflows()
      .then(wfs => setPendingCount(wfs.length))
      .catch(() => {});
  }, [pathname]);

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Co-Pilot Chat', href: '/chat', icon: MessageSquare, highlight: true },
    { name: 'Systems', href: '/systems', icon: Server },
    { name: 'Compliance Checklist', href: '/compliance', icon: CheckSquare },
    { name: 'Risk Register', href: '/risk', icon: AlertOctagon },
    { name: 'Audit Evidence', href: '/evidence', icon: FileCheck },
    {
      name: 'Approvals & Workflows',
      href: '/workflows',
      icon: GitPullRequest,
      badge: pendingCount > 0 ? pendingCount : null
    },
    { name: 'GxP Audit & Intelligence', href: '/audit', icon: History, shield: true, highlight: true },
    { name: 'Documents Viewer', href: '/documents', icon: FileText },
    { name: 'Agent Observability', href: '/admin', icon: Cpu },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 border-r border-slate-800 flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="py-4">
        <div className="px-4 mb-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          GxP Operations Navigation
        </div>
        <nav className="space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-700 text-white shadow-sm'
                    : item.highlight
                    ? 'text-blue-300 hover:bg-slate-800 hover:text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : item.highlight ? 'text-blue-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
                  <span>{item.name}</span>
                </div>
                {item.badge !== null && item.badge !== undefined && (
                  <span className="bg-amber-500 text-slate-950 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
                {item.shield && (
                  <span className="text-[9px] bg-emerald-950 text-emerald-300 border border-emerald-700 px-1 py-0.2 rounded font-mono">
                    SHA-256
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Regulatory Notice in Footer */}
      <div className="p-3 m-3 bg-slate-950/80 rounded-lg border border-slate-800 text-[10px] text-slate-400 leading-relaxed">
        <p className="font-semibold text-slate-300 mb-1">GxP Prototype Notice:</p>
        <p>Aligned with ALCOA+ & 21 CFR Part 11 principles. AI recommendations strictly require human authorization before execution.</p>
      </div>
    </aside>
  );
};
