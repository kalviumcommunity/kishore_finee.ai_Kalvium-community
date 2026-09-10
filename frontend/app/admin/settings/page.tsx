"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  Shield,
  ShieldCheck,
  Cpu,
  Database,
  Sliders,
  RefreshCw,
  Lock,
  CheckCircle,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { ragApi } from "@/services/ragApi";

export default function SystemSettingsPage() {
  const [settings, setSettings] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const s = await ragApi.getSystemSettings();
        setSettings(s);
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="System Settings & Guardrail Configuration"
        subtitle="Retrieval Thresholds • Active LLM / Embedding Models • Context Budgets"
      />

      <main className="flex-1 p-6 space-y-6 max-w-5xl w-full mx-auto">
        {/* Header */}
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Active Engine Parameters</h2>
          <p className="text-xs text-gray-400 font-mono">
            Environment-level parameters governing vector similarity, guardrails, and context injection
          </p>
        </div>

        {/* Guardrail Thresholds Card */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Compliance Retrieval Guardrails
              </h3>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                Pre-LLM validation rejecting weak context before token generation
              </p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-800/60">
              STATUS: ENFORCED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1">
              <span className="text-[10px] text-gray-400 font-mono block">MIN_TOP_SCORE</span>
              <span className="text-lg font-bold font-mono text-emerald-400">
                {settings?.MIN_TOP_SCORE ?? 0.72}
              </span>
              <p className="text-[11px] text-gray-400 leading-tight">
                Minimum cosine similarity score required for top candidate chunk.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1">
              <span className="text-[10px] text-gray-400 font-mono block">MIN_SUPPORTING_CHUNKS</span>
              <span className="text-lg font-bold font-mono text-white">
                {settings?.MIN_SUPPORTING_CHUNKS ?? 1}
              </span>
              <p className="text-[11px] text-gray-400 leading-tight">
                Minimum chunks that must exceed the score threshold.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-1">
              <span className="text-[10px] text-gray-400 font-mono block">RETRIEVAL_TOP_K</span>
              <span className="text-lg font-bold font-mono text-white">
                {settings?.RETRIEVAL_TOP_K ?? 4}
              </span>
              <p className="text-[11px] text-gray-400 leading-tight">
                Default candidates retrieved before re-ranking and guardrail evaluation.
              </p>
            </div>
          </div>
        </div>

        {/* Model Infrastructure Card */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                Model & Vector DB Configuration
              </h3>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                Dense embedding architecture and generation engines
              </p>
            </div>
            <span className="text-xs font-mono text-gray-400 bg-surface-raised px-2.5 py-1 rounded border border-surface-border">
              Environment: {settings?.APP_ENV || "development"}
            </span>
          </div>

          <div className="divide-y divide-surface-border text-xs">
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">Embedding Model</p>
                <p className="text-gray-400 font-mono text-[11px]">Dense vector representation engine</p>
              </div>
              <span className="font-mono text-emerald-400 font-bold bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/40">
                {settings?.EMBEDDING_MODEL || "text-embedding-3-small (1536d)"}
              </span>
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">Generation Chat Model</p>
                <p className="text-gray-400 font-mono text-[11px]">Compliance grounded synthesizer</p>
              </div>
              <span className="font-mono text-gray-200 bg-surface-raised px-2.5 py-1 rounded border border-surface-border">
                {settings?.CHAT_MODEL || "gpt-4o-mini / llama-3.3-70b"}
              </span>
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">Vector Storage Backend</p>
                <p className="text-gray-400 font-mono text-[11px]">HNSW cosine similarity collection</p>
              </div>
              <span className="font-mono text-gray-200 bg-surface-raised px-2.5 py-1 rounded border border-surface-border">
                ChromaDB (Persistent Engine)
              </span>
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">Re-ranking Engine</p>
                <p className="text-gray-400 font-mono text-[11px]">Cross-encoder candidate scoring</p>
              </div>
              <span className="font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/40">
                ENABLED (Top-3 Selection)
              </span>
            </div>
          </div>
        </div>

        {/* Safe Refusal Message Card */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            Standardized Compliance Refusal Message
          </h3>
          <p className="text-xs text-gray-400 font-mono">
            Returned verbatim when guardrails detect insufficient evidence
          </p>
          <div className="p-3.5 rounded-lg bg-surface-raised border border-surface-border text-xs text-gray-300 font-sans border-l-2 border-l-amber-500">
            "{settings?.SAFE_REFUSAL_MESSAGE || "I don't have enough reliable evidence in the approved knowledge base to answer that question."}"
          </div>
        </div>
      </main>
    </div>
  );
}
