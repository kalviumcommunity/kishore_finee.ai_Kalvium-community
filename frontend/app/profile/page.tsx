"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Mail,
  ShieldCheck,
  Building,
  Key,
  LogOut,
  CheckCircle2,
  Lock,
  History,
  Shield,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAdmin, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  const getInitials = (name?: string) => {
    if (!name) return "AD";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background text-gray-100 p-6 sm:p-8 max-w-4xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="space-y-1 border-b border-surface-border pb-6">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Advisor Identity &amp; Session</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">
          User Profile
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 font-sans">
          Your authenticated credentials, session parameters, and compliance authorization level.
        </p>
      </div>

      {/* Main Profile Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-surface border border-surface-border shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500 text-black font-extrabold text-xl flex items-center justify-center shrink-0 shadow-lg">
              {getInitials(user?.name)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white font-sans">{user?.name || "Advisor User"}</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {isAdmin ? "ADMINISTRATOR" : "ADVISOR"}
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono mt-0.5">{user?.email || "No email available"}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="px-4 py-2.5 rounded-xl bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer self-start sm:self-auto"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out Session</span>
          </button>
        </div>

        {/* Credentials & Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <Mail className="w-3.5 h-3.5 text-emerald-400" />
              <span>Verified Email</span>
            </div>
            <p className="text-sm font-semibold text-white font-mono">{user?.email || "—"}</p>
          </div>

          <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <Building className="w-3.5 h-3.5 text-emerald-400" />
              <span>Department / Desk</span>
            </div>
            <p className="text-sm font-semibold text-white">
              {user?.department || (isAdmin ? "Compliance Administration" : "Wealth Management")}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <Key className="w-3.5 h-3.5 text-emerald-400" />
              <span>Authentication Provider</span>
            </div>
            <p className="text-sm font-semibold text-white font-mono">
              {isAdmin ? "Local System Key" : "Google Identity Services (OAuth 2.0)"}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Guardrail Protection</span>
            </div>
            <p className="text-sm font-semibold text-emerald-400 font-mono">
              Enforced (0.720 Threshold)
            </p>
          </div>
        </div>
      </div>

      {/* Security & Data Sovereignty Card */}
      <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          Fiduciary Data Sovereignty
        </h3>
        <p className="text-xs text-gray-300 leading-relaxed font-sans">
          Your session queries and retrieved citations are isolated within your institution&apos;s workspace. FINEE.ai enforces a strict zero-model-training policy. No queries are used to fine-tune external language models.
        </p>
        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 pt-1">
          <CheckCircle2 className="w-4 h-4" />
          <span>SOC-2 Type II Aligned &amp; AES-256 Encrypted</span>
        </div>
      </div>
    </div>
  );
}
