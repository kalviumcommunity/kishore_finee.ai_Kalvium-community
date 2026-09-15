"use client";

import React, { useState, useEffect } from "react";
import { Search, Bell, ShieldCheck, Sparkles, Terminal, Activity, Wifi, WifiOff } from "lucide-react";
import { ragApi } from "@/services/ragApi";

interface TopbarProps {
  title?: string;
  subtitle?: string;
  onSearchClick?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  title = "FINEE.ai",
  subtitle = "Compliance-Grounded Knowledge Control",
  onSearchClick,
}) => {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const check = async () => {
      const ok = await ragApi.checkBackendHealth();
      setIsOnline(ok);
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-surface/80 backdrop-blur-md border-b border-surface-border sticky top-0 z-20 flex items-center justify-between px-6">
      {/* Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-2 font-sans">
            {title}
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? "bg-emerald-400" : "bg-amber-400"}`} />
          </h1>
          <p className="text-[11px] text-gray-400 font-mono">{subtitle}</p>
        </div>
      </div>

      {/* Center Search Bar */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
        <button
          onClick={onSearchClick}
          className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-xl bg-surface-raised border border-surface-border text-xs text-gray-400 hover:border-surface-borderLight transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-gray-500" />
            <span>Search compliance rules, policies, guidelines...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-surface border border-surface-border text-[10px] font-mono text-gray-400">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right System Indicators */}
      <div className="flex items-center gap-3">
        {/* Live Service Status */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs ${
            isOnline
              ? "bg-surface-raised border-surface-border text-emerald-400"
              : "bg-amber-950/40 border-amber-800/60 text-amber-400"
          }`}
        >
          {isOnline ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-amber-400" />}
          <span className="font-mono text-[11px]">{isOnline ? "Knowledge Service Active" : "Service Connecting..."}</span>
        </div>

        {/* Notification Bell */}
        <button className="p-2 rounded-lg bg-surface-raised border border-surface-border text-gray-400 hover:text-white transition-colors relative cursor-pointer">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-400" />
        </button>
      </div>
    </header>
  );
};
