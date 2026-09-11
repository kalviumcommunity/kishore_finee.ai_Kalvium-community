"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  ShieldCheck,
  Scale,
  Building2,
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  FileCheck2,
  Clock,
  Sparkles,
  Search,
  Database,
  Users,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function SolutionsPage() {
  const [activePersona, setActivePersona] = useState<"advisors" | "compliance" | "legal" | "institutions">("advisors");

  const personas = [
    {
      id: "advisors" as const,
      title: "Wealth Advisors & RIAs",
      subtitle: "Instant policy clarity during client meetings",
      icon: Briefcase,
      badge: "Front-Office Advisory",
      challenge:
        "Advisors spend hours digging through 100-page Form ADV brochures and custodial agreements to answer simple client questions about fee schedules, account minimums, and suitability rules.",
      solution:
        "FINEE.ai acts as an instant fiduciary co-pilot, retrieving exact policy sections with cited page numbers so advisors can respond to clients with total confidence in seconds.",
      benefits: [
        "Instant answers to fee tier questions and billing breakpoints",
        "Clear suitability guidance for complex products (options, private equity)",
        "Zero risk of citing outdated or superseded policy manuals",
        "Persistent conversation history with pinned client consultation threads",
      ],
      sampleQuery: "What is the fee breakpoint for discretionary accounts exceeding $2.5M under our 2024 ADV?",
    },
    {
      id: "compliance" as const,
      title: "Chief Compliance Officers",
      subtitle: "Supervisory control and automated guardrail enforcement",
      icon: ShieldCheck,
      badge: "Supervisory & Oversight",
      challenge:
        "Supervising hundreds of advisor inquiries across multiple branch offices is error-prone. Generic AI tools introduce unvetted hallucination risks that violate FINRA Rule 2210.",
      solution:
        "FINEE.ai provides complete administrative control over document ingestion, strict 0.720 similarity gating to block ungrounded responses, and real-time MongoDB audit logging.",
      benefits: [
        "Enforce strict policy grounding with automated safe refusals",
        "Monitor user search queries, token consumption, and refusal rates",
        "One-click policy updates with automatic vector re-indexing",
        "Exportable audit trails for internal and regulatory examination",
      ],
      sampleQuery: "Supervisory review: show all queries where similarity score fell below 0.720 threshold this month.",
    },
    {
      id: "legal" as const,
      title: "Legal & Regulatory Counsel",
      subtitle: "Attributed regulatory cross-referencing",
      icon: Scale,
      badge: "Risk & Regulatory",
      challenge:
        "Legal teams must ensure that all institutional disclosures, custodial agreements, and client brochures remain consistent across evolving SEC rules and state regulations.",
      solution:
        "FINEE.ai indexes multi-version legal contracts and regulatory filings, enabling deterministic cross-referencing with exact paragraph-level citation attestation.",
      benefits: [
        "High-fidelity extraction preserving contractual clauses and tables",
        "Document version control with isolated draft vs active states",
        "Zero data leakage — proprietary contracts are never sent to public models",
        "Verifiable page and paragraph citations for every response",
      ],
      sampleQuery: "Compare indemnification clauses between Custodian A Agreement v2 and Custodian B Agreement v3.",
    },
    {
      id: "institutions" as const,
      title: "Enterprise Broker-Dealers",
      subtitle: "Scalable knowledge architecture for multi-desk organizations",
      icon: Building2,
      badge: "Enterprise Scale",
      challenge:
        "Large financial institutions suffer from fragmented knowledge silos across wealth management, investment banking, and retail advisory departments.",
      solution:
        "FINEE.ai deploys multi-tenant namespacing in Chroma DB and MongoDB, ensuring each business unit accesses only its authorized compliance manuals.",
      benefits: [
        "Department-level namespace partitioning and access controls",
        "High-throughput vector retrieval with sub-100ms response times",
        "Centralized document lifecycle management with role permissions",
        "Enterprise SSO and Google Identity integration",
      ],
      sampleQuery: "Retrieve authorized wealth management guidelines for structured note distribution in Tier 2 branches.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#06090e] text-gray-100 selection:bg-emerald-500/30 selection:text-emerald-200">
      <PublicNavbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-16 md:pt-40 md:pb-20 overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <Building2 className="w-3.5 h-3.5" />
            <span>Tailored Financial Workflows</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-sans max-w-4xl mx-auto leading-tight">
            Built for the specific demands of{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
              fiduciary professionals.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto font-sans leading-relaxed">
            Whether you are advising high-net-worth clients, managing enterprise supervisory compliance, or reviewing regulatory filings, FINEE.ai provides the exact verification and speed you need.
          </p>
        </div>
      </section>

      {/* Persona Tabs & Content */}
      <section className="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Persona Selector Tabs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {personas.map((p) => {
            const Icon = p.icon;
            const isSelected = activePersona === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setActivePersona(p.id)}
                className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between space-y-3 cursor-pointer ${
                  isSelected
                    ? "bg-surface border-emerald-500/60 shadow-lg"
                    : "bg-surface/50 border-surface-border hover:bg-surface hover:border-surface-borderLight"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                      isSelected
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-surface-raised text-gray-400 border border-surface-border"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-gray-400">{p.badge}</span>
                </div>
                <div>
                  <h4 className="text-xs sm:text-sm font-semibold text-white">{p.title}</h4>
                  <p className="text-[11px] text-gray-400 truncate mt-0.5">{p.subtitle}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Persona Deep Dive Card */}
        {(() => {
          const current = personas.find((p) => p.id === activePersona) || personas[0];
          const Icon = current.icon;
          return (
            <div className="p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl space-y-8">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-border pb-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0">
                    <Icon className="w-7 h-7" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                      {current.badge}
                    </span>
                    <h3 className="text-2xl font-bold text-white font-sans mt-0.5">
                      {current.title}
                    </h3>
                  </div>
                </div>

                <Link
                  href="/signup"
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md self-start md:self-auto cursor-pointer"
                >
                  <span>Start with this Workflow</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Challenge & Solution */}
                <div className="space-y-5">
                  <div className="space-y-2">
                    <h5 className="text-xs font-mono uppercase font-bold text-red-400">
                      The Operational Challenge
                    </h5>
                    <p className="text-xs sm:text-sm text-gray-300 leading-relaxed bg-surface-raised p-4 rounded-xl border border-surface-border">
                      {current.challenge}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <h5 className="text-xs font-mono uppercase font-bold text-emerald-400">
                      The FINEE.ai Solution
                    </h5>
                    <p className="text-xs sm:text-sm text-gray-300 leading-relaxed bg-emerald-950/20 p-4 rounded-xl border border-emerald-800/40">
                      {current.solution}
                    </p>
                  </div>
                </div>

                {/* Key Operational Benefits */}
                <div className="space-y-4">
                  <h5 className="text-xs font-mono uppercase font-bold text-gray-400">
                    Key Workflow Benefits
                  </h5>
                  <div className="space-y-2.5">
                    {current.benefits.map((b, i) => (
                      <div
                        key={i}
                        className="p-3.5 rounded-xl bg-surface-raised border border-surface-border flex items-start gap-3 text-xs text-gray-200"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{b}</span>
                      </div>
                    ))}
                  </div>

                  {/* Sample Query Box */}
                  <div className="p-3.5 rounded-xl bg-[#0a0f1d] border border-surface-border space-y-1">
                    <span className="text-[10px] font-mono text-gray-400 uppercase">
                      Typical Advisor Prompt
                    </span>
                    <p className="text-xs font-mono text-emerald-300">
                      &quot;{current.sampleQuery}&quot;
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}
      </section>

      {/* ROI & Operational Impact Grid */}
      <section className="py-16 border-t border-surface-border bg-[#0a0f1d]/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-2">
            <h3 className="text-xs font-mono uppercase font-bold text-emerald-400">
              Measurable Outcomes
            </h3>
            <p className="text-2xl font-bold text-white font-sans">
              Operational Efficiency Across Advisory Teams
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3">
              <span className="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono">
                90%
              </span>
              <h4 className="text-base font-bold text-white font-sans">
                Reduction in Policy Search Time
              </h4>
              <p className="text-xs text-gray-400 leading-relaxed font-sans">
                Advisors get instant, cited answers in seconds rather than manually searching across multiple PDF directories.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3">
              <span className="text-3xl sm:text-4xl font-extrabold text-white font-mono">
                0%
              </span>
              <h4 className="text-base font-bold text-white font-sans">
                Hallucinated Policy Citations
              </h4>
              <p className="text-xs text-gray-400 leading-relaxed font-sans">
                Strict 0.720 similarity gating ensures that every response is backed by an actual document chunk or safely refused.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-3">
              <span className="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono">
                100%
              </span>
              <h4 className="text-base font-bold text-white font-sans">
                Compliance Examination Readiness
              </h4>
              <p className="text-xs text-gray-400 leading-relaxed font-sans">
                Every query, chunk, and response is recorded in MongoDB with timestamp and token metrics for complete auditability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 border-t border-surface-border relative overflow-hidden text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans">
            Ready to Empower Your Advisory Team?
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
            Get started with FINEE.ai today or speak with our solutions engineering team.
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
              href="/contact"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-surface-raised hover:bg-surface-elevated text-gray-200 hover:text-white border border-surface-border text-sm font-medium flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>Request Custom Demo</span>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
