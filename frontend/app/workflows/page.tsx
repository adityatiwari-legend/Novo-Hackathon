'use client';

import React, { useEffect, useState } from 'react';
import {
  GitPullRequest, CheckCircle2, XCircle, AlertCircle, Clock,
  ShieldCheck, RefreshCw, ExternalLink, ArrowRight, UserCheck
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
      const res = await api.getAllWorkflows('SYS-LIMS-001');
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
  const executed = workflows.filter(w => w.status !== 'PENDING_APPROVAL');

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
            <GitPullRequest className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-900">Human-in-the-Loop Approval Center</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Mandatory human authorization gate for all GxP actions. AI proposes; authenticated humans authorize.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded">
            {pending.length} Pending Approval
          </span>
        </div>
      </div>

      {/* Pending Approvals Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
          <Clock className="w-4 h-4 text-amber-600" />
          Pending Human Authorizations ({pending.length})
        </h2>

        {pending.length === 0 ? (
          <div className="bg-white p-8 rounded-xl border border-slate-200 text-center shadow-sm">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            <p className="text-sm font-bold text-slate-800">No Pending Approvals</p>
            <p className="text-xs text-slate-500 mt-1">All AI recommendations have either been authorized or addressed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pending.map((wf) => {
              const recTitle = wf.payload_json?.recommendation_title || 'Route URS for formal QA sign-off';
              const priority = wf.payload_json?.priority || 'CRITICAL';
              return (
                <div key={wf.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        priority === 'CRITICAL' ? 'bg-rose-100 text-rose-800 border border-rose-200' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {priority}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{recTitle}</h3>
                    </div>
                    <span className="text-xs font-mono text-slate-400">Target: SYS-LIMS-001</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-[10px] font-semibold text-slate-400 uppercase">GxP Justification:</span>
                      <p className="text-slate-800 mt-1 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                        Operating an unapproved User Requirements Specification invalidates system qualification baseline under 21 CFR Part 11 and EU Annex 11.
                      </p>
                    </div>

                    <div>
                      <span className="text-[10px] font-semibold text-slate-400 uppercase">Primary Evidence Citation:</span>
                      <p className="text-slate-700 mt-1 bg-slate-50 p-2.5 rounded-lg border border-slate-200 font-mono text-[11px]">
                        System_A_URS.docx (Section 6: Document Approvals & Signatures) — QA signature MISSING.
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                      <span>Requested for QA Review | Created: {new Date(wf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setSelectedWf(wf);
                          setRejectModalOpen(true);
                        }}
                        className="px-3.5 py-1.5 border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-lg text-xs font-semibold transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => {
                          setSelectedWf(wf);
                          setApproveModalOpen(true);
                        }}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-colors"
                      >
                        Approve & Execute Task
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* History of Executed Workflows */}
      {executed.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Executed GxP Actions History ({executed.length})
          </h2>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 font-semibold">Workflow Action</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Authorized By</th>
                  <th className="py-3 px-4 font-semibold">Enterprise Execution</th>
                  <th className="py-3 px-4 font-semibold text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {executed.map((wf) => {
                  const isApproved = wf.status === 'APPROVED';
                  const ticketId = wf.payload_json?.ticket_id || wf.payload_json?.snow_ticket?.ticket_id || 'SNOW-TASK-1001';
                  return (
                    <tr key={wf.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        {wf.payload_json?.recommendation_title || 'Route URS for formal QA approval'}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isApproved ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                        }`}>
                          {wf.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-600">{wf.approved_by || 'qa@demo.local'}</td>
                      <td className="py-3 px-4">
                        {isApproved ? (
                          <div className="flex items-center gap-1.5 font-bold text-blue-700 font-mono text-[11px]">
                            <span>ServiceNow:</span>
                            <span className="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded border border-blue-200">
                              {ticketId}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Rejection: {wf.rejection_reason || 'Rejected by QA'}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-500 text-[11px]">
                        {new Date(wf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Approve Confirmation Modal */}
      {approveModalOpen && selectedWf && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-2.5 text-slate-900 border-b border-slate-100 pb-3">
              <ShieldCheck className="w-6 h-6 text-emerald-600" />
              <h3 className="text-base font-bold">Authorize GxP Action</h3>
            </div>

            {/* Regulatory Notice Banner */}
            <div className="bg-blue-50 border border-blue-200 text-blue-900 p-3 rounded-lg text-xs leading-relaxed">
              <p className="font-bold mb-0.5">Mandatory GxP Authorization Statement:</p>
              You are approving an AI-generated workflow. The AI recommendation will not become effective until this human approval is recorded in the tamper-evident audit ledger.
            </div>

            <div className="text-xs text-slate-600 space-y-2">
              <p><b>Target Action:</b> {selectedWf.payload_json?.recommendation_title || 'Route URS for formal QA sign-off'}</p>
              <p><b>Target System:</b> SYS-LIMS-001 (Validated LIMS)</p>
              <p><b>Authorizer:</b> Dr. Elena Rostova (qa@demo.local)</p>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                Approval Justification Comment:
              </label>
              <textarea
                rows={3}
                value={approvalComment}
                onChange={(e) => setApprovalComment(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                onClick={() => setApproveModalOpen(false)}
                disabled={actionLoading}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                {actionLoading ? 'Recording Approval...' : 'Confirm Authorization & Create Ticket'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModalOpen && selectedWf && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-2.5 text-slate-900 border-b border-slate-100 pb-3">
              <XCircle className="w-6 h-6 text-rose-600" />
              <h3 className="text-base font-bold">Reject GxP Workflow</h3>
            </div>

            <div className="bg-rose-50 border border-rose-200 text-rose-900 p-3 rounded-lg text-xs">
              Under GxP compliance rules, a written justification reason is mandatory for any rejected workflow.
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                Mandatory Rejection Reason:
              </label>
              <textarea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="State the regulatory or technical basis for rejecting this recommendation..."
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                onClick={() => setRejectModalOpen(false)}
                disabled={actionLoading}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading || !rejectionReason.trim()}
                className="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {actionLoading ? 'Recording...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
