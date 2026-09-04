'use client';

import React, { useEffect, useState } from 'react';
import {
  GitPullRequest, CheckCircle2, XCircle, AlertCircle, Clock,
  ShieldCheck, RefreshCw, ExternalLink, ArrowRight, UserCheck,
  Lock, FileText, CheckSquare, AlertTriangle
} from 'lucide-react';
import { api } from '@/lib/api';
import { Workflow } from '@/lib/types';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State for Approve
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [selectedWf, setSelectedWf] = useState<Workflow | null>(null);
  const [approvalComment, setApprovalComment] = useState('Approved after review of evidence and mitigation plan.');
  const [actionLoading, setActionLoading] = useState(false);

  // Modal State for Reject
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getAllWorkflows();
      setWorkflows(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async () => {
    if (!selectedWf) return;
    setActionLoading(true);
    try {
      await api.approveWorkflow(selectedWf.id, approvalComment, 'qa@demo.local');
      setApproveModalOpen(false);
      setSelectedWf(null);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedWf || !rejectionReason.trim()) return;
    setActionLoading(true);
    try {
      await api.rejectWorkflow(selectedWf.id, rejectionReason, 'qa@demo.local');
      setRejectModalOpen(false);
      setSelectedWf(null);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const pending = workflows.filter(w => w.status === 'PENDING_APPROVAL');
  const history = workflows.filter(w => w.status !== 'PENDING_APPROVAL');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GitPullRequest className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">
              Human-in-the-Loop Governance & Change Authorizations
            </h1>
            <span className="text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">
              {pending.length} Action Pending
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            21 CFR Part 11 Compliant Electronic Signatures & ServiceNow IT Change Gatekeeping
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Workflows</span>
        </button>
      </div>

      {/* GxP Governance Policy Notice */}
      <div className="bg-gradient-to-r from-blue-900 to-[#002B49] text-white p-5 rounded-2xl shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-cyan-300" />
          </div>
          <div className="space-y-0.5">
            <h2 className="text-sm font-bold">AI Proposes, Humans Authorize (ALCOA+ Safeguard)</h2>
            <p className="text-xs text-slate-200 max-w-2xl leading-relaxed">
              Autonomous agents continuously monitor telemetry and formulate remediation workflows. Under no circumstances does AI execute production changes without explicit QA electronic sign-off.
            </p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <span className="text-[11px] font-mono bg-white/15 px-2.5 py-1 rounded-md border border-white/20 font-semibold block">
            Role: QA_COMPLIANCE
          </span>
        </div>
      </div>

      {/* Pending Authorizations Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" />
            <span>Pending Authorizations Requiring QA Electronic Signature ({pending.length})</span>
          </h2>
        </div>

        {pending.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="text-sm font-semibold text-slate-800">All GxP Workflows Authorized</p>
            <p className="text-xs text-slate-400">There are no outstanding human-in-the-loop approvals queued.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pending.map(wf => (
              <div
                key={wf.id}
                className="bg-white rounded-2xl border border-amber-200/80 shadow-xs p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5 bg-gradient-to-r from-amber-50/20 to-white"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2 py-0.5 rounded font-mono">
                      PENDING AUTHORIZATION
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-800">{wf.id}</span>
                    <span className="text-slate-400">•</span>
                    <span className="font-mono text-xs text-blue-700 font-semibold">{wf.system_id}</span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900">
                    {wf.type || 'SOP Remediation & Gap Closure'}
                  </h3>

                  <p className="text-xs text-slate-600 leading-relaxed">
                    {wf.payload_json?.action_summary || wf.payload_json?.title || 'Remediation proposed by AI Compliance Engine. Automated analysis determined corrective action is required before Gate G5 can be satisfied.'}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
                    <span className="font-mono text-[10.5px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                      Target: {wf.payload_json?.target || 'PAS-X Configuration'}
                    </span>
                    {wf.payload_json?.citation && (
                      <span className="font-mono text-[10.5px] bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded">
                        {wf.payload_json.citation}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
                  <button
                    onClick={() => {
                      setSelectedWf(wf);
                      setRejectModalOpen(true);
                    }}
                    className="bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => {
                      setSelectedWf(wf);
                      setApproveModalOpen(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>Authorize & Execute (21 CFR Part 11)</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historical Workflows Ledger */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Completed Lifecycle Changes & Approvals Ledger ({history.length})
          </h2>
          <span className="text-xs text-slate-400 font-mono">ServiceNow Synced</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                <th className="py-3 px-4 w-28">Workflow ID</th>
                <th className="py-3 px-4 w-28">System</th>
                <th className="py-3 px-4">Action Summary</th>
                <th className="py-3 px-4 w-28 text-center">Status</th>
                <th className="py-3 px-4 w-40">Approver / QA Sign-off</th>
                <th className="py-3 px-4 w-36">Change Ticket</th>
                <th className="py-3 px-4 w-32">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.map(w => {
                const isApproved = w.status === 'APPROVED';
                return (
                  <tr key={w.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-800">{w.id}</td>
                    <td className="py-3 px-4 font-mono text-slate-700">{w.system_id}</td>
                    <td className="py-3 px-4 text-slate-800">
                      <p className="font-semibold">{w.type}</p>
                      <p className="text-[11px] text-slate-500 line-clamp-1">
                        {w.payload_json?.action_summary || w.rejection_reason || 'Authorization granted'}
                      </p>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-bold ${
                          isApproved
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : 'bg-rose-100 text-rose-800 border border-rose-300'
                        }`}
                      >
                        {w.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                      {w.approved_by || 'qa@demo.local'}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-blue-700">
                      {w.payload_json?.servicenow_ticket ? (
                        <span className="bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                          {w.payload_json.servicenow_ticket}
                        </span>
                      ) : (
                        <span className="text-slate-400">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      {w.approved_at ? new Date(w.approved_at).toLocaleDateString() : 'Recent'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* APPROVE MODAL */}
      {approveModalOpen && selectedWf && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                <UserCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">21 CFR Part 11 Electronic Signature</h3>
                <p className="text-xs text-slate-500">Formal authorization of GxP change</p>
              </div>
            </div>

            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs space-y-1">
              <p className="font-bold text-slate-800">{selectedWf.type || 'SOP Remediation'}</p>
              <p className="text-slate-600 font-mono text-[11px]">Target: {selectedWf.system_id}</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                QA Authorization Justification & Comments:
              </label>
              <textarea
                rows={3}
                value={approvalComment}
                onChange={e => setApprovalComment(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-[11px] text-blue-900 space-y-1">
              <span className="font-bold block">Attestation:</span>
              <p>
                By clicking Authorize, I certify under 21 CFR Part 11 that I have reviewed the qualification evidence, verified the remediation action, and approve this release workflow.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                onClick={() => setApproveModalOpen(false)}
                className="bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 px-4 py-2 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs disabled:opacity-50"
              >
                {actionLoading ? 'Signing & Linking...' : 'Sign & Authorize'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT MODAL */}
      {rejectModalOpen && selectedWf && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="w-9 h-9 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center">
                <XCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Reject GxP Proposed Action</h3>
                <p className="text-xs text-slate-500">Provide regulatory justification for audit trail</p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                Regulatory Rejection Reason (Mandatory):
              </label>
              <textarea
                rows={3}
                value={rejectionReason}
                onChange={e => setRejectionReason(e.target.value)}
                placeholder="State why this recommendation cannot be authorized..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-rose-500 resize-none"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                onClick={() => setRejectModalOpen(false)}
                className="bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 px-4 py-2 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading || !rejectionReason.trim()}
                className="bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs disabled:opacity-50"
              >
                {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
