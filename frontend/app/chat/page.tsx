'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import {
  Send, Bot, User, Sparkles, CheckCircle2, AlertCircle, FileText,
  ExternalLink, ArrowRight, ShieldAlert, Cpu, RefreshCw, Activity, ShieldCheck
} from 'lucide-react';
import { api } from '@/lib/api';
import { QueryResponse, SourceCitation } from '@/lib/types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  responseMeta?: QueryResponse;
  timestamp: string;
}

type ChatMode = 'GxP Audit' | 'General Q&A' | 'Document Search' | 'Release Readiness' | 'Risk Analysis' | 'Traceability';

const MODE_PROMPTS: Record<ChatMode, string[]> = {
  'GxP Audit': [
    "Run the GxP audit on PAS-X.",
    "Why did question 7 fail?",
    "Compare PAS-X against the master lifecycle SOP.",
    "Which audit questions fail?",
    "Show questions where evidence is missing.",
    "What should we fix before release?",
    "Generate an audit evidence report."
  ],
  'Release Readiness': [
    "Is the MES PAS-X system audit ready?",
    "What is blocking release?",
    "Why is G5 not met?",
    "Have all verification activities been completed?"
  ],
  'Risk Analysis': [
    "What risks remain open?",
    "Why are residual risks unrated for 49 requirements?"
  ],
  'Document Search': [
    "Show evidence in NL-MES-IREP-001 Section 3.2",
    "What does HACK-IT-SOP-001 expect for Gate G5?"
  ],
  'Traceability': [
    "Which URS requirements lack verified test scripts?",
    "Show traceability for URS-009 and URS-028"
  ],
  'General Q&A': [
    "Explain how MES PAS-X differs from LIMS benchmark",
    "What regulations apply to commercial packaging MES?"
  ]
};

