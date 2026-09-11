"use client";

import React from "react";
import Link from "next/link";
import {
  Shield,
  ShieldCheck,
  Lock,
  FileCheck2,
  CheckCircle2,
  Database,
  Activity,
  ArrowRight,
  ChevronRight,
  Key,
  Server,
  Scale,
  Users,
  Eye,
  AlertTriangle,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function TrustPage() {
  const securityPillars = [
    {
      title: "Zero Model Training Guarantee",
      subtitle: "Your proprietary IP is strictly isolated",
      icon: Lock,
      description:
        "FINEE.ai never utilizes your uploaded compliance documents, client advisory queries, or session transcripts to fine-tune or train third-party foundation models. Data is processed strictly in-memory during inference.",
    },
    {
      title: "End-to-End Cryptographic Security",
      subtitle: "AES-256 at rest, TLS 1.3 in transit",
      icon: Key,
      description:
        "All vector embeddings in Chroma, PDF source documents, and conversation history in MongoDB are encrypted using enterprise-grade AES-256 encryption with rigorous key rotation protocols.",
    },
    {
      title: "Role-Based Access Governance",
      subtitle: "Granular separation of duties",
      icon: Users,
      description:
        "Advisors have read-only query access to authorized compliance documents. Document ingestion, vector re-indexing, approval status toggles, and audit monitoring are strictly restricted to verified administrators.",
    },
    {
      title: "Fiduciary Attribution & Zero Hallucination",
      subtitle: "Hard threshold relevance gates",
      icon: ShieldCheck,
      description:
        "By enforcing a mandatory 0.720 similarity threshold, FINEE eliminates speculative AI hallucinations. If authoritative evidence is absent, the system produces a safe, structured refusal.",
    },
    {
      title: "Comprehensive Audit Trail & Telemetry",
      subtitle: "SEC & FINRA examination readiness",
      icon: Activity,
      description:
        "Every advisor query, retrieved citation chunk, confidence score, token consumption, and response timestamp is permanently recorded in MongoDB for instant supervisory review.",
    },
    {
      title: "Isolated Tenant Namespacing",
      subtitle: "Logical & physical data boundary protection",
      icon: Database,
      description:
        "Institutional policies and user session states are isolated via strict namespace boundaries, preventing cross-tenant information leakage across advisory desks.",
    },
  ];

  const trustFaqs = [
    {
      q: "Are client questions or advisor queries used to train AI models?",
      a: "No. FINEE.ai operates under a strict zero-data-retention training policy. Your data is used exclusively at runtime for semantic retrieval and response synthesis.",
    },
    {
      q: "How does FINEE ensure compliance with FINRA and SEC supervisory rules?",
      a: "FINEE logs all queries, retrieved source passages, timestamps, and model responses into MongoDB. Compliance officers can review full audit trails and verify that answers adhered strictly to approved manuals.",
    },
    {
      q: "What happens when an advisor asks a question not covered by our policy manuals?",
      a: "The system's relevance engine evaluates retrieved chunks against a 0.720 similarity threshold. If no chunks qualify, the system safely refuses to answer rather than fabricating ungrounded information.",
    },
    {
      q: "How is administrator access managed?",
      a: "Admin access requires dedicated credentials and multi-factor authorization. The admin portal is segregated from standard advisor access with dedicated audit logging.",
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
            <Shield className="w-3.5 h-3.5" />
            <span>Enterprise Security &amp; Compliance Standards</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-sans max-w-4xl mx-auto leading-tight">
            Institutional-grade trust, data sovereignty, and{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
              fiduciary governance.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto font-sans leading-relaxed">
            Financial advisors operate in highly regulated environments. FINEE.ai is designed to meet the rigorous compliance, privacy, and supervisory standards demanded by wealth managers, broker-dealers, and RIAs.
          </p>
        </div>
      </section>

      {/* Security Pillars Grid */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
            Core Trust Architecture
          </h2>
          <p className="text-2xl sm:text-3xl font-bold text-white font-sans">
            6 Pillars of Fiduciary Data Protection
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {securityPillars.map((p, idx) => {
            const Icon = p.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-surface border border-surface-border hover:border-surface-borderLight transition-all shadow-xl space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white font-sans">{p.title}</h3>
                    <p className="text-xs font-mono text-emerald-400 mt-0.5">{p.subtitle}</p>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed font-sans pt-1">
                    {p.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-surface-border flex items-center gap-1.5 text-[11px] font-mono text-gray-400">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Enforced by Policy Gate</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Compliance Framework & Standards */}
      <section className="py-16 border-y border-surface-border bg-[#0a0f1d]/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-2">
            <h3 className="text-xs font-mono uppercase font-bold text-emerald-400">
              Regulatory Alignment
            </h3>
            <p className="text-2xl font-bold text-white font-sans">
              Designed for Fiduciary Regulatory Oversight
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-surface border border-surface-border space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase">SOC-2 Type II</span>
              <h4 className="text-sm font-semibold text-white">Security &amp; Confidentiality</h4>
              <p className="text-xs text-gray-400">Audited organizational controls for cloud software architectures.</p>
            </div>

            <div className="p-5 rounded-xl bg-surface border border-surface-border space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase">FINRA Rule 2210 &amp; 3110</span>
              <h4 className="text-sm font-semibold text-white">Supervisory Controls</h4>
              <p className="text-xs text-gray-400">Immutable consultation logging to assist compliance officer review.</p>
            </div>

            <div className="p-5 rounded-xl bg-surface border border-surface-border space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase">SEC Fiduciary Duty</span>
              <h4 className="text-sm font-semibold text-white">Attributed Grounding</h4>
              <p className="text-xs text-gray-400">Eliminates ungrounded advice by enforcing explicit page-level citations.</p>
            </div>

            <div className="p-5 rounded-xl bg-surface border border-surface-border space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase">GDPR / CCPA</span>
              <h4 className="text-sm font-semibold text-white">Privacy Rights</h4>
              <p className="text-xs text-gray-400">User identity controls and full session deletion capabilities.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust & Compliance FAQs */}
      <section className="py-20 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center space-y-2">
          <h3 className="text-xs font-mono uppercase font-bold text-emerald-400">
            Frequently Asked Questions
          </h3>
          <p className="text-2xl font-bold text-white font-sans">
            Security &amp; Compliance Inquiries
          </p>
        </div>

        <div className="space-y-4">
          {trustFaqs.map((faq, i) => (
            <div
              key={i}
              className="p-5 rounded-xl bg-surface border border-surface-border space-y-2"
            >
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{faq.q}</span>
              </h4>
              <p className="text-xs text-gray-300 pl-6 leading-relaxed font-sans">
                {faq.a}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 border-t border-surface-border relative overflow-hidden text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans">
            Protect Your Advisory Operations with FINEE.ai
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
            Speak with our enterprise compliance team or schedule a technical architecture walkthrough.
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
              <span>Contact Compliance Team</span>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
