"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  ShieldCheck,
  Sparkles,
  Activity,
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  FileCheck2,
  Database,
  Lock,
  Layers,
  HelpCircle,
  Cpu,
  BookOpen,
  Filter,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function HowItWorksPage() {
  const [activeStep, setActiveStep] = useState(1);

  const steps = [
    {
      step: 1,
      number: "01",
      title: "Upload & Verify Official Policies",
      subtitle: "Deterministic Ingestion & Admin Approval",
      icon: FileText,
      description:
        "Compliance officers and platform administrators upload authoritative financial policies, Form ADV brochures, custodial schedules, and AML supervisory manuals in PDF format.",
      details: [
        "Upload raw institutional PDF documents securely.",
        "Verify document status, department ownership, and versioning.",
        "Automatic layout detection and structural header tagging.",
      ],
      tag: "Admin Controlled",
    },
    {
      step: 2,
      number: "02",
      title: "Structure-Aware Chunking & Cleaning",
      subtitle: "Zero Information Loss",
      icon: Layers,
      description:
        "Documents undergo high-fidelity extraction that cleans OCR artifacts while preserving regulatory tables, bullet hierarchies, and page numbers.",
      details: [
        "Preserves numeric fee schedules and multi-column tables.",
        "Deterministic chunking with 15% overlap to avoid context fragmentation.",
        "Enriches each chunk with page offsets and parent section metadata.",
      ],
      tag: "Deterministic Preprocessing",
    },
    {
      step: 3,
      number: "03",
      title: "High-Dimensional Vector Indexing",
      subtitle: "Dense Embeddings in Chroma DB",
      icon: Database,
      description:
        "Chunks are converted into dense vector embeddings and stored in Chroma DB alongside approval metadata, ready for instant semantic retrieval.",
      details: [
        "High-dimensional semantic embeddings capture financial terminology.",
        "Indexed vector collections for sub-100ms similarity scoring.",
        "Partitioned metadata for active vs draft document isolation.",
      ],
      tag: "Vector Indexing",
    },
    {
      step: 4,
      number: "04",
      title: "Advisor Query & Strict Similarity Gate",
      subtitle: "Hard Threshold Gating (0.720 Cutoff)",
      icon: ShieldCheck,
      description:
        "When an advisor asks a question, FINEE retrieves candidate chunks and measures cosine similarity. If the score falls below 0.720, an automated safe refusal is generated.",
      details: [
        "Semantic matching surfaces the most relevant policy chunks.",
        "Strict 0.720 threshold blocks irrelevant or speculative documents.",
        "Automated refusal prevents model from guessing answers outside approved corpus.",
      ],
      tag: "Fiduciary Guardrails",
    },
    {
      step: 5,
      number: "05",
      title: "Grounded Synthesis & Audit Trail",
      subtitle: "Exact Attestation & MongoDB Logging",
      icon: Sparkles,
      description:
        "The model synthesizes a concise, professional answer exclusively from the qualified chunks, attaching clickable citations with page numbers and logging the session to MongoDB.",
      details: [
        "Output contains zero leaked prompt artifacts or raw metadata.",
        "Every factual claim links directly to [Document Name, Page N].",
        "Full conversation and citation records are saved to MongoDB.",
      ],
      tag: "Fiduciary Output",
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
            <BookOpen className="w-3.5 h-3.5" />
            <span>5-Step Fiduciary Retrieval Pipeline</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-sans max-w-4xl mx-auto leading-tight">
            How FINEE.ai turns complex compliance manuals into{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
              verifiable advisory answers.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto font-sans leading-relaxed">
            Unlike standard consumer chatbots that hallucinate plausible answers, FINEE.ai enforces a strict 5-stage verification loop that grounds every single word in your approved documents.
          </p>
        </div>
      </section>

      {/* Interactive Step-by-Step Pipeline */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Step Selector List */}
          <div className="lg:col-span-5 space-y-3">
            <div className="p-2 text-xs font-mono font-bold uppercase text-emerald-400">
              Pipeline Stages
            </div>
            {steps.map((s) => {
              const Icon = s.icon;
              const isSelected = activeStep === s.step;
              return (
                <button
                  key={s.step}
                  onClick={() => setActiveStep(s.step)}
                  className={`w-full text-left p-4 rounded-xl border transition-all flex items-start gap-4 cursor-pointer ${
                    isSelected
                      ? "bg-surface-raised border-emerald-500/50 shadow-lg"
                      : "bg-surface/60 border-surface-border hover:bg-surface hover:border-surface-borderLight"
                  }`}
                >
                  <span
                    className={`font-mono font-bold text-sm px-2.5 py-1 rounded-lg border ${
                      isSelected
                        ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                        : "bg-surface-raised text-gray-400 border-surface-border"
                    }`}
                  >
                    {s.number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-white">{s.title}</h4>
                      <span className="text-[10px] font-mono text-gray-400">{s.tag}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 truncate">{s.subtitle}</p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Active Step Detailed Card */}
          <div className="lg:col-span-7 p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl space-y-6">
            {(() => {
              const current = steps.find((s) => s.step === activeStep) || steps[0];
              const Icon = current.icon;
              return (
                <>
                  <div className="flex items-center justify-between border-b border-surface-border pb-5">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center">
                        <Icon className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                          Stage {current.number}
                        </span>
                        <h3 className="text-xl font-bold text-white font-sans">
                          {current.title}
                        </h3>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                      {current.tag}
                    </span>
                  </div>

                  <p className="text-sm text-gray-300 leading-relaxed font-sans">
                    {current.description}
                  </p>

                  <div className="space-y-3 pt-2">
                    <h5 className="text-xs font-mono uppercase font-bold text-gray-400">
                      Execution Guarantees
                    </h5>
                    <div className="space-y-2.5">
                      {current.details.map((d, i) => (
                        <div
                          key={i}
                          className="p-3.5 rounded-xl bg-surface-raised border border-surface-border flex items-start gap-3 text-xs text-gray-200 font-sans"
                        >
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{d}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-surface-border flex items-center justify-between">
                    <button
                      disabled={activeStep === 1}
                      onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
                      className="px-4 py-2 rounded-lg bg-surface-raised text-xs font-semibold text-gray-300 hover:text-white disabled:opacity-40 disabled:pointer-events-none transition-colors cursor-pointer"
                    >
                      &larr; Previous Stage
                    </button>
                    <button
                      disabled={activeStep === steps.length}
                      onClick={() => setActiveStep((prev) => Math.min(steps.length, prev + 1))}
                      className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white disabled:opacity-40 disabled:pointer-events-none transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <span>Next Stage</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      </section>

      {/* Comparison: In-Scope vs Out-of-Scope Execution */}
      <section className="py-16 border-t border-surface-border bg-[#0a0f1d]/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-2">
            <h3 className="text-xs font-mono uppercase font-bold text-emerald-400">
              Operational Safeguards
            </h3>
            <p className="text-2xl font-bold text-white font-sans">
              How FINEE Handles Different Types of Queries
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Grounded In-Scope Example */}
            <div className="p-6 rounded-2xl bg-surface border border-emerald-500/30 space-y-4 shadow-xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                  IN-SCOPE QUERY
                </span>
                <span className="text-[10px] font-mono text-emerald-400">Similarity: 0.892 (Pass)</span>
              </div>
              <div className="p-3 rounded-xl bg-surface-raised border border-surface-border text-xs text-gray-200">
                <p className="font-semibold text-white">Advisor Query:</p>
                <p className="text-gray-400 mt-0.5">&quot;What is the maximum advisory fee allowable for Tier 1 equity accounts?&quot;</p>
              </div>
              <div className="space-y-2 text-xs text-gray-300">
                <p className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Grounded Synthesis Output:
                </p>
                <p className="text-gray-300 leading-relaxed bg-surface-raised/40 p-3 rounded-xl border border-surface-border">
                  According to the Fee Schedule &amp; Client Agreement, Tier 1 equity accounts have a maximum allowable advisory fee of 1.25% annually, billed quarterly in arrears.
                </p>
                <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-[11px] font-mono text-emerald-300 flex items-center gap-2">
                  <FileCheck2 className="w-3.5 h-3.5" />
                  <span>Citation: Fee_Schedule_2024.pdf (Page 4, Section 2.1)</span>
                </div>
              </div>
            </div>

            {/* Out-of-Scope Safe Refusal Example */}
            <div className="p-6 rounded-2xl bg-surface border border-amber-500/30 space-y-4 shadow-xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800">
                  OUT-OF-SCOPE QUERY
                </span>
                <span className="text-[10px] font-mono text-amber-400">Similarity: 0.412 (Blocked)</span>
              </div>
              <div className="p-3 rounded-xl bg-surface-raised border border-surface-border text-xs text-gray-200">
                <p className="font-semibold text-white">Advisor Query:</p>
                <p className="text-gray-400 mt-0.5">&quot;What will be the price target of Tesla stock by Q4 2026?&quot;</p>
              </div>
              <div className="space-y-2 text-xs text-gray-300">
                <p className="font-semibold text-amber-400 flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4" />
                  Automated Safe Refusal Output:
                </p>
                <p className="text-gray-300 leading-relaxed bg-surface-raised/40 p-3 rounded-xl border border-surface-border">
                  I cannot find relevant information in the approved knowledge base to answer this question. The current policies cover institutional compliance, fee schedules, suitability, and AML guidelines.
                </p>
                <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/60 text-[11px] font-mono text-amber-300 flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Guardrail Gate: Similarity score below 0.720 threshold</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 border-t border-surface-border relative overflow-hidden text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans">
            Ready to See FINEE.ai in Action?
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
            Experience our grounded intelligence workspace and test your own compliance workflows today.
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
              href="/trust"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-surface-raised hover:bg-surface-elevated text-gray-200 hover:text-white border border-surface-border text-sm font-medium flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>Security &amp; Trust</span>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
