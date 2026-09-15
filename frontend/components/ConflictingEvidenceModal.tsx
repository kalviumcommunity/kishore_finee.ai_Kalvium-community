import React from "react";
import { X, ArrowRightLeft, ShieldAlert, CheckCircle, FileText, Calendar, Building, Send } from "lucide-react";
import { ConflictDetails } from "@/types";
import { StatusBadge } from "./StatusBadge";

interface ConflictingEvidenceModalProps {
  conflict: ConflictDetails | null;
  isOpen: boolean;
  onClose: () => void;
  onRequestReview?: () => void;
}

export const ConflictingEvidenceModal: React.FC<ConflictingEvidenceModalProps> = ({
  conflict,
  isOpen,
  onClose,
  onRequestReview,
}) => {
  if (!isOpen || !conflict) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="relative bg-surface border border-surface-border rounded-2xl max-w-4xl w-full p-6 shadow-2xl overflow-hidden z-10 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-surface-border pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-950/80 border border-amber-800 text-amber-400 flex items-center justify-center">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                {conflict.title}
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800 text-amber-400 font-normal">
                  Divergent Provisions
                </span>
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                Side-by-side compliance policy resolution analysis
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-surface-raised transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Side-by-Side Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Source A */}
          <div className="bg-surface-raised border border-emerald-800/40 rounded-xl p-4 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold font-mono text-emerald-400 px-2 py-0.5 bg-emerald-950/80 border border-emerald-800 rounded">
                  Source A (Active Guidance)
                </span>
                <StatusBadge status={conflict.source_a.approval_status} size="sm" />
              </div>

              <h4 className="text-sm font-semibold text-white mt-2">
                {conflict.source_a.title}
              </h4>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                {conflict.source_a.section}
              </p>

              <div className="mt-3 p-3 rounded-lg bg-surface border border-surface-border text-xs text-gray-200 leading-relaxed font-sans border-l-2 border-l-emerald-500">
                "{conflict.source_a.excerpt}"
              </div>
            </div>

            <div className="pt-3 border-t border-surface-border text-[11px] text-gray-400 space-y-1">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Effective Date</span>
                <span className="font-mono text-gray-200">{conflict.source_a.effective_date}</span>
              </div>
              {conflict.source_a.authority && (
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1"><Building className="w-3 h-3" /> Issuing Authority</span>
                  <span className="text-gray-200">{conflict.source_a.authority}</span>
                </div>
              )}
            </div>
          </div>

          {/* Source B */}
          <div className="bg-surface-raised border border-amber-800/40 rounded-xl p-4 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold font-mono text-amber-400 px-2 py-0.5 bg-amber-950/80 border border-amber-800 rounded">
                  Source B (Contrasting Guidance)
                </span>
                <StatusBadge status={conflict.source_b.approval_status} size="sm" />
              </div>

              <h4 className="text-sm font-semibold text-white mt-2">
                {conflict.source_b.title}
              </h4>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                {conflict.source_b.section}
              </p>

              <div className="mt-3 p-3 rounded-lg bg-surface border border-surface-border text-xs text-gray-200 leading-relaxed font-sans border-l-2 border-l-amber-500">
                "{conflict.source_b.excerpt}"
              </div>
            </div>

            <div className="pt-3 border-t border-surface-border text-[11px] text-gray-400 space-y-1">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Effective Date</span>
                <span className="font-mono text-gray-200">{conflict.source_b.effective_date}</span>
              </div>
              {conflict.source_b.authority && (
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1"><Building className="w-3 h-3" /> Issuing Authority</span>
                  <span className="text-gray-200">{conflict.source_b.authority}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resolution Recommendation */}
        <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            <CheckCircle className="w-4 h-4" /> Compliance Resolution Guidance
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">
            {conflict.recommendation}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white transition-colors"
          >
            Dismiss
          </button>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (onRequestReview) onRequestReview();
                alert("Formal compliance escalation ticket logged with Elena Rostova (Lead Compliance Officer).");
                onClose();
              }}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition-colors flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Escalate to Compliance Review</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
            >
              Adopt Latest 2026 Policy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
