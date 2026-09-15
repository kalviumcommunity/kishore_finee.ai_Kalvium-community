"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowRight, Shield, CheckCircle2, Lock, FileText } from "lucide-react";

export const PublicFooter: React.FC = () => {
  return (
    <footer className="bg-[#050811] border-t border-surface-border text-gray-400 text-xs select-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand Column */}
          <div className="col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-base font-bold text-white tracking-tight font-sans">
                FINEE<span className="text-emerald-400">.ai</span>
              </span>
            </Link>

            <p className="text-xs text-gray-400 leading-relaxed font-sans max-w-sm">
              Compliance-Grounded Financial Advisory Intelligence. Searching approved institutional knowledge, verifying evidence, and generating citation-grounded advisory answers.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2 text-[11px] font-mono text-gray-400">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> SOC-2 Type II
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-400" /> 256-bit AES
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-emerald-400" /> Zero Training
              </span>
            </div>
          </div>

          {/* Column 1: Platform */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-white">Platform</h4>
            <ul className="space-y-2 font-sans">
              <li>
                <Link href="/platform" className="hover:text-emerald-400 transition-colors">
                  Overview & Architecture
                </Link>
              </li>
              <li>
                <Link href="/how-it-works" className="hover:text-emerald-400 transition-colors">
                  Retrieval & Re-ranking
                </Link>
              </li>
              <li>
                <Link href="/trust" className="hover:text-emerald-400 transition-colors">
                  Hallucination Guardrails
                </Link>
              </li>
              <li>
                <Link href="/platform" className="hover:text-emerald-400 transition-colors">
                  Source Provenance
                </Link>
              </li>
              <li>
                <Link href="/platform" className="hover:text-emerald-400 transition-colors">
                  Admin Control Center
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Solutions */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-white">Solutions</h4>
            <ul className="space-y-2 font-sans">
              <li>
                <Link href="/solutions" className="hover:text-emerald-400 transition-colors">
                  Wealth Advisory
                </Link>
              </li>
              <li>
                <Link href="/solutions" className="hover:text-emerald-400 transition-colors">
                  Compliance Research
                </Link>
              </li>
              <li>
                <Link href="/solutions" className="hover:text-emerald-400 transition-colors">
                  Policy Discrepancy Audit
                </Link>
              </li>
              <li>
                <Link href="/solutions" className="hover:text-emerald-400 transition-colors">
                  Client Suitability Check
                </Link>
              </li>
              <li>
                <Link href="/solutions" className="hover:text-emerald-400 transition-colors">
                  Knowledge Operations
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Company & Trust */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-white">Company</h4>
            <ul className="space-y-2 font-sans">
              <li>
                <Link href="/about" className="hover:text-emerald-400 transition-colors">
                  About FINEE.ai
                </Link>
              </li>
              <li>
                <Link href="/trust" className="hover:text-emerald-400 transition-colors">
                  Security & Trust Center
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-emerald-400 transition-colors">
                  Enterprise Contact
                </Link>
              </li>
              <li>
                <Link href="/trust" className="hover:text-emerald-400 transition-colors">
                  Fiduciary Principles
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Legal Row */}
        <div className="pt-8 mt-12 border-t border-surface-border/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] font-mono">
          <p className="text-gray-500">
            © 2026 FINEE.ai. All rights reserved. Built for evidence-first financial decisions.
          </p>

          <div className="flex items-center gap-6 text-gray-400">
            <Link href="/trust" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link href="/trust" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
            <Link href="/trust" className="hover:text-white transition-colors">
              Security Disclosures
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
