"use client";

import React from "react";
import Link from "next/link";
import {
  Cpu,
  Layers,
  ShieldCheck,
  Database,
  Search,
  Filter,
  FileCheck2,
  Lock,
  ArrowRight,
  ChevronRight,
  Zap,
  Activity,
  CheckCircle2,
  Sparkles,
  Scale,
  GitBranch,
  TerminalSquare,
  ShieldAlert,
  Server,
  FileText,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function PlatformPage() {
  const architecturalLayers = [
    {
      layer: "Tier 1",
      title: "Document Ingestion & Semantic Chunking",
      subtitle: "Deterministic parsing & institutional preservation",
      icon: FileText,
      color: "from-blue-500/20 to-indigo-500/10",
      borderColor: "border-blue-500/30",
      badgeColor: "bg-blue-950 text-blue-300 border-blue-800",
      description:
        "Institutional compliance PDFs, fee schedules, and regulatory filings are parsed with high-fidelity layout preservation. Complex tables, multi-column clauses, and page offsets are retained without metadata destruction.",
      features: [
        "Structure-preserving PDF layout parsing",
        "Deterministic semantic chunking with overlapping boundaries",
        "Metadata enrichment (Section, Page, Effective Date, Version)",
        "Automated cryptographic checksums for document provenance",
      ],
    },
    {
      layer: "Tier 2",
      title: "Vector Embeddings & Hybrid Chroma Store",
      subtitle: "High-dimensional vector indexing + metadata filtering",
      icon: Database,
      color: "from-emerald-500/20 to-teal-500/10",
      borderColor: "border-emerald-500/30",
      badgeColor: "bg-emerald-950 text-emerald-300 border-emerald-800",
      description:
        "Extracted chunks are embedded into dense vector representations and stored in an indexed Chroma vector database, paired with rich relational metadata for instantaneous filtering by approval state and document type.",
      features: [
        "Dense vector representations for semantic financial context",
        "Chroma vector store with sub-50ms search latency",
        "Active status & version-isolated namespace partitioning",
        "Cosine similarity scoring with dimensional normalization",
      ],
    },
    {
      layer: "Tier 3",
      title: "Fiduciary Guardrails & Relevance Engine",
      subtitle: "Hard threshold filtering (0.720 minimum similarity)",
      icon: ShieldCheck,
      color: "from-amber-500/20 to-yellow-500/10",
      borderColor: "border-amber-500/30",
      badgeColor: "bg-amber-950 text-amber-300 border-amber-800",
      description:
        "Before any query reaches language generation, retrieved chunks are evaluated against a mandatory 0.720 similarity gate. In-flight queries lacking qualifying citations trigger automated safe refusals.",
      features: [
        "Mandatory 0.720 similarity score threshold",
        "Automated refusal engine for out-of-corpus questions",
        "Cross-chunk deduplication and context pruning",
        "Zero speculative extrapolation policy enforcement",
      ],
    },
    {
      layer: "Tier 4",
      title: "Grounded Synthesis & Citation Attestation",
      subtitle: "Constraint-bound language generation with verified sources",
      icon: Sparkles,
      color: "from-purple-500/20 to-pink-500/10",
      borderColor: "border-purple-500/30",
      badgeColor: "bg-purple-950 text-purple-300 border-purple-800",
      description:
        "The language model operates under strict prompt constraints: it synthesizes answers exclusively from passed evidence chunks, tying every statement to explicit citations containing document name and page number.",
      features: [
        "Context-isolated answer generation",
        "Exact citation mapping [Document Name, Page N]",
        "Cleaned response output with zero leaked raw metadata",
        "Institutional tone calibrated for wealth managers and compliance",
      ],
    },
    {
      layer: "Tier 5",
      title: "Persistence, MongoDB Sessions & Audit Logging",
      subtitle: "Real-time state tracking and regulatory compliance records",
      icon: Activity,
      color: "from-cyan-500/20 to-blue-500/10",
      borderColor: "border-cyan-500/30",
      badgeColor: "bg-cyan-950 text-cyan-300 border-cyan-800",
      description:
        "Every advisor interaction, retrieved chunk, similarity score, latency metric, and token count is persisted to MongoDB collections, creating an immutable audit trail for internal compliance review.",
      features: [
        "Persistent chat sessions & conversation pinning",
        "Complete citation provenance logged per query",
        "Token consumption, latency, and refusal telemetry",
        "Role-based access control (Advisors vs Administrators)",
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#06090e] text-gray-100 selection:bg-emerald-500/30 selection:text-emerald-200">
      <PublicNavbar />

      {/* Header Banner */}
      <section className="relative pt-32 pb-16 md:pt-40 md:pb-20 overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <Cpu className="w-3.5 h-3.5" />
            <span>Architecture & Technical Foundation</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-sans max-w-4xl mx-auto leading-tight">
            Built for deterministic precision,{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
              zero hallucination, and full auditability.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto font-sans leading-relaxed">
            FINEE.ai is engineered from the ground up as a closed-loop fiduciary intelligence system. Explore the multi-tiered architecture powering our grounded retrieval and compliance workflows.
          </p>
        </div>
      </section>

      {/* Platform Architecture Flow Diagram */}
      <section className="py-12 border-y border-surface-border bg-[#0a0f1d]/60 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
              System Architecture Flow
            </h2>
            <p className="text-xl font-bold text-white font-sans">
              From Raw PDF to Verifiable Advisory Output
            </p>
          </div>

          {/* Flow Blocks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-2 text-center relative">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center mx-auto">
                <FileText className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-gray-500 uppercase">Input</span>
              <h4 className="text-xs font-bold text-white">Compliance PDFs</h4>
              <p className="text-[11px] text-gray-400">Institutional policy, ADV filings, fee schedules</p>
            </div>

            <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-2 text-center relative">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
                <Search className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-gray-500 uppercase">Retrieval</span>
              <h4 className="text-xs font-bold text-white">Vector Index</h4>
              <p className="text-[11px] text-gray-400">Dense embeddings in Chroma DB</p>
            </div>

            <div className="p-4 rounded-xl bg-surface border border-emerald-500/30 bg-emerald-950/20 space-y-2 text-center relative">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-emerald-400 uppercase">Gate (0.720)</span>
              <h4 className="text-xs font-bold text-white">Relevance Filter</h4>
              <p className="text-[11px] text-gray-400">Discards weak matches; triggers safe refusal</p>
            </div>

            <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-2 text-center relative">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mx-auto">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-gray-500 uppercase">Synthesis</span>
              <h4 className="text-xs font-bold text-white">Contextual LLM</h4>
              <p className="text-[11px] text-gray-400">Evidence-bounded generation + citations</p>
            </div>

            <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-2 text-center relative">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-gray-500 uppercase">Audit</span>
              <h4 className="text-xs font-bold text-white">MongoDB Trail</h4>
              <p className="text-[11px] text-gray-400">Immutable conversation & citation logging</p>
            </div>
          </div>
        </div>
      </section>

      {/* Deep Dive: 5 Architectural Tiers */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-3xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
            Platform Deep Dive
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-white font-sans">
            Every Tier Engineered for Financial Compliance
          </h3>
          <p className="text-xs sm:text-sm text-gray-400">
            Standard RAG systems prioritize generic search. FINEE.ai prioritizes fiduciary reliability, evidence attestation, and deterministic reproducibility.
          </p>
        </div>

        <div className="space-y-6">
          {architecturalLayers.map((layer) => {
            const Icon = layer.icon;
            return (
              <div
                key={layer.layer}
                className="p-6 sm:p-8 rounded-2xl bg-surface border border-surface-border hover:border-surface-borderLight transition-all shadow-xl space-y-6"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-border pb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-surface-raised border border-surface-border flex items-center justify-center text-emerald-400 shrink-0 shadow-inner">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {layer.layer}
                        </span>
                        <span className="text-gray-600">•</span>
                        <span className="text-xs font-mono text-gray-400">{layer.subtitle}</span>
                      </div>
                      <h4 className="text-lg sm:text-xl font-bold text-white font-sans mt-0.5">
                        {layer.title}
                      </h4>
                    </div>
                  </div>

                  <span className={`px-3 py-1 rounded-full text-xs font-mono border self-start md:self-auto ${layer.badgeColor}`}>
                    Active Engine
                  </span>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1 space-y-2">
                    <h5 className="text-xs font-mono uppercase font-bold text-gray-400">
                      Functional Purpose
                    </h5>
                    <p className="text-xs sm:text-sm text-gray-300 leading-relaxed font-sans">
                      {layer.description}
                    </p>
                  </div>

                  <div className="lg:col-span-2 space-y-2">
                    <h5 className="text-xs font-mono uppercase font-bold text-gray-400">
                      Technical Guarantees
                    </h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {layer.features.map((feat, fidx) => (
                        <div
                          key={fidx}
                          className="p-3 rounded-xl bg-surface-raised border border-surface-border/80 flex items-start gap-2.5 text-xs text-gray-300"
                        >
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Technical Specifications Summary */}
      <section className="py-16 border-t border-surface-border bg-[#0a0f1d]/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="text-center space-y-2">
            <h3 className="text-xs font-mono uppercase font-bold text-emerald-400">
              Technical Specifications
            </h3>
            <p className="text-xl sm:text-2xl font-bold text-white font-sans">
              Core System Benchmarks & Architecture Stats
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-surface border border-surface-border text-center space-y-1">
              <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">0.720</span>
              <p className="text-xs font-semibold text-white">Relevance Threshold</p>
              <p className="text-[10px] text-gray-400">Hard cosine similarity gate</p>
            </div>
            <div className="p-5 rounded-2xl bg-surface border border-surface-border text-center space-y-1">
              <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono">&lt; 150ms</span>
              <p className="text-xs font-semibold text-white">Retrieval Latency</p>
              <p className="text-[10px] text-gray-400">Vector search & deduplication</p>
            </div>
            <div className="p-5 rounded-2xl bg-surface border border-surface-border text-center space-y-1">
              <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono">100%</span>
              <p className="text-xs font-semibold text-white">Citation Grounding</p>
              <p className="text-[10px] text-gray-400">Every response page-indexed</p>
            </div>
            <div className="p-5 rounded-2xl bg-surface border border-surface-border text-center space-y-1">
              <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">SOC-2</span>
              <p className="text-xs font-semibold text-white">Security Alignment</p>
              <p className="text-[10px] text-gray-400">Zero model training on user data</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 border-t border-surface-border relative overflow-hidden text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans">
            Ready to Deploy Evidence-Grounded Financial Intelligence?
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
            Experience how FINEE.ai empowers advisors with instant, verified compliance answers.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
            <Link
              href="/signup"
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-emerald-500/25 cursor-pointer"
            >
              <span>Get Started</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              href="/how-it-works"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-surface-raised hover:bg-surface-elevated text-gray-200 hover:text-white border border-surface-border text-sm font-medium flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>See How It Works</span>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
