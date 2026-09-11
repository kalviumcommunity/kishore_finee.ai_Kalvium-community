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
  Pin,
  Clock,
  Search,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ragApi } from "@/services/ragApi";
import { DocumentRecord, ConversationSummary } from "@/types";

export default function UserDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [quickQuery, setQuickQuery] = useState("");

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await ragApi.getDocuments();
        setDocuments(res || []);
      } catch (err) {
        console.warn("Could not load documents:", err);
      } finally {
        setLoadingDocs(false);
      }
    };

    const fetchConvs = async () => {
      try {
        const res = await ragApi.getConversations();
        setConversations(res || []);
      } catch (err) {
        console.warn("Could not load conversations:", err);
      } finally {
        setLoadingConvs(false);
      }
    };

    fetchDocs();
    fetchConvs();
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

  const pinnedConversations = conversations.filter((c) => c.is_pinned);
  const recentConversations = conversations.slice(0, 5);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background text-gray-100 p-6 sm:p-8 max-w-6xl mx-auto w-full space-y-8">
      {/* Header Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-6">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Fiduciary Knowledge Control</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">
            {getGreeting()}, {user?.name || "Advisor"}
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 font-sans">
            Ask compliance and financial policy questions grounded in approved institutional knowledge.
          </p>
        </div>

        <Link
          href="/chatask"
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-md self-start sm:self-auto cursor-pointer"
        >
          <MessageSquare className="w-4 h-4" />
          <span>New Consultation</span>
        </Link>
      </div>

      {/* Real Metrics Summary Cards (NO MOCK DATA) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-1">
          <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
            <span>Approved Policies</span>
            <FileText className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">
            {loadingDocs ? "—" : documents.length}
          </p>
          <p className="text-[10px] text-gray-500">Active in Vector Store</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-1">
          <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
            <span>Consultations</span>
            <History className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">
            {loadingConvs ? "—" : conversations.length}
          </p>
          <p className="text-[10px] text-gray-500">Persisted in MongoDB</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-1">
          <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
            <span>Pinned Threads</span>
            <Pin className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">
            {loadingConvs ? "—" : pinnedConversations.length}
          </p>
          <p className="text-[10px] text-gray-500">Priority References</p>
        </div>

        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-1">
          <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
            <span>Guardrail Gate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400 font-mono">0.720</p>
          <p className="text-[10px] text-gray-500">Cosine Threshold</p>
        </div>
      </div>

      {/* Dominant Ask FINEE Search Box */}
      <div className="p-6 sm:p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl relative overflow-hidden space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
            <Sparkles className="w-4 h-4" />
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
          <span className="text-gray-500 font-mono">Quick Inquiries:</span>
          <button
            onClick={() => router.push(`/chatask?q=What+is+the+maximum+allowable+advisory+fee%3F`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            Advisory Fee Limits
          </button>
          <button
            onClick={() => router.push(`/chatask?q=What+are+the+annual+KYC+and+suitability+refresh+rules%3F`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            Suitability &amp; KYC Refresh
          </button>
          <button
            onClick={() => router.push(`/chatask?q=What+are+the+mandatory+AML+reporting+thresholds%3F`)}
            className="px-2.5 py-1 rounded-lg bg-surface-raised hover:bg-surface-hover text-gray-300 hover:text-white border border-surface-border transition-colors cursor-pointer"
          >
            AML Thresholds
          </button>
        </div>
      </div>

      {/* Grid: Consultations & Approved Policies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent & Pinned Consultations */}
        <div className="p-5 rounded-2xl bg-surface border border-surface-border space-y-4 shadow-lg flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
                <History className="w-4 h-4 text-emerald-400" />
                Recent Consultations
              </h3>
              <Link
                href="/chatask"
                className="text-[11px] text-emerald-400 hover:underline font-mono flex items-center gap-1"
              >
                <span>View in Chat</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-2">
              {loadingConvs ? (
                <p className="text-xs text-gray-500 py-6 text-center">Loading consultations...</p>
              ) : recentConversations.length === 0 ? (
                <div className="p-6 rounded-xl bg-surface-raised/40 border border-surface-border text-center space-y-2">
                  <MessageSquare className="w-8 h-8 text-gray-600 mx-auto" />
                  <p className="text-xs text-gray-400">No consultation history yet.</p>
                  <p className="text-[11px] text-gray-500">
                    Ask a compliance question to create your first persistent session.
                  </p>
                </div>
              ) : (
                recentConversations.map((conv) => (
                  <Link
                    key={conv.id}
                    href={`/chatask?id=${conv.id}`}
                    className="p-3 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border flex items-center justify-between transition-colors group block"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="flex items-center gap-2">
                        {conv.is_pinned && <Pin className="w-3 h-3 text-amber-400 shrink-0" />}
                        <p className="text-xs font-medium text-white truncate group-hover:text-emerald-400 transition-colors">
                          {conv.title || "Untitled Consultation"}
                        </p>
                      </div>
                      <p className="text-[10px] text-gray-400 font-mono mt-0.5">
                        {conv.message_count} messages ·{" "}
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-emerald-400 shrink-0" />
                  </Link>
                ))
              )}
            </div>
          </div>

          <Link
            href="/chatask"
            className="w-full py-2.5 px-4 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border text-center text-xs font-semibold text-white transition-colors block cursor-pointer mt-2"
          >
            Open Chat Studio &rarr;
          </Link>
        </div>

        {/* Approved Compliance Documents */}
        <div className="p-5 rounded-2xl bg-surface border border-surface-border space-y-4 shadow-lg flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                Approved Compliance Policies
              </h3>
              <Link
                href="/sources"
                className="text-[11px] text-emerald-400 hover:underline font-mono flex items-center gap-1"
              >
                <span>Browse All</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-2">
              {loadingDocs ? (
                <p className="text-xs text-gray-500 py-6 text-center">Loading policies...</p>
              ) : documents.length === 0 ? (
                <div className="p-6 rounded-xl bg-surface-raised/40 border border-surface-border text-center space-y-2">
                  <FileText className="w-8 h-8 text-gray-600 mx-auto" />
                  <p className="text-xs text-gray-400">No compliance policies uploaded yet.</p>
                  <p className="text-[11px] text-gray-500">
                    Administrator approval is required to add new policy manuals.
                  </p>
                </div>
              ) : (
                documents.slice(0, 5).map((doc) => (
                  <div
                    key={doc.document_id}
                    className="p-3 rounded-xl bg-surface-raised border border-surface-border flex items-center justify-between"
                  >
                    <div className="min-w-0 pr-2">
                      <p className="text-xs font-medium text-white truncate">{doc.original_filename}</p>
                      <p className="text-[10px] text-gray-400 font-mono">
                        {doc.metadata?.document_type || "Policy"} · v{doc.metadata?.version || "1.0"} · {doc.chunks_indexed || doc.chunks_created || 0} chunks
                      </p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 shrink-0">
                      Approved
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <Link
            href="/sources"
            className="w-full py-2.5 px-4 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border text-center text-xs font-semibold text-white transition-colors block cursor-pointer mt-2"
          >
            View Knowledge Corpus &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
