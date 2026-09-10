"use client";

import React from "react";
import { Search, Bell, ShieldCheck, Sparkles, Terminal, Activity } from "lucide-react";

interface TopbarProps {
  title?: string;
  subtitle?: string;
  onSearchClick?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  title = "Analysis Session",
  subtitle = "Compliance-Grounded Advisory RAG",
  onSearchClick,
}) => {
  return (
    <header className="h-16 bg-surface/80 backdrop-blur-md border-b border-surface-border sticky top-0 z-20 flex items-center justify-between px-6">
      {/* Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            {title}
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          </h1>
          <p className="text-[11px] text-gray-400 font-mono">{subtitle}</p>
        </div>
      </div>

      {/* Center Search Bar Placeholder */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
        <button
          onClick={onSearchClick}
          className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg bg-surface-raised border border-surface-border text-xs text-gray-400 hover:border-surface-borderLight transition-colors"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-gray-500" />
            <span>Search compliance rules, clients, policy chunks...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-surface border border-surface-border text-[10px] font-mono text-gray-400">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right System Indicators */}
      <div className="flex items-center gap-3">
        {/* Real-time Status */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Active Corpus: 37 Chunks</span>
        </div>

        {/* Live Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-raised border border-surface-border text-xs text-gray-300">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-mono text-[11px]">Online</span>
        </div>

        {/* Notification Bell */}
        <button className="p-2 rounded-lg bg-surface-raised border border-surface-border text-gray-400 hover:text-white transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-400" />
        </button>
      </div>
    </header>
  );
};
