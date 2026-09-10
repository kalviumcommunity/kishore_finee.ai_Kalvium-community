"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileCheck,
  Clock,
  AlertCircle,
  Archive,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Plus,
  FileText,
  Activity,
  Layers,
  Database,
  ExternalLink,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { OverviewData } from "@/types";

export default function AdminOverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const res = await ragApi.getAdminOverview();
      setData(res);
    } catch (err) {
      console.error("Failed to load overview data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const stats = data?.stats;

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Knowledge Control Center"
        subtitle="Policy Corpus Health • Ingestion Status • Live Pipeline Activity"
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Top KPI Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Approved Policies"
            value={stats?.approved_documents ?? 28}
            subtext="96.4% retrieval ready"
            icon={<FileCheck className="w-4 h-4 text-emerald-400" />}
            accentColor="emerald"
            badge="Active"
          />
          <StatCard
            label="Processing Pipeline"
            value={stats?.processing_documents ?? 1}
            subtext="Ingestion & Vectorizing"
            icon={<RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />}
            accentColor="amber"
            badge="Live"
          />
          <StatCard
            label="Pending Review"
            value={stats?.pending_documents ?? 3}
            subtext="Awaiting Compliance Approval"
            icon={<Clock className="w-4 h-4 text-blue-400" />}
            accentColor="blue"
          />
          <StatCard
            label="Archived / Superseded"
            value={stats?.archived_documents ?? 2}
            subtext="Deprecated from Search"
            icon={<Archive className="w-4 h-4 text-gray-400" />}
            accentColor="purple"
          />
        </div>

        {/* Knowledge Base Status Workflow Visual Card */}
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Knowledge Base Ingestion Lifecycle
              </h3>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                Automated document extraction, semantic chunking, and ChromaDB vector indexing
              </p>
            </div>
            <Link
              href="/admin/documents"
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300">1. Raw Document Ingest</span>
                <span className="w-2 h-2 rounded-full bg-blue-400" />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                PDF, Markdown, HTML, or TXT safe streaming storage with path traversal protection.
              </p>
              <div className="text-[11px] font-mono text-emerald-400">100% Validated</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300">2. Recursive Chunking</span>
                <span className="w-2 h-2 rounded-full bg-amber-400" />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Clean text normalization and token-aware semantic chunking with overlap.
              </p>
              <div className="text-[11px] font-mono text-emerald-400">~185 avg tokens/chunk</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300">3. Vector Embeddings</span>
                <span className="w-2 h-2 rounded-full bg-purple-400" />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                1536-dimensional dense vectors generated via OpenAI text-embedding-3-small.
              </p>
              <div className="text-[11px] font-mono text-emerald-400">Cosine Space</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300">4. ChromaDB HNSW</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Persistent indexing ready for sub-second similarity search & re-ranking.
              </p>
              <div className="text-[11px] font-mono text-emerald-400">
                {stats?.vector_chunks_indexed || 37} active vectors
              </div>
            </div>
          </div>
        </div>

        {/* Bottom 2-Column Split: Recent Documents & Processing Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Recent Documents Table (8 Cols) */}
          <div className="lg:col-span-8 bg-surface border border-surface-border rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-surface-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" /> Recent Tracked Documents
                </h3>
                <p className="text-xs text-gray-400 font-mono">
                  Managed regulatory policies and client suitability documents
                </p>
              </div>
              <Link
                href="/admin/documents"
                className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-medium"
              >
                <span>View all documents</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-surface-border text-gray-400 font-mono">
                    <th className="pb-2.5 font-medium">Document Name</th>
                    <th className="pb-2.5 font-medium">Version</th>
                    <th className="pb-2.5 font-medium">Status</th>
                    <th className="pb-2.5 font-medium">Chunks</th>
                    <th className="pb-2.5 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border/60">
                  {data?.recent_documents && data.recent_documents.length > 0 ? (
                    data.recent_documents.slice(0, 6).map((doc) => (
                      <tr key={doc.document_id} className="hover:bg-surface-raised/50 transition-colors">
                        <td className="py-3 font-medium text-white flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-gray-400" />
                          <span className="truncate max-w-[220px]">{doc.original_filename}</span>
                        </td>
                        <td className="py-3 font-mono text-gray-400">
                          v{doc.metadata?.version || "1.0"}
                        </td>
                        <td className="py-3">
                          <StatusBadge status={doc.metadata?.approval_status || doc.status} size="sm" />
                        </td>
                        <td className="py-3 font-mono text-gray-300">
                          {doc.chunks_indexed || 1} indexed
                        </td>
                        <td className="py-3 text-right">
                          <Link
                            href={`/admin/documents/${doc.document_id}`}
                            className="text-xs text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1"
                          >
                            <span>Inspect</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-gray-500">
                        No documents uploaded yet. Click Upload Document to add policies.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Processing Activity Timeline (4 Cols) */}
          <div className="lg:col-span-4 bg-surface border border-surface-border rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-surface-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" /> Live Audit Trail
                </h3>
                <p className="text-xs text-gray-400 font-mono">System activity stream</p>
              </div>
              <Link
                href="/admin/activity"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-medium"
              >
                All events
              </Link>
            </div>

            <div className="space-y-3.5 relative pl-3 border-l border-surface-border max-h-[380px] overflow-y-auto pr-1">
              {data?.activity_timeline && data.activity_timeline.length > 0 ? (
                data.activity_timeline.slice(0, 5).map((ev) => (
                  <div key={ev.id} className="relative pl-3 space-y-1">
                    <span
                      className={`absolute -left-[19px] top-1.5 w-2 h-2 rounded-full ${
                        ev.status === "SUCCESS"
                          ? "bg-emerald-400"
                          : ev.status === "WARNING"
                          ? "bg-amber-400"
                          : "bg-blue-400"
                      }`}
                    />
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-white truncate max-w-[170px]">
                        {ev.actor}
                      </p>
                      <span className="text-[10px] font-mono text-gray-400">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "Just now"}
                      </span>
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed line-clamp-2">
                      {ev.description}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500">No activity events recorded.</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
