"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  FileText,
  Search,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Database,
  History,
  Lock,
  Layers,
  Sparkles,
  Zap,
  TrendingUp,
  Cpu,
  BarChart3,
  ExternalLink,
  Users,
  Clock,
  Pin,
  FileCheck2,
  Scale,
  Eye,
  SlidersHorizontal,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function PublicHomePage() {
  const [activeTab, setActiveTab] = useState<"grounded" | "refusal">("grounded");

  return (
    <div className="min-h-screen bg-[#06090e] text-gray-100 selection:bg-emerald-500/30 selection:text-emerald-200">
      <PublicNavbar />

      {/* =====================================================================
          1. HERO SECTION
          ===================================================================== */}
      <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
        {/* Subtle Ambient Radial Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-12">
          {/* Hero Typography & CTAs */}
          <div className="text-center space-y-6 max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold tracking-wide uppercase text-[11px]">
                Compliance-Grounded Financial Intelligence
              </span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.12] font-sans">
              Make every advisory answer{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
                traceable to trusted evidence.
              </span>
            </h1>

            <p className="text-sm sm:text-base lg:text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed font-sans">
              FINEE.ai helps financial advisory teams search approved institutional knowledge, retrieve verified evidence, and generate grounded answers without relying on unsupported model knowledge.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
              <Link
                href="/signup"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-emerald-500/25 active:scale-[0.99] cursor-pointer"
              >
                <span>Get Started</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
              <Link
                href="/platform"
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-surface-raised hover:bg-surface-elevated text-gray-200 hover:text-white border border-surface-border text-sm font-medium flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <span>Explore the Platform</span>
                <ArrowRight className="w-4 h-4 text-gray-400" />
              </Link>
            </div>
          </div>

          {/* =================================================================
              2. REALISTIC PRODUCT PREVIEW MOCKUP (Hero Artwork)
              ================================================================= */}
          <div className="max-w-5xl mx-auto pt-6">
            <div className="rounded-2xl border border-surface-border bg-surface/90 shadow-2xl overflow-hidden backdrop-blur-md">
              {/* Mockup Window Header */}
              <div className="px-4 py-3 bg-[#0a0f1d] border-b border-surface-border flex items-center justify-between text-xs font-mono text-gray-400">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
                  </div>
                  <span className="ml-2 text-gray-400 font-semibold text-[11px]">FINEE Advisory Workspace</span>
                </div>

                <div className="flex items-center gap-2 text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300">
                    HNSW Cosine · Cosine Sim &gt; 0.70
                  </span>
                  <span className="px-2 py-0.5 rounded bg-surface-raised border border-surface-border text-gray-300">
                    MongoDB Persisted
                  </span>
                </div>
              </div>

              {/* Mockup Body: Two Column Showcase */}
              <div className="p-5 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-[#080d1a]/80">
                {/* Left: Chat Conversation */}
                <div className="lg:col-span-7 space-y-4">
                  {/* User Query */}
                  <div className="flex items-start justify-end gap-2.5">
                    <div className="bg-emerald-600/90 text-white rounded-2xl rounded-tr-none px-4 py-2.5 text-xs sm:text-[13px] leading-relaxed max-w-md shadow-md">
                      What are the approved advisory fee limits for Tier 1 discretionary wealth accounts?
                    </div>
                  </div>

                  {/* Assistant Grounded Response */}
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5 shadow-inner">
                      <ShieldCheck className="w-4 h-4" />
                    </div>

                    <div className="bg-surface border border-surface-border rounded-2xl rounded-tl-none p-4 text-xs sm:text-[13px] text-gray-200 leading-relaxed shadow-lg space-y-3 flex-1">
                      <p>
                        Under Section 4.1 of the approved 2026 Global Wealth Advisory Standards, the maximum allowable annual advisory fee for Tier 1 discretionary wealth accounts is capped at <strong className="text-white font-semibold">1.25% of AUM</strong>.{" "}
                        <span className="inline-flex items-center px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono text-[10px] font-bold mx-0.5">
                          [1]
                        </span>
                      </p>
                      <p>
                        Advisory billing must be calculated quarterly in arrears using the average daily asset value of the preceding quarter with itemized client notification.{" "}
                        <span className="inline-flex items-center px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono text-[10px] font-bold mx-0.5">
                          [2]
                        </span>
                      </p>

                      {/* Supporting Citations Bar */}
                      <div className="pt-2 border-t border-surface-border flex flex-wrap items-center gap-2">
                        <span className="text-[10px] font-mono text-gray-400 font-semibold uppercase">Verified Citations:</span>
                        <span className="px-2 py-1 rounded bg-surface-raised border border-surface-border text-[11px] font-mono text-gray-300 flex items-center gap-1">
                          <span className="text-emerald-400 font-bold">[1]</span> Global Wealth Advisory Standard 2026
                        </span>
                        <span className="px-2 py-1 rounded bg-surface-raised border border-surface-border text-[11px] font-mono text-gray-300 flex items-center gap-1">
                          <span className="text-emerald-400 font-bold">[2]</span> Fee Billing Schedule (v2.4)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Real-time Evidence Inspector Drawer */}
                <div className="lg:col-span-5 bg-surface rounded-2xl border border-surface-border p-4 space-y-3.5 shadow-xl">
                  <div className="flex items-center justify-between pb-2 border-b border-surface-border">
                    <div className="flex items-center gap-1.5 text-xs font-bold font-mono uppercase text-emerald-400">
                      <FileCheck2 className="w-4 h-4" />
                      <span>Evidence Inspector</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-emerald-950 border border-emerald-800 text-emerald-300">
                      100% Grounded
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
                      <span>Source Document:</span>
                      <span className="text-white font-medium">wealth_advisory_2026.pdf</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
                      <span>Section & Page:</span>
                      <span className="text-white">Section 4.1 · Page 4</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
                      <span>Approval State:</span>
                      <span className="text-emerald-400 font-semibold">APPROVED (Active)</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
                      <span>Relevance Score:</span>
                      <span className="text-emerald-400 font-bold">0.942 Cosine / 9.2 Rerank</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-surface-raised border border-surface-border text-[11px] text-gray-300 leading-relaxed font-sans space-y-1">
                    <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">Verbatim Excerpt</span>
                    <p className="italic text-gray-300">
                      "Section 4.1: Maximum allowable annual advisory fee for Tier 1 discretionary wealth accounts is capped at 1.25% of AUM, with billing executed quarterly in arrears."
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          3. TRUST & CREDIBILITY STRIP
          ===================================================================== */}
      <section className="border-y border-surface-border bg-[#070b14] py-8 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4">
            <p className="text-xs font-mono uppercase tracking-widest text-emerald-400 font-semibold">
              Built for Evidence-First Financial Decisions
            </p>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-2">
              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border/60 text-center space-y-1">
                <ShieldCheck className="w-5 h-5 text-emerald-400 mx-auto" />
                <p className="text-xs font-semibold text-white">Approved Knowledge</p>
                <p className="text-[10px] text-gray-400">Strictly institutional docs</p>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border/60 text-center space-y-1">
                <FileCheck2 className="w-5 h-5 text-emerald-400 mx-auto" />
                <p className="text-xs font-semibold text-white">Source Traceability</p>
                <p className="text-[10px] text-gray-400">Page & section citations</p>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border/60 text-center space-y-1">
                <Sparkles className="w-5 h-5 text-emerald-400 mx-auto" />
                <p className="text-xs font-semibold text-white">Grounded Responses</p>
                <p className="text-[10px] text-gray-400">Zero model fabrication</p>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border/60 text-center space-y-1">
                <Eye className="w-5 h-5 text-emerald-400 mx-auto" />
                <p className="text-xs font-semibold text-white">Human Review</p>
                <p className="text-[10px] text-gray-400">Auditable decision trail</p>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border/60 text-center space-y-1 col-span-2 md:col-span-1">
                <Lock className="w-5 h-5 text-emerald-400 mx-auto" />
                <p className="text-xs font-semibold text-white">Zero Data Training</p>
                <p className="text-[10px] text-gray-400">Client queries never trained</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          4. PROBLEM STATEMENT
          ===================================================================== */}
      <section className="py-20 md:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-amber-400 font-bold">
            <AlertCircle className="w-4 h-4" />
            <span>The Advisory Compliance Challenge</span>
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight font-sans">
            Financial advice is only as trustworthy as the evidence behind it.
          </h2>
          <p className="text-sm sm:text-base text-gray-400 leading-relaxed font-sans">
            Advisory teams work across complex matrices of fund factsheets, regulatory circulars, client suitability disclosures, and fee schedules. When teams rely on generic AI models or manual searches, compliance risks multiply.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3 hover:border-amber-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white font-sans">Fragmented & Outdated Policies</h3>
            <p className="text-xs text-gray-400 leading-relaxed font-sans">
              Guidance evolves across quarterly policy revisions. Advisors frequently reference superseded fee schedules or outdated compliance thresholds.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3 hover:border-amber-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white font-sans">Generic AI Hallucinations</h3>
            <p className="text-xs text-gray-400 leading-relaxed font-sans">
              Standard commercial LLMs invent percentages, fabricate rules, and answer questions confidently even when no institutional policy exists.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3 hover:border-amber-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
              <Eye className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white font-sans">Unverifiable Black Boxes</h3>
            <p className="text-xs text-gray-400 leading-relaxed font-sans">
              Auditors and compliance officers cannot accept answers without exact document IDs, versions, and paragraph-level source attribution.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================================
          5. THE FINEE SOLUTION PIPELINE
          ===================================================================== */}
      <section id="how-it-works" className="py-20 bg-[#070b14] border-y border-surface-border relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-emerald-400 font-bold">
              <Cpu className="w-4 h-4" />
              <span>Deterministic Advisory Pipeline</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight font-sans">
              From question to evidence-backed answer.
            </h2>
            <p className="text-xs sm:text-sm text-gray-400 font-sans leading-relaxed">
              Every query executes through a multi-stage validation engine designed to enforce fiduciary rigor.
            </p>
          </div>

          {/* Sequential Process Flow */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 sm:gap-4">
            {[
              { step: "01", name: "ASK", desc: "Advisor enters financial or compliance question", icon: Search },
              { step: "02", name: "RETRIEVE", desc: "HNSW cosine vector search across verified chunks", icon: Database },
              { step: "03", name: "RERANK", desc: "Two-stage relevance evaluation & distractor filter", icon: SlidersHorizontal },
              { step: "04", name: "VERIFY", desc: "Retrieval guardrails & pre-LLM safe refusal check", icon: ShieldCheck },
              { step: "05", name: "ANSWER", desc: "Grounded context synthesis strictly bounded by facts", icon: Sparkles },
              { step: "06", name: "CITE", desc: "Precise bracketed citations mapped to source pages", icon: FileCheck2 },
            ].map((p, idx) => {
              const Icon = p.icon;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-surface border border-surface-border space-y-2.5 relative group hover:border-emerald-500/40 transition-all flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-800">
                      {p.step}
                    </span>
                    <Icon className="w-4 h-4 text-gray-400 group-hover:text-emerald-400 transition-colors" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xs font-bold font-mono uppercase text-white tracking-wider">{p.name}</h3>
                    <p className="text-[11px] text-gray-400 leading-snug font-sans">{p.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =====================================================================
          6. KEY PRODUCT CAPABILITIES
          ===================================================================== */}
      <section className="py-20 md:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-emerald-400 font-bold">
            <Sparkles className="w-4 h-4" />
            <span>Enterprise Features</span>
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight font-sans">
            Engineered for institutional rigor.
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 font-sans">
            Comprehensive knowledge control, verification, and auditability at enterprise scale.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              title: "Grounded AI Answers",
              desc: "Answers generated strictly from verified context. Zero extrapolation beyond approved documents.",
              icon: ShieldCheck,
            },
            {
              title: "Source Citations",
              desc: "Exact inline citation markers ([1], [2]) linking every sentence to source document, section, and page.",
              icon: FileCheck2,
            },
            {
              title: "Document Control",
              desc: "Administrator registry for versions, effective dates, approval state, and chunk embedding management.",
              icon: Database,
            },
            {
              title: "Semantic Vector Search",
              desc: "High-dimensional HNSW cosine retrieval indexed in ChromaDB for sub-50ms candidate matching.",
              icon: Cpu,
            },
            {
              title: "Re-ranking Engine",
              desc: "Secondary scoring model prioritizing direct entity facts and eliminating distractor fund documents.",
              icon: SlidersHorizontal,
            },
            {
              title: "Hallucination Guardrails",
              desc: "Pre-LLM retrieval strength checks that safely refuse unsupported queries without guessing.",
              icon: ShieldAlert,
            },
            {
              title: "Persistent Chat History",
              desc: "Full conversation history persisted in MongoDB with pinning, multi-turn query rewriting, and multi-tenant isolation.",
              icon: History,
            },
            {
              title: "Real-time Token & Audit Ledger",
              desc: "Accurate prompt and completion token tracking with exact cost calculations and compliance audit events.",
              icon: BarChart3,
            },
          ].map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-surface border border-surface-border space-y-3 hover:border-emerald-500/30 transition-all group"
              >
                <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">{feat.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed font-sans">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* =====================================================================
          7. EVIDENCE-FIRST & SAFE REFUSAL COMPARISON
          ===================================================================== */}
      <section className="py-20 bg-[#070b14] border-y border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-sans">
              Every answer should be explainable.
            </h2>
            <p className="text-xs sm:text-sm text-gray-400 font-sans">
              Compare how FINEE provides grounded answers when evidence is verified versus refusing when evidence is missing.
            </p>

            {/* Toggle Tabs */}
            <div className="inline-flex items-center p-1 rounded-xl bg-surface border border-surface-border mt-2">
              <button
                onClick={() => setActiveTab("grounded")}
                className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeTab === "grounded"
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Grounded Answer Example
              </button>
              <button
                onClick={() => setActiveTab("refusal")}
                className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeTab === "refusal"
                    ? "bg-amber-600 text-white shadow-sm"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Safe Refusal Example
              </button>
            </div>
          </div>

          {/* Interactive Card Example */}
          <div className="max-w-4xl mx-auto">
            {activeTab === "grounded" ? (
              <div className="p-6 sm:p-8 rounded-2xl bg-surface border border-emerald-500/30 space-y-6 shadow-2xl animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                  <span className="text-xs font-mono text-emerald-400 font-bold uppercase">
                    Case 1: Verified Compliance Query
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                    Status: ANSWERED (Grounded)
                  </span>
                </div>

                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl bg-surface-raised border border-surface-border text-xs text-gray-300 font-sans">
                    <span className="text-[10px] font-mono text-gray-500 font-bold uppercase block mb-1">Advisor Question</span>
                    "What documentation is required to verify client suitability prior to high-risk portfolio allocation?"
                  </div>

                  <div className="p-4 rounded-xl bg-surface-raised border border-emerald-500/30 text-xs sm:text-sm text-gray-100 font-sans leading-relaxed space-y-2">
                    <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase block mb-1">Grounded Synthesis</span>
                    <p>
                      Advisors must obtain a completed Client Risk Tolerance Assessment (v2.1), verified government identification, and certified liquid net worth verification before placing allocations in high-risk strategies.{" "}
                      <span className="font-mono text-emerald-400 font-bold">[1]</span> Suitability forms must be re-certified every 12 months.{" "}
                      <span className="font-mono text-emerald-400 font-bold">[2]</span>
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-xs space-y-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-mono font-bold text-[11px]">
                      <FileCheck2 className="w-4 h-4" />
                      <span>Attached Provenance</span>
                    </div>
                    <p className="text-[11px] text-gray-300 font-mono">
                      [1] Client Suitability Standard Operating Procedure (SOP-WM-2026), Section 3.2, Page 8.
                    </p>
                    <p className="text-[11px] text-gray-300 font-mono">
                      [2] Annual Suitability Refresh Guidelines, Section 1.4, Page 2.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 sm:p-8 rounded-2xl bg-surface border border-amber-500/30 space-y-6 shadow-2xl animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                  <span className="text-xs font-mono text-amber-400 font-bold uppercase">
                    Case 2: Out-of-Scope / Unsupported Query
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-amber-950 text-amber-300 border border-amber-800">
                    Status: REFUSED_WEAK_CONTEXT
                  </span>
                </div>

                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl bg-surface-raised border border-surface-border text-xs text-gray-300 font-sans">
                    <span className="text-[10px] font-mono text-gray-500 font-bold uppercase block mb-1">Out-of-Scope Question</span>
                    "What is today's current Bitcoin price and Ethereum trading volume?"
                  </div>

                  <div className="p-4 rounded-xl bg-surface-raised border border-amber-500/30 text-xs sm:text-sm text-gray-100 font-sans leading-relaxed space-y-2">
                    <span className="text-[10px] font-mono text-amber-400 font-bold uppercase block mb-1">Safe Refusal (Pre-LLM Guardrail)</span>
                    <p className="text-gray-200">
                      "I don't have enough reliable evidence in the approved knowledge base to answer that question."
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-raised border border-surface-border text-xs space-y-2 font-mono text-gray-400 text-[11px]">
                    <div className="flex items-center gap-2 text-amber-400 font-bold">
                      <ShieldAlert className="w-4 h-4" />
                      <span>Guardrail Compliance Check</span>
                    </div>
                    <p>Vector Retrieval Score: 0.3200 (Required: &gt;= 0.7000)</p>
                    <p>Re-ranking Score: 0.00/10 (Required: &gt;= 5.00/10)</p>
                    <p>LLM Invoked: <span className="text-emerald-400 font-bold">FALSE (Zero Cost, Zero Guessing)</span></p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* =====================================================================
          8. COMPARISON MATRIX (Why FINEE)
          ===================================================================== */}
      <section className="py-20 md:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-emerald-400 font-bold">
            <Scale className="w-4 h-4" />
            <span>The Enterprise Advantage</span>
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight font-sans">
            Why financial leaders choose FINEE.ai.
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 font-sans">
            Clear comparison against traditional manual search and generic commercial AI chatbots.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse bg-surface rounded-2xl border border-surface-border overflow-hidden">
            <thead>
              <tr className="bg-[#0a0f1d] border-b border-surface-border font-mono text-gray-400 text-[11px]">
                <th className="p-4 sm:p-5">Capability</th>
                <th className="p-4 sm:p-5">Traditional Search</th>
                <th className="p-4 sm:p-5">Generic AI Chatbots</th>
                <th className="p-4 sm:p-5 text-emerald-400 font-bold bg-emerald-950/20">FINEE.ai</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border font-sans text-gray-300">
              <tr>
                <td className="p-4 sm:p-5 font-semibold text-white">Knowledge Source</td>
                <td className="p-4 sm:p-5 text-gray-400">File folder search</td>
                <td className="p-4 sm:p-5 text-gray-400">Public web training data</td>
                <td className="p-4 sm:p-5 text-white font-medium bg-emerald-950/10">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approved Institutional Docs
                  </span>
                </td>
              </tr>
              <tr>
                <td className="p-4 sm:p-5 font-semibold text-white">Hallucination Risk</td>
                <td className="p-4 sm:p-5 text-gray-400">Low (Manual reading)</td>
                <td className="p-4 sm:p-5 text-red-400 font-semibold">High (Unverified output)</td>
                <td className="p-4 sm:p-5 text-white font-medium bg-emerald-950/10">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Pre-LLM Guardrail Enforced
                  </span>
                </td>
              </tr>
              <tr>
                <td className="p-4 sm:p-5 font-semibold text-white">Inline Citations</td>
                <td className="p-4 sm:p-5 text-gray-400">None</td>
                <td className="p-4 sm:p-5 text-gray-400">Generic or hallucinated</td>
                <td className="p-4 sm:p-5 text-white font-medium bg-emerald-950/10">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Page & Section Traceability
                  </span>
                </td>
              </tr>
              <tr>
                <td className="p-4 sm:p-5 font-semibold text-white">Unsupported Queries</td>
                <td className="p-4 sm:p-5 text-gray-400">0 results</td>
                <td className="p-4 sm:p-5 text-red-400 font-semibold">Fabricates answers</td>
                <td className="p-4 sm:p-5 text-white font-medium bg-emerald-950/10">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Automated Safe Refusal
                  </span>
                </td>
              </tr>
              <tr>
                <td className="p-4 sm:p-5 font-semibold text-white">Audit & Monitoring</td>
                <td className="p-4 sm:p-5 text-gray-400">Manual log files</td>
                <td className="p-4 sm:p-5 text-gray-400">None</td>
                <td className="p-4 sm:p-5 text-white font-medium bg-emerald-950/10">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Full Token & Query Ledger
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* =====================================================================
          9. HIGH-IMPACT CALL TO ACTION (CTA)
          ===================================================================== */}
      <section className="py-20 bg-gradient-to-b from-[#070b14] to-[#04060b] border-t border-surface-border relative overflow-hidden">
        <div className="absolute inset-0 bg-emerald-500/5 blur-[120px] pointer-events-none" />

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8 relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <ShieldCheck className="w-4 h-4" />
            <span>Fiduciary Advisory Intelligence</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight font-sans leading-tight">
            Bring evidence into every financial advisory decision.
          </h2>

          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto leading-relaxed font-sans">
            Deploy institutional-grade intelligence grounded strictly in verified compliance documents with complete source traceability.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link
              href="/signup"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center justify-center gap-2 transition-all shadow-xl hover:shadow-emerald-500/30 active:scale-[0.98] cursor-pointer"
            >
              <span>Get Started Now</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-surface-raised hover:bg-surface-elevated text-gray-200 hover:text-white border border-surface-border text-sm font-semibold transition-all cursor-pointer"
            >
              Sign In to Workspace
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