export default function ChatPage() {
  const [chatMode, setChatMode] = useState<ChatMode>('GxP Audit');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-welcome',
      sender: 'assistant',
      content: (
        "Hello! I am your GxP IT Audit & Lifecycle Intelligence Assistant for Novo Nordisk.\n\n" +
        "I reason across:\n" +
        "• Primary Evidence: Novo Life MES PAS-X Lifecycle Package (NL-MES-*)\n" +
        "• Governance SOP: NN Master IT System Lifecycle SOP (HACK-IT-SOP-001)\n" +
        "• Benchmark Reference: GxP LIMS Lifecycle Package (LIMS-LCP-001)\n" +
        "• Executable Audit: Top 25 Difficult-Auditor Questions (2026 XLSX)\n\n" +
        "Try asking: 'Run the GxP audit on PAS-X.' or 'Why did question 7 fail?'"
      ),
      timestamp: 'Just now'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedMeta, setSelectedMeta] = useState<QueryResponse | null>(null);
  const [aiHealth, setAiHealth] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    api.getAiHealth().then(setAiHealth).catch(() => {});
  }, []);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const response = await api.queryRAG(query, 'SYS-MES-001', 6, chatMode);
      setSelectedMeta(response);

      const assistantMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        sender: 'assistant',
        content: response.answer,
        responseMeta: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error(err);
      const errorMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        sender: 'assistant',
        content: "Error executing GxP grounded search: " + (err.message || 'Unknown network error'),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = MODE_PROMPTS[chatMode] || MODE_PROMPTS['GxP Audit'];

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-8.5rem)]">
      {/* Left Pane: Chat Conversation Window */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        {/* Chat Window Header */}
        <div className="px-6 py-3 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#002B49] flex items-center justify-center text-white shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm font-bold text-slate-900">GxP Audit & Lifecycle Assistant</h2>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-1.5 py-0.5 rounded border border-emerald-300">
                  Audit Grounded
                </span>
                <span className="text-[10px] bg-blue-100 text-blue-800 font-semibold px-1.5 py-0.5 rounded border border-blue-300 font-mono">
                  SYS-MES-001
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Reasoning across MES PAS-X (Primary), Master IT SOP, LIMS Benchmark & Top 25 Audit Checklist
              </p>
            </div>
          </div>

          {/* Mode Selector Tabs */}
          <div className="flex items-center gap-1 bg-slate-200/80 p-1 rounded-lg text-xs overflow-x-auto max-w-full">
            {(['GxP Audit', 'Release Readiness', 'Risk Analysis', 'Traceability', 'General Q&A'] as ChatMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setChatMode(m)}
                className={`px-2 py-1 rounded-md text-[11px] font-semibold transition-all shrink-0 ${
                  chatMode === m
                    ? 'bg-[#002B49] text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-300/60'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div key={msg.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-[#002B49] flex items-center justify-center text-white shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}
                <div className={`max-w-2xl rounded-xl p-4 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-blue-600 text-white rounded-br-none shadow-sm'
                    : 'bg-slate-50 text-slate-900 border border-slate-200 rounded-bl-none shadow-sm'
                }`}>
                  <div className="whitespace-pre-wrap font-sans text-xs">{msg.content}</div>

                  {/* Inline Citations & Guardrail Tags */}
                  {!isUser && msg.responseMeta && (
                    <div className="mt-3 pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-slate-600">Grounded Citations:</span>
                        <div className="flex flex-wrap gap-1">
                          {msg.responseMeta.citations.map((cite, i) => (
                            <span key={i} className="text-[9.5px] bg-blue-100 text-blue-900 border border-blue-200 font-mono px-1.5 py-0.5 rounded font-semibold">
                              {cite}
                            </span>
                          ))}
                        </div>
                      </div>

                      <button
                        onClick={() => setSelectedMeta(msg.responseMeta!)}
                        className="text-[10px] font-semibold text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
                      >
                        Inspect Evidence →
                      </button>
                    </div>
                  )}

                  <div className={`text-[9px] mt-2 text-right ${isUser ? 'text-blue-200' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </div>
                </div>
                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-blue-100 border border-blue-300 flex items-center justify-center text-blue-800 shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-3 justify-start items-center text-xs text-slate-500">
              <div className="w-7 h-7 rounded-lg bg-[#002B49] flex items-center justify-center text-white shrink-0">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center gap-2 text-xs text-slate-600">
                <span>Multi-agent mesh verifying GxP rules & document evidence...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts Pill Carousel */}
        <div className="px-6 py-2 bg-slate-50/50 border-t border-slate-100 flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0">Quick Queries ({chatMode}):</span>
          {samplePrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              className="shrink-0 bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-300 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Query Input Box */}
        <div className="p-4 border-t border-slate-200 flex gap-2 bg-white">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask questions grounded in MES PAS-X documents (e.g. 'What is blocking release?')..."
            className="flex-1 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={loading || !inputQuery.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Right Pane: Real-Time Evidence & Multi-Agent Execution Panel */}
      <div className="w-full lg:w-96 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden shrink-0">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600" />
            <h3 className="text-xs font-bold text-slate-900">AI Observability & Evidence</h3>
          </div>
          <span className="text-[10px] bg-blue-100 text-blue-800 font-mono px-1.5 py-0.5 rounded font-bold">
            {aiHealth?.provider || 'OpenRouter'}
          </span>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {/* AI Provider Health Badge */}
          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-700">Provider Status:</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                aiHealth?.has_api_key ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {aiHealth?.status || 'Offline Fallback'}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-1 font-mono">
              Model: {aiHealth?.model || 'anthropic/claude-3.5-sonnet'}
            </div>
          </div>

          {/* Multi-Agent Execution Pipeline (Section 43) */}
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Multi-Agent Execution Pipeline</span>
            <div className="mt-2 space-y-2">
              {[
                { name: 'Supervisor Agent', detail: 'Decomposed intent & evaluated lifecycle scope' },
                { name: 'System Knowledge Agent', detail: 'Retrieved grounded chunks from 10 lifecycle docs' },
                { name: 'Compliance Agent', detail: 'Evaluated 15 rules from compliance_rules.json' },
                { name: 'Traceability Agent', detail: 'Traversed 50 URS requirements & 26 system risks' },
                { name: 'Release Gate Engine', detail: 'Evaluated G1-G6: Confirmed HOLD / DEFER' },
                { name: 'Recommendation Agent', detail: 'Synthesized corrective human-gated remediation' }
              ].map((step, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs bg-slate-50 p-2 rounded-md border border-slate-100">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-800 block text-[11px]">{step.name}</span>
                    <span className="text-[10px] text-slate-500">{step.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Confidence Score */}
          {selectedMeta && (
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Confidence Evaluation</span>
              <div className="mt-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800">
                    {Math.round(selectedMeta.confidence * 100)}% Grounded Confidence
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    selectedMeta.confidence >= 0.85
                      ? 'bg-emerald-100 text-emerald-800'
                      : selectedMeta.confidence >= 0.70
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}>
                    {selectedMeta.confidence >= 0.85 ? 'HIGH' : selectedMeta.confidence >= 0.70 ? 'MEDIUM' : 'LOW'}
                  </span>
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full ${
                      selectedMeta.confidence >= 0.85
                        ? 'bg-emerald-500'
                        : selectedMeta.confidence >= 0.70
                        ? 'bg-amber-500'
                        : 'bg-rose-500'
                    }`}
                    style={{ width: `${selectedMeta.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Warnings (Hallucination Detection) */}
          {selectedMeta?.warnings && selectedMeta.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg">
              <div className="flex items-center gap-1.5 text-amber-900 font-bold text-xs mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>Hallucination Guardrail Notice</span>
              </div>
              <ul className="list-disc list-inside text-[11px] text-amber-800 space-y-0.5">
                {selectedMeta.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Verified Source Citations */}
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Primary Grounding Evidence</span>
            <div className="mt-2 space-y-2">
              {(selectedMeta?.sources || [
                { document: 'NL-MES-ITPSE-001.docx', section: 'Overall Conclusion & Recommendation', page: 1 },
                { document: 'NL-MES-IREP-001.docx', section: 'Lifecycle Phase Gate Status (G1-G6)', page: 3 },
                { document: 'NL-MES-URS-001.docx', section: 'Document Approvals & Signatures', page: 2 },
              ]).map((src: any, idx: number) => (
                <div key={idx} className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 text-[11px] flex items-center gap-1 truncate">
                      <FileText className="w-3 h-3 text-blue-600 shrink-0" />
                      {src.document}
                    </span>
                    {src.page && (
                      <span className="text-[10px] bg-slate-200 text-slate-700 px-1 rounded shrink-0">Page {src.page}</span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">Section: {src.section || 'General'}</p>
                  {src.snippet && (
                    <p className="text-[10px] text-slate-600 italic bg-white p-1.5 rounded mt-1 border border-slate-100">
                      &quot;{src.snippet}&quot;
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Shortcuts */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <Link
              href="/compliance"
              className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-between transition-colors"
            >
              <span>Release Gates & Traceability</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
            <Link
              href="/evidence"
              className="w-full bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-between transition-colors"
            >
              <span>Compile Evidence Pack</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
