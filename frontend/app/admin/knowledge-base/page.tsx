"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Search,
  Cpu,
  Layers,
  ShieldCheck,
  Zap,
  Play,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Sliders,
  FileText,
  Activity,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { KnowledgeBaseData, TestRetrievalResult } from "@/types";

export default function KnowledgeBaseInfrastructurePage() {
  const [data, setData] = useState<KnowledgeBaseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchChunkQuery, setSearchChunkQuery] = useState("");

  // Test Retrieval Console State
  const [testQuery, setTestQuery] = useState("");
  const [topK, setTopK] = useState(4);
  const [useReranker, setUseReranker] = useState(true);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<TestRetrievalResult | null>(null);

  const fetchKnowledgeBase = async (query?: string) => {
    try {
      setLoading(true);
      const res = await ragApi.getKnowledgeBaseMetrics(query);
      setData(res);
    } catch (err) {
      console.error("Failed to load knowledge base data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledgeBase();
  }, []);

  const handleTestRetrieval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testQuery.trim()) return;

    setTestLoading(true);
    try {
      const res = await ragApi.testRetrieval({
        query: testQuery.trim(),
        top_k: topK,
        use_reranker: useReranker,
      });
      setTestResult(res);
    } catch (err) {
      console.error("Test retrieval failed:", err);
    } finally {
      setTestLoading(false);
    }
  };

  const metrics = data?.metrics;
  const health = data?.corpus_health;

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Knowledge Base Infrastructure"
        subtitle="ChromaDB Vector Store • Pipeline Health • Interactive Retrieval Console"
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Policies"
            value={metrics?.total_documents ?? 0}
            subtext="Compliance grounded"
            icon={<FileText className="w-4 h-4 text-emerald-400" />}
            accentColor="emerald"
            badge="Live"
          />
          <StatCard
            label="Vector Chunks"
            value={metrics?.total_chunks ?? 0}
            subtext="ChromaDB HNSW space"
            icon={<Database className="w-4 h-4 text-blue-400" />}
            accentColor="blue"
          />
          <StatCard
            label="Retrieval Readiness"
            value={`${health?.readiness_pct ?? 0}%`}
            subtext="Cosine Guardrail Enforced"
            icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
            accentColor="emerald"
          />
          <StatCard
            label="Index Storage"
            value={`${metrics?.storage_size_kb ?? 0} KB`}
            subtext="text-embedding-3-small (1536d)"
            icon={<Cpu className="w-4 h-4 text-purple-400" />}
            accentColor="purple"
          />
        </div>

        {/* Knowledge Processing Pipeline Horizontal Visual */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              Live Knowledge Processing Pipeline
            </h3>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
              All 5 Stages Operational
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-1">
            {data?.pipeline_stages ? (
              data.pipeline_stages.map((st, i) => (
                <div
                  key={i}
                  className="p-3.5 rounded-xl bg-surface-raised border border-surface-border space-y-2 hover:border-surface-borderLight transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white truncate">{st.name}</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  </div>
                  <div className="space-y-1 text-[11px] font-mono text-gray-400">
                    <div className="flex justify-between">
                      <span>Throughput:</span>
                      <span className="text-gray-200">{st.throughput}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Latency:</span>
                      <span className="text-emerald-400 font-medium">{st.latency}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500">Pipeline telemetry active.</p>
            )}
          </div>
        </div>

        {/* Interactive Test Retrieval Console */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-lg">
          <div className="border-b border-surface-border pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-emerald-400" />
                Interactive Retrieval Test Console
              </h3>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                Execute dry-run similarity searches against active vector store & inspect guardrail decisions
              </p>
            </div>
            <span className="text-xs font-mono text-gray-400 bg-surface-raised px-2.5 py-1 rounded border border-surface-border">
              Model: text-embedding-3-small
            </span>
          </div>

          {/* Test Controls Form */}
          <form onSubmit={handleTestRetrieval} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
              <div className="md:col-span-8 space-y-1">
                <label className="text-xs font-medium text-gray-300">Test Query String</label>
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="Enter test compliance query..."
                  className="w-full bg-surface-raised border border-surface-border rounded-lg px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors font-sans"
                />
              </div>

              <div className="md:col-span-2 space-y-1">
                <label className="text-xs font-medium text-gray-300">Top-K Chunks ({topK})</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full accent-emerald-500 mt-2"
                />
              </div>

              <div className="md:col-span-2 flex items-end">
                <button
                  type="submit"
                  disabled={testLoading}
                  className="w-full py-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-raised disabled:text-gray-600 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors shadow-md"
                >
                  {testLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Test Retrieval</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {/* Test Retrieval Results View */}
          {testResult && (
            <div className="pt-4 border-t border-surface-border space-y-4">
              <div className="flex items-center justify-between bg-surface-raised p-3.5 rounded-xl border border-surface-border">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-white">Evaluation Outcome:</span>
                  <StatusBadge status={testResult.status} />
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span>
                    Top Score:{" "}
                    <span className="text-emerald-400 font-bold">
                      {testResult.top_score ? testResult.top_score.toFixed(4) : "0.0000"}
                    </span>
                  </span>
                  <span>
                    Supporting:{" "}
                    <span className="text-gray-200 font-bold">{testResult.supporting_chunks_count}</span>
                  </span>
                  <span>
                    Latency:{" "}
                    <span className="text-emerald-400 font-bold">{testResult.latency_ms}ms</span>
                  </span>
                </div>
              </div>

              {/* Chunks List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {testResult.chunks && testResult.chunks.length > 0 ? (
                  testResult.chunks.map((c, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-surface-raised/70 border border-surface-border space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between border-b border-surface-border/60 pb-2">
                        <span className="font-mono text-emerald-400 font-bold">Rank #{c.rank}</span>
                        <span className="font-mono text-xs text-emerald-400 font-bold">
                          Score: {(c.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="font-semibold text-white truncate">{c.source}</p>
                      <p className="text-gray-300 line-clamp-3 leading-relaxed bg-surface p-2.5 rounded border border-surface-border">
                        "{c.text}"
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 col-span-2 text-center py-4">
                    No matching candidate chunks found.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Explore Knowledge Chunk Explorer Table */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-400" />
                Explore Knowledge Base Chunks ({data?.total_chunks_count || data?.chunks.length || 0})
              </h3>
              <p className="text-xs text-gray-400 font-mono">
                Inspect vector indexed policy chunks from the active ChromaDB store
              </p>
            </div>

            <div className="relative w-full sm:w-72">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
              <input
                type="text"
                value={searchChunkQuery}
                onChange={(e) => {
                  setSearchChunkQuery(e.target.value);
                  fetchKnowledgeBase(e.target.value);
                }}
                placeholder="Search indexed chunk text..."
                className="w-full bg-surface-raised border border-surface-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-surface-border text-gray-400 font-mono">
                  <th className="pb-2.5 font-medium">Source Document</th>
                  <th className="pb-2.5 font-medium">Section</th>
                  <th className="pb-2.5 font-medium">Chunk Excerpt</th>
                  <th className="pb-2.5 font-medium">Status</th>
                  <th className="pb-2.5 font-medium">Embedding Model</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/60">
                {data?.chunks && data.chunks.length > 0 ? (
                  data.chunks.slice(0, 15).map((chunk, idx) => (
                    <tr key={chunk.id || idx} className="hover:bg-surface-raised/40 transition-colors">
                      <td className="py-3 font-semibold text-white truncate max-w-[180px]">
                        {chunk.source}
                      </td>
                      <td className="py-3 font-mono text-gray-400 text-[11px]">
                        {chunk.section || "General"}
                      </td>
                      <td className="py-3 text-gray-300 max-w-[320px]">
                        <p className="line-clamp-2 leading-relaxed font-sans">{chunk.text}</p>
                      </td>
                      <td className="py-3">
                        <StatusBadge status={chunk.approval_status || "approved"} size="sm" />
                      </td>
                      <td className="py-3 font-mono text-gray-400 text-[11px]">
                        {chunk.embedding_model || "text-embedding-3-small"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-500">
                      No chunks found in active vector collection.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
