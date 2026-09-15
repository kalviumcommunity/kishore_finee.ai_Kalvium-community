import React, { useState } from "react";
import { AlertTriangle, ChevronRight, ArrowRightLeft, ShieldAlert } from "lucide-react";
import { ConflictDetails } from "@/types";

interface ConflictBannerProps {
  conflict: ConflictDetails;
  onOpenModal: () => void;
}

export const ConflictBanner: React.FC<ConflictBannerProps> = ({ conflict, onOpenModal }) => {
  return (
    <div className="bg-amber-950/30 border border-amber-800/60 rounded-xl p-4 my-4 relative overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-950 border border-amber-800 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-amber-300">
                {conflict.title}
              </h4>
              <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded bg-amber-900/60 text-amber-300 border border-amber-700/60">
                Review Advised
              </span>
            </div>
            <p className="text-xs text-gray-300 mt-1 leading-relaxed">
              {conflict.description}
            </p>
            <p className="text-xs text-amber-200/80 mt-2 font-medium">
              💡 <span className="underline">Recommendation</span>: {conflict.recommendation}
            </p>
          </div>
        </div>

        <button
          onClick={onOpenModal}
          className="px-3 py-1.5 rounded-lg bg-amber-900/40 hover:bg-amber-800/50 border border-amber-700/70 text-amber-200 text-xs font-medium flex items-center gap-1.5 transition-colors shrink-0"
        >
          <ArrowRightLeft className="w-3.5 h-3.5" />
          <span>Compare Sources (A vs B)</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
