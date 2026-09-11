"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  ShieldCheck,
  FileText,
  Sparkles,
  ArrowRight,
  BookOpen,
  History,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ragApi } from "@/services/ragApi";
import { DocumentRecord } from "@/types";

export default function UserDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [quickQuery, setQuickQuery] = useState("");

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await ragApi.getDocuments();
        setDocuments(res || []);
      } catch (err) {
        console.warn("Could not load documents:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  const handleQuickSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickQuery.trim()) return;
    router.push(`/chatask?q=${encodeURIComponent(quickQuery.trim())}`);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background text-gray-100 p-6 sm:p-8 max-w-5xl mx-auto w-full space-y-8">
      {/* Header Greeting */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Fiduciary Knowledge Control</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">
          {getGreeting()}, {user?.name || "Advisor"}
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 max-w-2xl font-sans">
          Your compliance-grounded AI knowledge workspace. Ask questions regarding fee schedules, client suitability, AML requirements, and institutional guidelines.
        </p>
      </div>

      {/* Dominant Ask FINEE Search Box */}
      <div className="p-6 sm:p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl relative overflow-hidden space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
            <MessageSquare className="w-4 h-4" />
            <span>Direct Advisory Intelligence</span>
          </div>
          <span className="text-[10px] font-mono text-gray-500">100% Policy Grounded</span>
        </div>

        <form onSubmit={handleQuickSubmit} className="relative flex items-center">
          <input
            type="text"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder="Ask a financial or compliance question (e.g. fee limits, suitability, AML)..."
            className="w-full bg-surface-raised border border-surface-border focus:border-emerald-500 rounded-2xl pl-5 pr-28 py-4 text-xs sm:text-sm text-white placeholder-gray-500 focus:outline-none transition-colors shadow-inner"
          />
          <button
            type="submit"
            className="absolute right-2.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md cursor-pointer"
          >
            <span>Ask FINEE</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-gray-400">
          <span className="text-gray-500 font-mono">Suggested:</span>
          <button
            onClick={() => router.push(`/chatask`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            Advisory Fee Limits
          </button>
          <button
            onClick={() => router.push(`/chatask`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            Suitability & KYC Refresh
          </button>
          <button
            onClick={() => router.push(`/chatask`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            AML Thresholds
          </button>
        </div>
      </div>

      {/* Grid: Approved Policies & Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Approved Compliance Documents */}
        <div className="p-5 rounded-2xl bg-surface border border-surface-border space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              Approved Compliance Policies
            </h3>
            <Link
              href="/chatask"
              className="text-[11px] text-emerald-400 hover:underline font-mono flex items-center gap-1"
            >
              <span>Search All</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-2.5">
            {loading ? (
              <p className="text-xs text-gray-500 py-4 text-center">Loading policies...</p>
            ) : documents.length === 0 ? (
              <p className="text-xs text-gray-500 py-4 text-center">No compliance policies uploaded yet.</p>
            ) : (
              documents.slice(0, 4).map((doc) => (
                <div
                  key={doc.document_id}
                  className="p-3 rounded-xl bg-surface-raised border border-surface-border flex items-center justify-between"
                >
                  <div className="min-w-0 pr-2">
                    <p className="text-xs font-medium text-white truncate">{doc.original_filename}</p>
                    <p className="text-[10px] text-gray-400 font-mono">
                      {doc.metadata?.approval_status || "Approved"} · v{doc.metadata?.version || "1.0"}
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 shrink-0">
                    Active
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Advisory Session Hub */}
        <div className="p-5 rounded-2xl bg-surface border border-surface-border space-y-4 shadow-lg flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Grounded AI Verification
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed font-sans">
              FINEE synthesizes answers strictly using semantic retrieval against verified compliance chunks. Any question falling outside approved knowledge triggers an automated safe refusal.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Zero Hallucination Fiduciary Guarantee</span>
            </div>
            <p className="text-[11px] text-gray-400 font-mono leading-relaxed">
              Every sentence is tied to exact citations with section and page level attestation.
            </p>
          </div>

          <Link
            href="/chatask"
            className="w-full py-2.5 px-4 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border text-center text-xs font-semibold text-white transition-colors block cursor-pointer"
          >
            Launch Interactive Chat &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
