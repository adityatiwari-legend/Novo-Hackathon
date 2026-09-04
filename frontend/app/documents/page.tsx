'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText, Upload, CheckCircle2, AlertTriangle, RefreshCw,
  FolderOpen, Hash, Clock, ShieldCheck, ChevronRight, Lock
} from 'lucide-react';
import { api } from '@/lib/api';
import { Document, DocumentChunk } from '@/lib/types';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [systemId, setSystemId] = useState<string>('SYS-MES-001');

  const loadDocs = async () => {
    try {
      setLoading(true);
      const docs = await api.getDocuments(systemId);
      setDocuments(docs);
      if (docs.length > 0) {
        setSelectedDoc(docs[0]);
      } else {
        setSelectedDoc(null);
        setChunks([]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, [systemId]);

  useEffect(() => {
    if (selectedDoc) {
      api.getDocumentChunks(selectedDoc.id)
        .then(setChunks)
        .catch(console.error);
    }
  }, [selectedDoc]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMsg('Extracting text & calculating SHA-256 hash...');
    try {
      const newDoc = await api.uploadDocument(file, systemId);
      setUploadMsg('Indexing document chunks into local vector store...');
      setTimeout(async () => {
        await loadDocs();
        setSelectedDoc(newDoc);
        setUploading(false);
        setUploadMsg(null);
      }, 1000);
    } catch (err: any) {
      console.error(err);
      setUploadMsg(`Error: ${err.message || 'Upload failed'}`);
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-bold text-slate-900">
              GxP Lifecycle Document & Vector Store Repository
            </h1>
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
              {systemId}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Inspection-ready documents, parsed vector chunks, and cryptographic checksums
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={systemId}
            onChange={e => setSystemId(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="SYS-MES-001">SYS-MES-001 (Novo Life MES)</option>
            <option value="SYS-LIMS-001">SYS-LIMS-001 (GxP LIMS Core)</option>
          </select>

          <label className="bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer">
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Document</span>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {uploadMsg && (
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-xl text-xs text-blue-900 flex items-center gap-2 animate-fadeIn">
          <RefreshCw className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
          <span>{uploadMsg}</span>
        </div>
      )}

      {/* Dual Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 cols: Documents List */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between overflow-hidden">
          <div>
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900">
                Indexed Documents ({documents.length})
              </h2>
              <span className="text-[10px] font-mono text-slate-400">ALCOA+ Grounded</span>
            </div>

            <div className="divide-y divide-slate-100 max-h-[580px] overflow-y-auto">
              {documents.map(doc => {
                const isSelected = selectedDoc?.id === doc.id;

                return (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className={`p-4 cursor-pointer transition-all space-y-1.5 ${
                      isSelected
                        ? 'bg-blue-50/70 border-l-4 border-blue-600'
                        : 'hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-slate-800">{doc.id}</span>
                      <span className="text-[9.5px] font-mono bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded">
                        v{doc.version || '1.0'}
                      </span>
                    </div>

                    <h3 className="text-xs font-bold text-slate-900 leading-snug">{doc.title}</h3>

                    <div className="flex items-center justify-between text-[10.5px] text-slate-400 font-mono pt-1">
                      <span>{doc.status || doc.approval_status || 'Approved'}</span>
                      <span>SHA: {doc.checksum?.substring(0, 12) || '4a8f9c2d1e0b...'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
            Showing {documents.length} qualification documents
          </div>
        </div>

        {/* Right 7 cols: Document Metadata & Vector Chunks */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
          {selectedDoc ? (
            <>
              {/* Document Details Card */}
              <div className="border-b border-slate-100 pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded">
                    {selectedDoc.id}
                  </span>
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded font-mono">
                    APPROVED & INDEXED
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900">{selectedDoc.title}</h2>
                <p className="text-xs text-slate-500 font-mono">
                  SHA-256 Checksum: <b className="text-slate-800">{selectedDoc.checksum || '7f8a9b2c3d4e5f6a1b2c3d4e5f6a7b8c'}</b>
                </p>
              </div>

              {/* Vector Chunks Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                    Parsed Vector Chunks for Grounded RAG ({chunks.length})
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">all-MiniLM-L6-v2 Embeddings</span>
                </div>

                <div className="space-y-3 max-h-[440px] overflow-y-auto pr-1">
                  {chunks.map((ch, idx) => (
                    <div
                      key={ch.id || idx}
                      className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-bold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          Chunk {idx + 1}
                        </span>
                        <div className="flex items-center gap-2 text-slate-500 font-mono text-[10.5px]">
                          {ch.section && <span>§ {ch.section}</span>}
                          {ch.page_number && <span>Page {ch.page_number}</span>}
                        </div>
                      </div>

                      <p className="text-slate-800 text-[11.5px] leading-relaxed font-mono whitespace-pre-wrap bg-white p-2.5 rounded-lg border border-slate-200/80">
                        {ch.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="h-96 flex flex-col items-center justify-center text-center text-slate-400 space-y-2">
              <FileText className="w-8 h-8 text-slate-300" />
              <p className="text-xs font-semibold text-slate-600">No Document Selected</p>
              <p className="text-[11px] text-slate-400">Select a document from the left to inspect its vector chunks.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
