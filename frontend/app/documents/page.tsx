'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText, Upload, CheckCircle2, AlertTriangle, RefreshCw,
  FolderOpen, Hash, Clock, ShieldCheck, ChevronRight
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

  const loadDocs = async () => {
    try {
      setLoading(true);
      const docs = await api.getDocuments('SYS-LIMS-001');
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        setSelectedDoc(docs[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

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
    setUploadMsg('Validating file checksum, extracting metadata, and indexing chunks in vector store...');
    try {
      const doc = await api.uploadDocument(file, 'SYS-LIMS-001');
      setUploadMsg(`Successfully ingested ${doc.title} with SHA-256 checksum!`);
      await loadDocs();
      setSelectedDoc(doc);
      setTimeout(() => setUploadMsg(null), 5000);
    } catch (err: any) {
      setUploadMsg(`Upload error: ${err.message || 'Failed'}`);
    } finally {
      setUploading(false);
    }
  };

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Upload Zone */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FolderOpen className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-900">GxP Document Ingestion & Validation Repository</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            ALCOA+ document verification. Calculates SHA-256 checksums, extracts section headings, and generates grounded vector chunks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors cursor-pointer shrink-0">
            <Upload className="w-4 h-4" />
            <span>Upload GxP Document</span>
            <input
              type="file"
              accept=".pdf,.docx,.xlsx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploadMsg && (
        <div className="bg-blue-50 border border-blue-200 text-blue-900 px-4 py-3 rounded-xl text-xs font-medium flex items-center gap-2 shadow-sm animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
          <span>{uploadMsg}</span>
        </div>
      )}

      {/* Dual Column: Document List & Document Inspection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900">Indexed Documents ({documents.length})</span>
            <span className="text-[10px] text-slate-400 font-mono">SYS-LIMS-001</span>
          </div>
          <div className="divide-y divide-slate-100 overflow-y-auto max-h-[600px]">
            {documents.map((doc) => {
              const isSelected = selectedDoc?.id === doc.id;
              const isUnapproved = doc.approval_status.includes('Missing') || doc.approval_status.includes('Pending');
              return (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDoc(doc)}
                  className={`p-4 cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50/70 border-l-4 border-blue-600' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      {doc.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">v{doc.version}</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500 font-medium">{doc.document_type}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isUnapproved ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {doc.approval_status}
                    </span>
                  </div>
                  <div className="mt-1 text-[10px] text-slate-400 font-mono truncate">
                    SHA256: {doc.checksum.slice(0, 16)}...
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Document Details & Chunks Inspector (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col space-y-4">
          {selectedDoc ? (
            <>
              {/* Document Metadata Bar */}
              <div className="border-b border-slate-100 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <h2 className="text-base font-bold text-slate-900">{selectedDoc.title}</h2>
                  <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                    selectedDoc.approval_status.includes('Missing') || selectedDoc.approval_status.includes('Pending')
                      ? 'bg-rose-100 text-rose-800 border border-rose-200'
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}>
                    {selectedDoc.approval_status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-xs">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold">Document Type</span>
                    <span className="font-bold text-slate-800">{selectedDoc.document_type}</span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold">Version</span>
                    <span className="font-bold text-slate-800">v{selectedDoc.version}</span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold">Review Date</span>
                    <span className="font-bold text-slate-800">{selectedDoc.review_date || 'Current'}</span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold">Owner</span>
                    <span className="font-bold text-slate-800">{selectedDoc.owner_id || 'Sarah Jenkins'}</span>
                  </div>
                </div>
              </div>

              {/* Chunks Inspector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold text-slate-900">
                    Extracted Vector Chunks ({chunks.length} Grounded Segments)
                  </h3>
                  <span className="text-[10px] text-slate-400">Preserving Page & Section Traceability</span>
                </div>

                <div className="space-y-3 overflow-y-auto max-h-[420px] pr-1">
                  {chunks.map((ch) => (
                    <div key={ch.id} className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-slate-800 text-[11px]">
                          Section: {ch.section || 'General'}
                        </span>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
                          {ch.page_number && (
                            <span className="bg-white border border-slate-200 px-1.5 py-0.5 rounded">
                              Page {ch.page_number}
                            </span>
                          )}
                          <span className="bg-white border border-slate-200 px-1.5 py-0.5 rounded">
                            Chunk #{ch.chunk_index}
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-700 whitespace-pre-wrap font-sans text-[11px] leading-relaxed">
                        {ch.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-400 text-center py-12">Select a document to inspect details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
