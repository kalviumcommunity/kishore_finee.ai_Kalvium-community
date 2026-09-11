"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Send,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Clock,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  X,
  ChevronRight,
  ExternalLink,
  MessageSquare,
  Plus,
  HelpCircle,
  RotateCcw,
  ArrowRight,
} from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { ragApi } from "@/services/ragApi";
import { useAuth } from "@/context/AuthContext";
import { CitationSource, ConflictDetails, MessageHistory, QueryResponse, RankedSnippet } from "@/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  response?: QueryResponse;
  status?: string;
  sources?: CitationSource[];
  hasConflict?: boolean;
  conflictDetails?: ConflictDetails;
}

export default function ChatAskPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Evidence Drawer State
  const [selectedSource, setSelectedSource] = useState<CitationSource | RankedSnippet | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Handle Form Submission
  const handleSubmitQuery = async (queryText: string) => {
    const q = queryText.trim();
    if (!q || loading) return;

    setError(null);
    const userTimestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Build rolling history for follow-up conversational RAG
    const historyPayload: MessageHistory[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: q,
      timestamp: userTimestamp,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const response = await ragApi.askQuestion({
        query: q,
        history: historyPayload,
        user_id: user?.user_id,
      });

      const assistantTimestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        role: "assistant",
        content: response.answer,
        timestamp: assistantTimestamp,
        response: response,
        status: response.status,
        sources: response.sources || [],
        hasConflict: response.has_conflict,
        conflictDetails: response.conflict_details,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Query execution failed:", err);
      setError("FINEE could not connect to the knowledge service. Please ensure the backend is running and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmitQuery(inputQuery);
    }
  };

  const handleOpenSourceDrawer = (source: CitationSource | RankedSnippet) => {
    setSelectedSource(source);
    setIsDrawerOpen(true);
  };

  const handleNewConversation = () => {
    setMessages([]);
    setError(null);
    setInputQuery("");
  };

  // Starter suggestion prompts
  const starterPrompts = [
    "What are the approved advisory fee limits for discretionary wealth accounts?",
    "What documentation is required to verify client suitability prior to trading?",
    "What are the mandatory reporting thresholds for AML suspicious activities?",
    "What are the fiduciary obligations regarding advisor conflicts of interest?",
  ];

  return (
    <div className="flex flex-col h-screen bg-background text-gray-100 overflow-hidden">
      {/* Top Header */}
      <header className="h-14 border-b border-surface-border bg-surface/90 backdrop-blur-md px-6 flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-xs font-bold text-white tracking-tight flex items-center gap-2">
              FINEE<span className="text-emerald-400">.ai</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </h1>
            <p className="text-[10px] text-gray-400 font-mono">
              Compliance-Grounded Financial Advisory Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleNewConversation}
            className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-xs text-gray-300 hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-emerald-400" />
            <span>New Chat</span>
          </button>
        </div>
      </header>

      {/* Main Conversational Workspace */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Chat Stream Column */}
        <div className="flex-1 flex flex-col justify-between overflow-hidden relative">
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 space-y-6 max-w-4xl w-full mx-auto">
            {/* Welcome State when empty */}
            {messages.length === 0 && (
              <div className="py-8 sm:py-12 space-y-8 animate-in fade-in duration-300">
                <div className="text-center space-y-3 max-w-xl mx-auto">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <h2 className="text-xl font-bold text-white tracking-tight font-sans">
                    Welcome to FINEE<span className="text-emerald-400">.ai</span>
                  </h2>
                  <p className="text-xs text-gray-400 font-sans leading-relaxed">
                    Ask any financial advisory or compliance question. Responses are strictly grounded in approved institutional guidelines, regulatory rules, and fee schedules.
                  </p>
                </div>

                {/* Example Starter Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto pt-2">
                  {starterPrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSubmitQuery(prompt)}
                      className="p-3.5 rounded-xl bg-surface border border-surface-border hover:border-emerald-500/50 hover:bg-surface-raised transition-all text-left group shadow-sm flex flex-col justify-between space-y-2 cursor-pointer"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-medium text-gray-200 group-hover:text-white leading-snug">
                          "{prompt}"
                        </p>
                        <ArrowRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-emerald-400 shrink-0 transition-colors mt-0.5" />
                      </div>
                      <span className="text-[10px] font-mono text-gray-500 group-hover:text-emerald-400/80">
                        Ask FINEE &rarr;
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Message Stream */}
            {messages.map((msg) => {
              const isUser = msg.role === "user";
              const isRefusal = msg.status && msg.status.includes("refused");

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${isUser ? "justify-end" : "justify-start"} animate-in fade-in duration-200`}
                >
                  {/* Assistant Icon */}
                  {!isUser && (
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`space-y-2.5 max-w-2xl w-full ${isUser ? "items-end flex flex-col" : ""}`}>
                    {/* Message Bubble Header */}
                    <div className="flex items-center gap-2 text-[11px] font-mono text-gray-400">
                      <span className="font-semibold text-gray-300">
                        {isUser ? user?.name || "You" : "FINEE Knowledge Assistant"}
                      </span>
                      <span>•</span>
                      <span>{msg.timestamp}</span>
                      {!isUser && !isRefusal && (
                        <span className="px-1.5 py-0.2 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-[9px] font-bold">
                          Grounded
                        </span>
                      )}
                    </div>

                    {/* Content Box */}
                    {isUser ? (
                      <div className="bg-emerald-600/90 text-white rounded-2xl rounded-tr-none px-4 py-3 text-xs leading-relaxed shadow-md">
                        {msg.content}
                      </div>
                    ) : isRefusal ? (
                      /* Refusal State Card */
                      <div className="w-full bg-surface border border-amber-500/40 rounded-2xl p-4 space-y-3 shadow-lg">
                        <div className="flex items-start gap-2.5 text-amber-400">
                          <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <h4 className="text-xs font-bold uppercase tracking-wider font-mono">
                              Insufficient Evidence in Approved Knowledge Base
                            </h4>
                            <p className="text-xs text-gray-300 leading-relaxed font-sans">
                              {msg.content}
                            </p>
                          </div>
                        </div>

                        <div className="p-3 rounded-xl bg-surface-raised border border-surface-border text-[11px] text-gray-400 space-y-1 font-mono">
                          <p className="text-gray-300 font-semibold">Guardrail Compliance Check:</p>
                          <p>The available evidence did not meet the minimum confidence threshold required for regulatory grounding.</p>
                        </div>

                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => handleSubmitQuery("What are the approved advisory fee limits for wealth accounts?")}
                            className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-xs text-gray-300 hover:text-white transition-colors cursor-pointer"
                          >
                            Try Approved Fee Limits
                          </button>
                        </div>
                      </div>
                    ) : msg.hasConflict ? (
                      /* Conflicting Evidence State Card */
                      <div className="w-full bg-surface border border-amber-500/40 rounded-2xl p-4 space-y-3 shadow-lg">
                        <div className="flex items-start gap-2.5 text-amber-400">
                          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <h4 className="text-xs font-bold uppercase tracking-wider font-mono">
                              Conflicting Evidence Detected
                            </h4>
                            <p className="text-xs text-gray-300 leading-relaxed font-sans">
                              {msg.content}
                            </p>
                          </div>
                        </div>

                        {msg.conflictDetails && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                            <div className="p-3 rounded-xl bg-surface-raised border border-surface-border space-y-1">
                              <span className="text-[10px] font-mono text-amber-400 font-bold block">SOURCE A</span>
                              <p className="font-semibold text-white truncate">{msg.conflictDetails.source_a.title}</p>
                              <p className="text-gray-400 text-[11px] line-clamp-3">"{msg.conflictDetails.source_a.excerpt}"</p>
                            </div>
                            <div className="p-3 rounded-xl bg-surface-raised border border-surface-border space-y-1">
                              <span className="text-[10px] font-mono text-amber-400 font-bold block">SOURCE B</span>
                              <p className="font-semibold text-white truncate">{msg.conflictDetails.source_b.title}</p>
                              <p className="text-gray-400 text-[11px] line-clamp-3">"{msg.conflictDetails.source_b.excerpt}"</p>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      /* Grounded Answer Card */
                      <div className="bg-surface border border-surface-border rounded-2xl rounded-tl-none p-5 text-xs text-gray-200 leading-relaxed shadow-lg space-y-4">
                        <div className="whitespace-pre-wrap font-sans text-xs sm:text-[13px] text-gray-100 leading-relaxed">
                          {msg.content}
                        </div>

                        {/* Sources List Underneath */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="pt-3 border-t border-surface-border space-y-2">
                            <h5 className="text-[10px] font-bold uppercase tracking-wider text-gray-400 font-mono flex items-center gap-1.5">
                              <FileText className="w-3 h-3 text-emerald-400" />
                              Supporting Compliance Sources ({msg.sources.length})
                            </h5>

                            <div className="flex flex-wrap gap-2 pt-1">
                              {msg.sources.map((source, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => handleOpenSourceDrawer(source)}
                                  className="px-2.5 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border hover:border-emerald-500/50 text-[11px] text-gray-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer group shadow-sm"
                                >
                                  <span className="font-mono text-emerald-400 font-bold">
                                    {source.marker || `[${idx + 1}]`}
                                  </span>
                                  <span className="truncate max-w-[200px]">{source.source}</span>
                                  <ChevronRight className="w-3 h-3 text-gray-500 group-hover:text-emerald-400 transition-colors" />
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* User Icon */}
                  {isUser && (
                    <div className="w-8 h-8 rounded-xl bg-surface-raised border border-surface-border text-emerald-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {user?.name
                        ? user.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")
                            .substring(0, 2)
                            .toUpperCase()
                        : "U"}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex gap-3.5 justify-start animate-in fade-in duration-150">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                </div>
                <div className="bg-surface border border-surface-border rounded-2xl rounded-tl-none px-4 py-3 text-xs text-gray-300 flex items-center gap-2.5 shadow-md">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-mono text-[11px]">FINEE is searching the approved knowledge base and verifying evidence...</span>
                </div>
              </div>
            )}

            {/* Network / Connection Error */}
            {error && (
              <div className="p-3.5 rounded-xl bg-red-950/50 border border-red-800 text-xs text-red-300 flex items-center justify-between shadow-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{error}</span>
                </div>
                <button
                  onClick={() => handleSubmitQuery(inputQuery || "What are the approved advisory fee limits for wealth accounts?")}
                  className="px-2.5 py-1 rounded bg-red-900/80 hover:bg-red-800 text-white font-mono text-[10px] transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Sticky Input Bar at Bottom */}
          <div className="p-4 border-t border-surface-border bg-surface/80 backdrop-blur-md">
            <div className="max-w-4xl mx-auto relative flex items-center">
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask FINEE a financial advisory or compliance question (e.g. fee limits, suitability, AML)..."
                disabled={loading}
                className="w-full bg-surface-raised border border-surface-border focus:border-emerald-500 rounded-2xl pl-4 pr-12 py-3.5 text-xs sm:text-sm text-white placeholder-gray-500 focus:outline-none resize-none transition-colors shadow-inner"
              />
              <button
                onClick={() => handleSubmitQuery(inputQuery)}
                disabled={loading || !inputQuery.trim()}
                className="absolute right-2.5 p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-border disabled:text-gray-500 text-white transition-all shadow-md cursor-pointer disabled:cursor-not-allowed"
                title="Send query (Enter)"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-center text-[10px] text-gray-500 font-mono mt-2">
              All responses are generated exclusively from verified institutional and regulatory sources.
            </p>
          </div>
        </div>

        {/* Source Evidence Inspector Drawer (Slides in on demand) */}
        {isDrawerOpen && selectedSource && (
          <div className="w-80 md:w-96 border-l border-surface-border bg-surface flex flex-col h-full z-30 shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-4 border-b border-surface-border flex items-center justify-between bg-surface-raised">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Source Evidence Details
                </h3>
              </div>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-surface transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans">
              {/* Document Identity */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-gray-400 block uppercase">Document Source</span>
                <p className="font-semibold text-white break-words">
                  {selectedSource.source}
                </p>
                {"document_id" in selectedSource && (
                  <p className="text-[10px] font-mono text-gray-400">{selectedSource.document_id}</p>
                )}
              </div>

              {/* Status & Version Pill Grid */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2.5 rounded-xl bg-surface-raised border border-surface-border">
                  <span className="text-[9px] text-gray-500 block uppercase">Approval Status</span>
                  <span className="text-emerald-400 font-bold capitalize">
                    {selectedSource.approval_status || "Approved"}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-raised border border-surface-border">
                  <span className="text-[9px] text-gray-500 block uppercase">Section / Page</span>
                  <span className="text-gray-200">
                    {selectedSource.section || "General"} · P.{selectedSource.page || 1}
                  </span>
                </div>
              </div>

              {/* Grounded Evidence Excerpt */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-gray-400 block uppercase">Verified Text Excerpt</span>
                <div className="p-3.5 rounded-xl bg-surface-raised border border-emerald-500/30 text-gray-200 leading-relaxed font-sans text-xs">
                  "{selectedSource.text}"
                </div>
              </div>

              {/* Relevance Reason */}
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-[11px] text-emerald-300 font-mono space-y-1">
                <span className="font-bold block flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Grounded Evidence Attestation
                </span>
                <p className="text-gray-400">
                  Retrieved and verified from the approved knowledge corpus to support the advisor answer.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
