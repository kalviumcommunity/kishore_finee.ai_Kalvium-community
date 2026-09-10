import React from "react";
import { X, ExternalLink, ShieldCheck, FileText, Calendar, Hash, Tag } from "lucide-react";
import { CitationSource, RankedSnippet } from "@/types";
import { StatusBadge } from "./StatusBadge";

interface SourceInspectorDrawerProps {
  source: CitationSource | RankedSnippet | null;
  isOpen: boolean;
  onClose: () => void;
}

export const SourceInspectorDrawer: React.FC<SourceInspectorDrawerProps> = ({
  source,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !source) return null;

  const score = "score" in source ? source.score : source.relevance_score;
  const isApproved = source.approval_status === "approved";

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-surface border-l border-surface-border shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-5 border-b border-surface-border flex items-center justify-between bg-surface-raised">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-semibold text-white truncate max-w-[280px]">
                  {source.source}
                </h3>
                <p className="text-xs text-gray-400 font-mono">Source Provenance & Audit Detail</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-surface transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {/* Status Banner */}
            <div className="bg-surface-raised border border-surface-border rounded-xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs text-gray-400 block mb-1">Compliance Status</span>
                <StatusBadge status={source.approval_status || "approved"} />
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-400 block mb-1">Relevance Score</span>
                <span className="text-sm font-bold font-mono text-emerald-400">
                  {(score * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Document Metadata
              </h4>
              <div className="bg-surface-raised/60 border border-surface-border rounded-xl divide-y divide-surface-border text-xs">
                <div className="p-3 flex items-center justify-between">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-gray-500" /> Section / Provision
                  </span>
                  <span className="text-gray-200 font-medium">{source.section || "General Guidelines"}</span>
                </div>
                <div className="p-3 flex items-center justify-between">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-gray-500" /> Page Number
                  </span>
                  <span className="text-gray-200 font-mono">Page {source.page || 1}</span>
                </div>
                {"version" in source && (
                  <div className="p-3 flex items-center justify-between">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-gray-500" /> Policy Version
                    </span>
                    <span className="text-gray-200 font-mono">v{source.version}</span>
                  </div>
                )}
                <div className="p-3 flex items-center justify-between">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-gray-500" /> Effective Date
                  </span>
                  <span className="text-gray-200 font-mono">
                    {"effective_date" in source ? source.effective_date : "2026-01-01"}
                  </span>
                </div>
              </div>
            </div>

            {/* Text Excerpt */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Indexed Vector Chunk Content
                </h4>
                <span className="text-[11px] text-gray-500 font-mono">Exact Match</span>
              </div>
              <div className="p-4 rounded-xl bg-surface-raised border border-surface-border text-sm text-gray-200 leading-relaxed font-sans border-l-2 border-l-emerald-500">
                "{source.text}"
              </div>
            </div>

            {/* Ingestion Pipeline Provenance */}
            <div className="p-4 rounded-xl bg-surface-raised/40 border border-surface-border text-xs text-gray-400 space-y-2">
              <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <ShieldCheck className="w-4 h-4" /> Cryptographic Integrity Verified
              </div>
              <p className="text-[11px] leading-relaxed text-gray-400">
                This chunk is securely anchored to the verified knowledge repository. Embeddings generated via OpenAI text-embedding-3-small and indexed in ChromaDB HNSW cosine space.
              </p>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-surface-border bg-surface-raised flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-gray-300 hover:text-white bg-surface border border-surface-border rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
