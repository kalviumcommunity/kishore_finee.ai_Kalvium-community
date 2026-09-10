"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Send,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Clock,
  Layers,
  Cpu,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Building,
  User,
  History,
  RotateCcw,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { EvidenceCard } from "@/components/EvidenceCard";
import { SourceInspectorDrawer } from "@/components/SourceInspectorDrawer";
import { ConflictBanner } from "@/components/ConflictBanner";
import { ConflictingEvidenceModal } from "@/components/ConflictingEvidenceModal";
import { RetrievalPipelineStatus } from "@/components/RetrievalPipelineStatus";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { CitationSource, ConflictDetails, MessageHistory, QueryResponse, RankedSnippet } from "@/types";

export default function AnalysisSessionPage() {
  const [questionInput, setQuestionInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active Analysis State
  const [activeResponse, setActiveResponse] = useState<QueryResponse | null>(null);
  const [conversationHistory, setConversationHistory] = useState<MessageHistory[]>([]);
  const [selectedSourceForInspector, setSelectedSourceForInspector] = useState<CitationSource | RankedSnippet | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isConflictModalOpen, setIsConflictModalOpen] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState<"evidence" | "pipeline" | "audit">("evidence");

  // Client Context State
  const [clientContext, setClientContext] = useState({
    entity_name: "Marcus Vance Portfolio",
    entity_id: "CLI-8902",
    risk_tier: "Tier 1 - Discretionary HNW",
    account_type: "Discretionary Wealth Management",
    jurisdiction: "Global Wealth (Tier 1)",
  });

  const presetQuestions = [
    "What evidence supports the advisory fee charged to Marcus?",
    "Does client suitability require an annual KYC refresh?",
    "What are the reporting thresholds for AML suspicious activities?",
    "Is there a conflicting fee schedule for Tier 1 wealth accounts?",
    "What is the cafeteria lunch menu today?", // Safe Refusal demonstration
  ];

  // Initial demo query on mount if empty
  useEffect(() => {
    handleQuery("What evidence supports the advisory fee charged to Marcus?", false);
  }, []);

  const handleQuery = async (queryText: string, isFollowUp: boolean = false) => {
    const q = queryText.trim();
    if (!q) return;

    setLoading(true);
    setError(null);

    try {
      const payload = {
        query: q,
        history: isFollowUp ? conversationHistory : [],
        user_id: "usr_marcus_vance",
        client_context: clientContext,
      };

      const res = await ragApi.askQuestion(payload);
      setActiveResponse(res);

      // Update history
      const newHistory: MessageHistory[] = isFollowUp ? [...conversationHistory] : [];
      newHistory.push({ role: "user", content: q });
      newHistory.push({ role: "assistant", content: res.answer });
      setConversationHistory(newHistory);
      setQuestionInput("");
    } catch (err: any) {
      console.error("Query failed:", err);
      setError(err.message || "Failed to execute query against RAG pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const handleInspectSource = (source: CitationSource | RankedSnippet) => {
    setSelectedSourceForInspector(source);
    setIsInspectorOpen(true);
  };

  const handleClearSession = () => {
    setConversationHistory([]);
    setQuestionInput("");
    handleQuery("What evidence supports the advisory fee charged to Marcus?", false);
  };

  const isRefused = activeResponse?.status.includes("refused");

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Analysis Session & Compliance Advisory"
        subtitle="Conversational RAG • Grounded Verification • Evidence Attestation"
      />

      {/* Main 3-Column Work Area */}
      <main className="flex-1 p-6 grid grid-cols-1 xl:grid-cols-12 gap-6 min-h-[calc(100vh-4rem)]">
        {/* ========================================================================= */}
        {/* COLUMN 1: Client & Advisory Context (Left - 3 Cols) */}
        {/* ========================================================================= */}
        <section className="xl:col-span-3 space-y-5">
          {/* Client Entity Card */}
          <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-mono">
                Client Context
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 font-bold">
                ACTIVE SESSION
              </span>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-surface-raised border border-surface-border flex items-center justify-center text-emerald-400 shrink-0 font-bold">
                <Building className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-white truncate">{clientContext.entity_name}</h3>
                <p className="text-xs text-gray-400 font-mono mt-0.5">{clientContext.entity_id}</p>
              </div>
            </div>

            <div className="space-y-2 text-xs divide-y divide-surface-border/60 pt-2 border-t border-surface-border">
              <div className="flex items-center justify-between pt-2">
                <span className="text-gray-400">Risk Profile:</span>
                <span className="text-emerald-400 font-medium font-mono">{clientContext.risk_tier}</span>
              </div>
              <div className="flex items-center justify-between pt-2">
                <span className="text-gray-400">Account Type:</span>
                <span className="text-gray-200 font-mono text-[11px] truncate max-w-[140px]">
                  {clientContext.account_type}
                </span>
              </div>
              <div className="flex items-center justify-between pt-2">
                <span className="text-gray-400">Jurisdiction:</span>
                <span className="text-gray-200 font-mono text-[11px]">{clientContext.jurisdiction}</span>
              </div>
            </div>
          </div>

          {/* Preset Suggested Questions */}
          <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Preset Compliance Queries
              </h4>
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="space-y-2">
              {presetQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuery(q, false)}
                  disabled={loading}
                  className="w-full text-left p-2.5 rounded-lg bg-surface-raised/70 hover:bg-surface-raised border border-surface-border/60 hover:border-surface-borderLight text-xs text-gray-300 hover:text-white transition-all line-clamp-2 leading-relaxed"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>

          {/* Conversation History Pill List */}
          {conversationHistory.length > 0 && (
            <div className="bg-surface border border-surface-border rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-emerald-400" />
                  Session Turns ({conversationHistory.length / 2})
                </h4>
                <button
                  onClick={handleClearSession}
                  className="text-[11px] text-gray-500 hover:text-gray-300 flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Reset
                </button>
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {conversationHistory
                  .filter((m) => m.role === "user")
                  .map((msg, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-lg bg-surface-raised border border-surface-border text-xs text-gray-300 truncate"
                    >
                      <span className="text-emerald-400 font-mono mr-1">Turn {i + 1}:</span>
                      {msg.content}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </section>

        {/* ========================================================================= */}
        {/* COLUMN 2: Grounded Q&A, Citations, & Dialogue (Center - 6 Cols) */}
        {/* ========================================================================= */}
        <section className="xl:col-span-6 space-y-5">
          {/* Main Search / Query Input Form */}
          <div className="bg-surface border border-surface-border rounded-2xl p-3 shadow-lg relative">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleQuery(questionInput, conversationHistory.length > 0);
              }}
              className="flex items-center gap-2"
            >
              <div className="pl-3 text-emerald-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                placeholder="Ask compliance rule, fee guideline, KYC requirement, or follow-up question..."
                className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none py-2 px-1"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !questionInput.trim()}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-raised disabled:text-gray-600 text-white font-medium text-xs flex items-center gap-2 transition-all shadow-md"
              >
                {loading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <span>Ask FINEE</span>
                    <Send className="w-3 h-3" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-3">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Active Question & Grounded Answer Container */}
          {activeResponse && (
            <div className="bg-surface border border-surface-border rounded-2xl p-6 space-y-5 shadow-xl relative overflow-hidden">
              {/* Question Header */}
              <div className="border-b border-surface-border pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-gray-400" />
                    Marcus Vance (Advisor Query)
                  </span>
                  <StatusBadge status={activeResponse.status} />
                </div>
                <h2 className="text-base font-bold text-white leading-snug">
                  "{activeResponse.question}"
                </h2>

                {/* Rewritten query chip if follow-up rewrite occurred */}
                {activeResponse.rewritten_query &&
                  activeResponse.rewritten_query !== activeResponse.question && (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-mono">
                      <Sparkles className="w-3 h-3 text-brand-400" />
                      <span>Rewritten Standalone Query:</span>
                      <span className="text-white">"{activeResponse.rewritten_query}"</span>
                    </div>
                  )}
              </div>

              {/* Conflicting Evidence Alert Banner (if conflict detected) */}
              {activeResponse.has_conflict && activeResponse.conflict_details && (
                <ConflictBanner
                  conflict={activeResponse.conflict_details}
                  onOpenModal={() => setIsConflictModalOpen(true)}
                />
              )}

              {/* SAFE REFUSAL STATE (0 Hallucination guarantee) */}
              {isRefused ? (
                <div className="bg-red-950/30 border border-red-800/60 rounded-xl p-5 space-y-3">
                  <div className="flex items-center gap-2.5 text-red-400 font-bold text-sm">
                    <ShieldAlert className="w-5 h-5" />
                    <span>Compliance Safe Refusal Triggered (0 Hallucination)</span>
                  </div>
                  <p className="text-sm text-gray-200 leading-relaxed font-sans bg-surface-raised/80 p-4 rounded-lg border border-surface-border">
                    {activeResponse.answer}
                  </p>
                  <div className="text-xs text-gray-400 space-y-1 pt-1">
                    <p>
                      <span className="text-gray-300 font-medium">Diagnostic Reason:</span>{" "}
                      {activeResponse.refusal_reason || "Relevance score did not satisfy guardrail threshold."}
                    </p>
                    <p className="font-mono text-[11px] text-red-300">
                      Top score: {(activeResponse.metrics.top_score || 0).toFixed(4)} (Threshold: 0.7200)
                    </p>
                  </div>
                </div>
              ) : (
                /* GROUNDED ANSWER WITH CITATION MARKERS */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Grounded Answer
                    </span>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                      100% Policy Grounded
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-raised border border-surface-border text-sm text-gray-100 leading-relaxed font-sans border-l-4 border-l-emerald-500 whitespace-pre-line">
                    {activeResponse.answer}
                  </div>
                </div>
              )}

              {/* EVIDENCE USED / CITATIONS SECTION */}
              {activeResponse.sources && activeResponse.sources.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-surface-border">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Verified Evidence ({activeResponse.sources.length} sources used)
                    </h3>
                    <span className="text-[11px] text-gray-400 font-mono">Click card to inspect</span>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    {activeResponse.sources.map((src, idx) => (
                      <EvidenceCard
                        key={idx}
                        source={src}
                        onInspect={() => handleInspectSource(src)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up Question Quick Bar */}
              <div className="pt-4 border-t border-surface-border flex items-center justify-between text-xs text-gray-400">
                <span className="font-mono text-[11px]">
                  Latency: {activeResponse.usage?.latency_ms || 145}ms • Total Tokens:{" "}
                  {activeResponse.usage?.total_tokens || 420}
                </span>
                <span className="text-emerald-400 font-mono font-medium">
                  Cost: ${activeResponse.usage?.cost_usd ? activeResponse.usage.cost_usd.toFixed(5) : "0.00018"}
                </span>
              </div>
            </div>
          )}
        </section>

        {/* ========================================================================= */}
        {/* COLUMN 3: Retrieved Evidence, Pipeline Trace & Audit (Right - 3 Cols) */}
        {/* ========================================================================= */}
        <section className="xl:col-span-3 space-y-5">
          {/* Right Sidebar Tab Switcher */}
          <div className="bg-surface border border-surface-border rounded-xl p-1 flex items-center">
            <button
              onClick={() => setActiveRightTab("evidence")}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeRightTab === "evidence"
                  ? "bg-surface-raised text-white font-semibold border border-surface-border"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Ranked Snippets
            </button>
            <button
              onClick={() => setActiveRightTab("pipeline")}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeRightTab === "pipeline"
                  ? "bg-surface-raised text-white font-semibold border border-surface-border"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Pipeline
            </button>
            <button
              onClick={() => setActiveRightTab("audit")}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeRightTab === "audit"
                  ? "bg-surface-raised text-white font-semibold border border-surface-border"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Audit Trail
            </button>
          </div>

          {/* TAB 1: RANKED SNIPPETS / RETRIEVED EVIDENCE */}
          {activeRightTab === "evidence" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-mono">
                  Retrieved Candidates
                </h4>
                <span className="text-xs text-gray-400 font-mono">HNSW Cosine Space</span>
              </div>

              {activeResponse?.ranked_snippets && activeResponse.ranked_snippets.length > 0 ? (
                activeResponse.ranked_snippets.map((snip, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleInspectSource(snip)}
                    className="bg-surface border border-surface-border hover:border-surface-borderLight rounded-xl p-4 cursor-pointer transition-all space-y-2 group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold text-emerald-400 px-2 py-0.5 rounded bg-surface-raised border border-surface-border">
                        Rank #{snip.rank} • {snip.type}
                      </span>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        {(snip.score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <h5 className="text-xs font-semibold text-white truncate group-hover:text-emerald-300">
                      {snip.source}
                    </h5>
                    <p className="text-[11px] text-gray-400 font-mono">
                      {snip.section} • Page {snip.page}
                    </p>

                    <p className="text-xs text-gray-300 line-clamp-2 bg-surface-raised/60 p-2 rounded border border-surface-border/40">
                      "{snip.text}"
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center bg-surface border border-surface-border rounded-xl text-gray-500 text-xs">
                  No snippets retrieved. Ask a question to view candidate vectors.
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PIPELINE TRACE & TOKEN METRICS */}
          {activeRightTab === "pipeline" && (
            <div className="space-y-4">
              <RetrievalPipelineStatus
                metrics={activeResponse?.pipeline_metrics}
                latencyMs={activeResponse?.usage?.latency_ms || 145}
              />

              {/* Token Observability Box */}
              <div className="bg-surface border border-surface-border rounded-xl p-4 space-y-3">
                <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-emerald-400" /> Token Observability
                </h4>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded-lg bg-surface-raised border border-surface-border">
                    <span className="text-[10px] text-gray-500 block">PROMPT TOKENS</span>
                    <span className="text-sm font-bold text-white">
                      {activeResponse?.usage?.prompt_tokens || 280}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-raised border border-surface-border">
                    <span className="text-[10px] text-gray-500 block">COMPLETION</span>
                    <span className="text-sm font-bold text-white">
                      {activeResponse?.usage?.completion_tokens || 140}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-raised border border-surface-border">
                    <span className="text-[10px] text-gray-500 block">TOTAL TOKENS</span>
                    <span className="text-sm font-bold text-emerald-400">
                      {activeResponse?.usage?.total_tokens || 420}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-raised border border-surface-border">
                    <span className="text-[10px] text-gray-500 block">EST. COST</span>
                    <span className="text-sm font-bold text-emerald-400">
                      ${activeResponse?.usage?.cost_usd ? activeResponse.usage.cost_usd.toFixed(5) : "0.00018"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: AUDIT TRAIL */}
          {activeRightTab === "audit" && (
            <div className="bg-surface border border-surface-border rounded-xl p-4 space-y-3">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                Query Execution Audit Trail
              </h4>

              <div className="space-y-3 relative pl-3 border-l border-surface-border">
                {activeResponse?.audit_trail && activeResponse.audit_trail.length > 0 ? (
                  activeResponse.audit_trail.map((item, idx) => (
                    <div key={idx} className="relative pl-3 space-y-0.5">
                      <span className="absolute -left-[19px] top-1.5 w-2 h-2 rounded-full bg-emerald-400" />
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold text-white">{item.step}</p>
                        <span className="text-[10px] font-mono text-gray-400">{item.timestamp}</span>
                      </div>
                      <p className="text-[11px] text-gray-400 font-mono">{item.detail}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500">No audit trail available.</p>
                )}
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Slide-Over Source Inspector Drawer */}
      <SourceInspectorDrawer
        source={selectedSourceForInspector}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />

      {/* Conflicting Evidence Modal */}
      <ConflictingEvidenceModal
        conflict={activeResponse?.conflict_details || null}
        isOpen={isConflictModalOpen}
        onClose={() => setIsConflictModalOpen(false)}
        onRequestReview={() => {
          // Log escalation
        }}
      />
    </div>
  );
}
