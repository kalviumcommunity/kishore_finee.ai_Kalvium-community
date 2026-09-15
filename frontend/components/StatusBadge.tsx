import React from "react";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = "md" }) => {
  const s = status.toLowerCase();

  let bg = "bg-surface-raised";
  let text = "text-gray-300";
  let border = "border-surface-border";
  let dot = "bg-gray-400";
  let label = status.toUpperCase();

  if (s === "approved" || s === "answered" || s === "indexed" || s === "passed" || s === "success" || s === "active") {
    bg = "bg-emerald-950/40";
    text = "text-emerald-400";
    border = "border-emerald-800/60";
    dot = "bg-emerald-400";
  } else if (s === "processing" || s === "pending" || s === "review_requested" || s === "warning" || s === "uploaded") {
    bg = "bg-amber-950/40";
    text = "text-amber-400";
    border = "border-amber-800/60";
    dot = "bg-amber-400";
  } else if (s.includes("refused") || s === "failed" || s === "error" || s === "conflict" || s === "conflicting_evidence") {
    bg = "bg-red-950/40";
    text = "text-red-400";
    border = "border-red-800/60";
    dot = "bg-red-400";
    if (s.includes("weak_context")) label = "REFUSED (WEAK CONTEXT)";
    if (s.includes("empty_context")) label = "REFUSED (EMPTY CONTEXT)";
  } else if (s === "archived" || s === "superseded" || s === "idle") {
    bg = "bg-gray-900/60";
    text = "text-gray-400";
    border = "border-gray-800";
    dot = "bg-gray-500";
  }

  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${bg} ${text} ${border} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
};
