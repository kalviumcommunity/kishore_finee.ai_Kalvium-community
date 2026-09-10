"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  LayoutDashboard,
  FileText,
  Database,
  History,
  Users,
  Settings,
  Shield,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Analysis Session",
      href: "/chatask",
      icon: MessageSquare,
      badge: "RAG",
    },
    {
      name: "Control Center",
      href: "/admin",
      icon: LayoutDashboard,
    },
    {
      name: "Documents",
      href: "/admin/documents",
      icon: FileText,
      badge: "Upload",
    },
    {
      name: "Knowledge Base",
      href: "/admin/knowledge-base",
      icon: Database,
    },
    {
      name: "Audit Trail",
      href: "/admin/activity",
      icon: History,
    },
    {
      name: "User Monitoring",
      href: "/admin/users",
      icon: Users,
      badge: "Tokens",
    },
    {
      name: "System Settings",
      href: "/admin/settings",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-surface-border flex flex-col justify-between h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-surface-border flex items-center justify-between">
          <Link href="/chatask" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight text-white font-sans">
                  FINEE<span className="text-emerald-400">.ai</span>
                </span>
                <span className="text-[9px] uppercase tracking-wider font-mono font-bold px-1.5 py-0.5 rounded bg-surface-raised border border-surface-border text-emerald-400">
                  v1.0
                </span>
              </div>
              <p className="text-[10px] text-gray-400 uppercase tracking-widest font-mono">
                Knowledge Control
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] uppercase font-bold tracking-wider text-gray-500 font-mono">
            Platform Workspace
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/chatask" && item.href !== "/admin" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? "bg-surface-raised text-white border border-surface-borderLight font-semibold"
                    : "text-gray-400 hover:text-gray-200 hover:bg-surface-raised/60"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive ? "text-emerald-400" : "text-gray-400 group-hover:text-gray-300"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                      isActive
                        ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                        : "bg-surface border-surface-border text-gray-400"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / User Profile & System Health */}
      <div className="p-4 border-t border-surface-border space-y-3">
        {/* Guardrail Status Pill */}
        <div className="p-2.5 rounded-xl bg-surface-raised border border-surface-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-mono text-gray-300">Guardrail Enforced</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-800/60">
            0.720
          </span>
        </div>

        {/* User Card */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-400 text-white font-bold text-xs flex items-center justify-center shrink-0">
              MV
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">Marcus Vance</p>
              <p className="text-[10px] text-gray-400 truncate">Senior Wealth Advisor</p>
            </div>
          </div>
          <Shield className="w-3.5 h-3.5 text-gray-500" />
        </div>
      </div>
    </aside>
  );
};
