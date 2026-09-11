"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ShieldCheck,
  Clock,
  Archive,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Send,
  Layers,
  Hash,
  Calendar,
  Database,
  RefreshCw,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { DocumentDetail } from "@/types";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params?.id as string;

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!documentId) return;
    try {
      setLoading(true);
      const doc = await ragApi.getDocumentDetail(documentId);
      setDocument(doc);
    } catch (err) {
      console.error("Failed to load document detail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [documentId]);

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      await ragApi.approveDocument(documentId);
      setFeedbackMessage("Document marked as APPROVED for production RAG retrieval.");
      await fetchDetail();
    } catch (err: any) {
      alert(err.message || "Failed to approve document.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReview = async () => {
    setActionLoading(true);
    try {
      await ragApi.reviewDocument(documentId);
      setFeedbackMessage("Compliance review ticket initiated.");
      await fetchDetail();
    } catch (err: any) {
      alert(err.message || "Failed to request review.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleArchive = async () => {
    setActionLoading(true);
    try {
      await ragApi.archiveDocument(documentId);
      setFeedbackMessage("Document archived and deprecated from active vector search.");
      await fetchDetail();
    } catch (err: any) {
      alert(err.message || "Failed to archive document.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Topbar title="Document Inspector" subtitle="Loading metadata and chunk boundaries..." />
        <div className="flex-1 flex items-center justify-center p-12 text-gray-400 text-xs">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-400 mr-2" />
          Loading document details...
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Topbar title="Document Inspector" subtitle="Document not found" />
        <div className="flex-1 p-12 text-center space-y-4">
          <p className="text-gray-400 text-sm">Document '{documentId}' was not found in the repository.</p>
          <Link
            href="/admin/documents"
            className="px-4 py-2 rounded-lg bg-surface-raised border border-surface-border text-emerald-400 text-xs inline-flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Documents
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Document Inspector & Chunk Overlay"
        subtitle={`Viewing ${document.original_filename} (${document.chunks_count} indexed chunks)`}
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/admin/documents"
            className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to All Documents</span>
          </Link>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleReview}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Request Review</span>
            </button>
            <button
              onClick={handleArchive}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-gray-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Archive className="w-3.5 h-3.5" />
              <span>Archive</span>
            </button>
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Approve Document</span>
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedbackMessage && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              {feedbackMessage}
            </span>
            <button onClick={() => setFeedbackMessage(null)} className="text-gray-400 hover:text-white">
              Dismiss
            </button>
          </div>
        )}

        {/* Header Document Card */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-surface-raised border border-surface-border text-emerald-400 flex items-center justify-center shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-white tracking-tight">
                  {document.original_filename}
                </h2>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-raised border border-surface-border text-gray-300">
                  v{document.version}
                </span>
                <StatusBadge status={document.approval_status} />
              </div>
              <p className="text-xs text-gray-400 font-mono mt-1">
                ID: {document.document_id} • Uploaded {new Date(document.upload_timestamp).toLocaleDateString()} •{" "}
                {(document.file_size_bytes / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
        </div>

        {/* 2-Column Split: Chunk Overlays & Timeline/Metadata */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Chunk Boundary Overlay (8 Cols) */}
          <div className="lg:col-span-8 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                Semantic Chunk Boundaries ({document.chunks.length} chunks)
              </h3>
              <span className="text-[11px] text-gray-500 font-mono">ChromaDB Indexed Embeddings</span>
            </div>

            <div className="space-y-4">
              {document.chunks && document.chunks.length > 0 ? (
                document.chunks.map((chunk, idx) => (
                  <div
                    key={chunk.id}
                    className="bg-surface border border-surface-border hover:border-surface-borderLight rounded-xl p-5 space-y-3 transition-all relative overflow-hidden"
                  >
                    {/* Chunk Boundary Marker Top Bar */}
                    <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60">
                          Chunk #{chunk.chunk_index}
                        </span>
                        <span className="text-xs font-semibold text-white">
                          {chunk.section || `Section ${idx + 1}`}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px] font-mono text-gray-400">
                        <span>Page {chunk.page}</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-medium">{chunk.token_count} tokens</span>
                      </div>
                    </div>

                    {/* Chunk Body */}
                    <p className="text-xs text-gray-200 leading-relaxed font-sans bg-surface-raised/60 p-3.5 rounded-lg border border-surface-border/60 border-l-2 border-l-emerald-500">
                      "{chunk.text}"
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center bg-surface border border-surface-border rounded-xl text-gray-400 text-xs">
                  No chunk boundaries available for this document.
                </div>
              )}
            </div>
          </div>

          {/* Right: Metadata & Ingestion Timeline (4 Cols) */}
          <div className="lg:col-span-4 space-y-5">
            {/* Metadata Card */}
            <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-3">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Document Metadata
              </h3>
              <div className="divide-y divide-surface-border text-xs">
                <div className="py-2.5 flex items-center justify-between">
                  <span className="text-gray-400">Document ID:</span>
                  <span className="font-mono text-gray-200 text-[11px] truncate max-w-[150px]">
                    {document.document_id}
                  </span>
                </div>
                <div className="py-2.5 flex items-center justify-between">
                  <span className="text-gray-400">Policy Version:</span>
                  <span className="font-mono text-gray-200">v{document.version}</span>
                </div>
                <div className="py-2.5 flex items-center justify-between">
                  <span className="text-gray-400">Vector Status:</span>
                  <span className="text-emerald-400 font-mono font-medium">HNSW Indexed</span>
                </div>
                <div className="py-2.5 flex items-center justify-between">
                  <span className="text-gray-400">Total Tokens:</span>
                  <span className="font-mono text-gray-200">
                    {document.chunks.reduce((acc, c) => acc + (c.token_count || 0), 0)} tokens
                  </span>
                </div>
              </div>
            </div>

            {/* Lifecycle Timeline */}
            <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                Ingestion & Compliance Trace
              </h3>

              <div className="space-y-4 relative pl-3 border-l border-surface-border">
                {document.timeline.map((item, idx) => (
                  <div key={idx} className="relative pl-3 space-y-0.5">
                    <span
                      className={`absolute -left-[19px] top-1.5 w-2 h-2 rounded-full ${
                        item.status === "COMPLETED" || item.status === "APPROVED"
                          ? "bg-emerald-400"
                          : "bg-amber-400"
                      }`}
                    />
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-white">{item.action}</p>
                      <span className="text-[10px] font-mono text-gray-400">
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : "Complete"}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400 font-mono">{item.actor}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
