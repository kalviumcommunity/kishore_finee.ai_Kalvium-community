import React from "react";
import { FileText, Eye, ShieldCheck, ChevronRight } from "lucide-react";
import { CitationSource } from "@/types";
import { StatusBadge } from "./StatusBadge";

interface EvidenceCardProps {
  source: CitationSource;
  onInspect: (source: CitationSource) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ source, onInspect }) => {
  return (
    <div className="bg-surface border border-surface-border rounded-xl p-4 transition-all hover:border-surface-borderLight group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-6 h-6 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 font-mono text-xs font-bold flex items-center justify-center shrink-0">
            {source.marker.replace("[", "").replace("]", "")}
          </span>
          <div className="min-w-0">
            <h4 className="text-xs font-semibold text-white truncate group-hover:text-emerald-300 transition-colors">
              {source.source}
            </h4>
            <p className="text-[11px] text-gray-400 font-mono">
              {source.section} • Page {source.page}
            </p>
          </div>
        </div>
        <StatusBadge status={source.approval_status || "approved"} size="sm" />
      </div>

      <p className="mt-3 text-xs text-gray-300 line-clamp-2 leading-relaxed bg-surface-raised/60 p-2.5 rounded-lg border border-surface-border/60">
        "{source.text}"
      </p>

      <div className="mt-3 flex items-center justify-between pt-2 border-t border-surface-border/60">
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-gray-400">
          <span>Relevance:</span>
          <span className="text-emerald-400 font-bold">
            {(source.relevance_score * 100).toFixed(0)}%
          </span>
        </div>

        <button
          onClick={() => onInspect(source)}
          className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Inspect Source</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
