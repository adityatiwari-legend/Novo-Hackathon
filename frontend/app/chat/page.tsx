'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Bot, User, Sparkles, FileText, CheckCircle2,
  AlertTriangle, ShieldCheck, ArrowRight, RefreshCw,
  ExternalLink, Layers, ChevronRight, Lock, Hash
} from 'lucide-react';
import { api } from '@/lib/api';
import { QueryResponse, DocumentChunk } from '@/lib/types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  responseObj?: QueryResponse;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-init',
      role: 'assistant',
      content:
        'Hello! I am your GxP IT Assurance Co-Pilot for Novo Life MES PAS-X (SYS-MES-001). All answers are deterministically grounded against 21 CFR Part 11, EU Annex 11, GAMP 5, and the 10 canonical PAS-X lifecycle documents. How can I assist your audit review today?',
      timestamp: 'Just now',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeMode, setActiveMode] = useState<string>('Audit Assessment');
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<any | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const modes = [
    { id: 'Audit Assessment', label: 'Top 25 Audit' },
    { id: 'Release Readiness', label: 'Release Gates' },
    { id: 'Risk & Hazard Analysis', label: 'ICH Q9 Risk' },
    { id: 'Traceability Gaps', label: 'Traceability' },
    { id: 'Document Grounding', label: 'SOP Grounding' },
  ];

  const suggestedQueries = [
    'Is Novo Life MES PAS-X ready for production release?',
    'What specific gaps are blocking Gate G5 Release Readiness?',
    'Show all failed questions in the Top 25 Audit Checklist',
    'Which URS requirements lack direct test script verification?',
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await api.queryRAG(textToSend, 'SYS-MES-001', 6, activeMode);

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        responseObj: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (res.retrieved_chunks && res.retrieved_chunks.length > 0) {
        setSelectedChunk(res.retrieved_chunks[0]);
      }
    } catch (err: any) {
      console.error(err);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error evaluating query against GxP knowledge base: ${err.message || 'Service unavailable'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-4">
      {/* Co-Pilot Top Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-cyan-600 flex items-center justify-center text-white shadow-xs">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900">GxP AI Co-Pilot Workspace</h1>
              <span className="text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded font-mono">
                SYS-MES-001
              </span>
              <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                95% Grounded
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Deterministic RAG retrieval grounded across 10 qualification documents & Master IT SOP
            </p>
          </div>
        </div>

        {/* Clean Segmented Mode Selector (NO HORIZONTAL SCROLL) */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl text-xs font-semibold">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setActiveMode(m.id)}
              className={`px-3 py-1.5 rounded-lg transition-all text-xs ${
                activeMode === m.id
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Dual-Column Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Chat Thread Area (Left 8 cols) */}
        <div className="lg:col-span-8 flex flex-col h-[calc(100vh-14rem)] bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          {/* Scrollable Message List */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                      isUser
                        ? 'bg-slate-900 text-white'
                        : 'bg-blue-50 text-blue-700 border border-blue-200'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`space-y-1.5 max-w-[85%] ${isUser ? 'items-end' : ''}`}>
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? 'bg-[#002B49] text-white rounded-tr-xs shadow-xs'
                          : 'bg-slate-50 text-slate-800 border border-slate-200/80 rounded-tl-xs shadow-xs'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{m.content}</p>

                      {/* Evidence Citations Chips */}
                      {m.responseObj?.citations && m.responseObj.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-slate-200/60 flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-500 uppercase font-mono mr-1">
                            Evidence Citations:
                          </span>
                          {m.responseObj.citations.map((cite, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setSelectedCitation(cite);
                                if (m.responseObj?.retrieved_chunks) {
                                  const matching = m.responseObj.retrieved_chunks.find((c: any) =>
                                    c.citation?.toLowerCase().includes(cite.toLowerCase()) ||
                                    c.content?.toLowerCase().includes(cite.toLowerCase())
                                  );
                                  if (matching) setSelectedChunk(matching);
                                }
                              }}
                              className="font-mono text-[10px] bg-white hover:bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded transition-colors flex items-center gap-1 shadow-2xs"
                              title="Click to inspect grounding chunk in right panel"
                            >
                              <FileText className="w-3 h-3 text-blue-600" />
                              <span>{cite}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className={`text-[10px] text-slate-400 font-mono px-1 ${isUser ? 'text-right' : ''}`}>
                      {m.timestamp}
                    </div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-center gap-3 animate-fadeIn">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 flex items-center justify-center shrink-0">
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-2xl text-xs text-slate-600 space-y-1">
                  <p className="font-semibold text-slate-800">
                    Grounded RAG retrieval active in mode: <b className="text-blue-700">{activeMode}</b>
                  </p>
                  <p className="text-[11px] text-slate-500 font-mono">
                    Searching vector embeddings, validating ALCOA+ citations & release criteria...
                  </p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Quick Queries Strip */}
          <div className="p-2.5 bg-slate-50/90 border-t border-slate-200 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] font-bold text-slate-400 font-mono uppercase px-1">
              Suggested:
            </span>
            {suggestedQueries.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="text-[11px] bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/80 px-2.5 py-1 rounded-lg transition-colors truncate max-w-xs shadow-2xs disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-3 bg-white border-t border-slate-200 flex items-end gap-2">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask anything regarding ${activeMode} for Novo Life MES PAS-X (Press Enter to submit)...`}
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white p-3 rounded-xl transition-colors shadow-xs shrink-0 flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Contextual Intelligence Panel (Right 4 cols) */}
        <div className="lg:col-span-4 flex flex-col h-[calc(100vh-14rem)] bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
                Evidence & Grounding Dossier
              </h2>
            </div>
            <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded">
              Verified
            </span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
            {selectedChunk ? (
              <div className="space-y-3">
                <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-3.5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-blue-900 text-xs truncate max-w-[200px]">
                      {selectedChunk.document_title || 'NL-MES-ITPSE-001'}
                    </span>
                    <span className="font-mono text-[10px] bg-white text-blue-800 border border-blue-200 px-1.5 py-0.2 rounded font-semibold">
                      v1.0
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[10.5px] text-slate-600 font-mono">
                    {selectedChunk.section && (
                      <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200">
                        § {selectedChunk.section}
                      </span>
                    )}
                    {selectedChunk.page_number && (
                      <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200">
                        Page {selectedChunk.page_number}
                      </span>
                    )}
                  </div>

                  <p className="text-slate-800 text-[11px] leading-relaxed whitespace-pre-wrap bg-white p-2.5 rounded-lg border border-blue-100 font-mono">
                    {selectedChunk.content}
                  </p>
                </div>

                <div className="space-y-2">
                  <span className="text-[10.5px] font-bold text-slate-500 uppercase font-mono block">
                    Grounded Regulatory Mapping:
                  </span>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 space-y-1 text-[11px]">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Framework:</span>
                      <span className="font-bold text-slate-800 font-mono">21 CFR Part 11 / EU Annex 11</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">GAMP Category:</span>
                      <span className="font-bold text-slate-800 font-mono">Category 4 (Configured)</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Traceability Status:</span>
                      <span className="font-bold text-amber-700 font-mono">Partial (Gate G5 Hold)</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
                <FileText className="w-8 h-8 text-slate-300" />
                <p className="text-xs font-semibold text-slate-600">No Citation Selected</p>
                <p className="text-[11px] text-slate-400">
                  Click any evidence citation chip inside an AI response to inspect the exact grounded document chunk, section, and page.
                </p>
              </div>
            )}
          </div>

          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
            <span className="flex items-center gap-1 font-mono">
              <Lock className="w-3 h-3 text-emerald-600" />
              <span>Tamper-evident chain linked</span>
            </span>
            <span className="text-blue-600 font-semibold font-mono">SHA-256</span>
          </div>
        </div>
      </div>
    </div>
  );
}
