"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Mail,
  Building,
  User,
  MessageSquare,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Send,
  Phone,
  Clock,
  Sparkles,
} from "lucide-react";
import { PublicNavbar } from "@/components/PublicNavbar";
import { PublicFooter } from "@/components/PublicFooter";

export default function ContactPage() {
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    firmName: "",
    role: "Wealth Advisor / RIA",
    message: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-[#06090e] text-gray-100 selection:bg-emerald-500/30 selection:text-emerald-200">
      <PublicNavbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-16 md:pt-40 md:pb-20 overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <Mail className="w-3.5 h-3.5" />
            <span>Connect with our Team</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-sans max-w-4xl mx-auto leading-tight">
            Schedule an enterprise demo or{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
              compliance consultation.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto font-sans leading-relaxed">
            Discover how FINEE.ai can be tailored to your firm’s specific compliance manuals, custodial policies, and supervisory workflows.
          </p>
        </div>
      </section>

      {/* Form & Info Section */}
      <section className="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Contact Details & Value Props */}
          <div className="lg:col-span-5 space-y-6">
            <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-6 shadow-xl">
              <div>
                <h3 className="text-lg font-bold text-white font-sans">
                  Enterprise Advisory Inquiries
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Our solutions architecture team is available to review your compliance data structure and deployment requirements.
                </p>
              </div>

              <div className="space-y-4 text-xs text-gray-300">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-surface-raised border border-surface-border flex items-center justify-center text-emerald-400 shrink-0">
                    <Mail className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-semibold text-white">Direct Email</span>
                    <p className="text-gray-400 font-mono">compliance@finee.ai</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-surface-raised border border-surface-border flex items-center justify-center text-emerald-400 shrink-0">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-semibold text-white">Security &amp; Audit Requests</span>
                    <p className="text-gray-400 font-mono">security@finee.ai</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-surface-raised border border-surface-border flex items-center justify-center text-emerald-400 shrink-0">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-semibold text-white">Response Guarantee</span>
                    <p className="text-gray-400 font-mono">Within 24 business hours</p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>SOC-2 Aligned Architecture</span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  All enterprise demonstrations operate in isolated sandboxes with zero client data retention.
                </p>
              </div>
            </div>
          </div>

          {/* Contact / Demo Request Form */}
          <div className="lg:col-span-7 p-8 rounded-2xl bg-surface border border-surface-border shadow-2xl space-y-6">
            {formSubmitted ? (
              <div className="py-12 text-center space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-white font-sans">
                  Demo Request Received
                </h3>
                <p className="text-xs sm:text-sm text-gray-400 max-w-md mx-auto font-sans leading-relaxed">
                  Thank you, {formData.fullName}. A member of our enterprise compliance team will reach out to <span className="text-emerald-400 font-mono">{formData.email}</span> within 24 hours.
                </p>
                <div className="pt-4">
                  <Link
                    href="/"
                    className="px-6 py-2.5 rounded-xl bg-surface-raised hover:bg-surface-elevated text-xs font-semibold text-white border border-surface-border inline-flex items-center gap-2 transition-colors"
                  >
                    <span>Return to Homepage</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ) : (
              <>
                <div className="space-y-1 border-b border-surface-border pb-4">
                  <h3 className="text-xl font-bold text-white font-sans">
                    Request an Enterprise Walkthrough
                  </h3>
                  <p className="text-xs text-gray-400">
                    Fill out the form below and we will customize a demo for your advisory firm.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-gray-300">Full Name</label>
                      <input
                        type="text"
                        required
                        value={formData.fullName}
                        onChange={(e) =>
                          setFormData({ ...formData, fullName: e.target.value })
                        }
                        placeholder="Sarah Jenkins"
                        className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-gray-300">Work Email</label>
                      <input
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                        placeholder="sjenkins@advisorygroup.com"
                        className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-gray-300">Firm / Institution Name</label>
                      <input
                        type="text"
                        required
                        value={formData.firmName}
                        onChange={(e) =>
                          setFormData({ ...formData, firmName: e.target.value })
                        }
                        placeholder="Apex Wealth Partners"
                        className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-gray-300">Your Role</label>
                      <select
                        value={formData.role}
                        onChange={(e) =>
                          setFormData({ ...formData, role: e.target.value })
                        }
                        className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 transition-colors cursor-pointer"
                      >
                        <option>Wealth Advisor / RIA</option>
                        <option>Chief Compliance Officer (CCO)</option>
                        <option>Supervisory Principal</option>
                        <option>Legal Counsel / General Counsel</option>
                        <option>IT / Technology Leadership</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-gray-300">Message / Ingestion Needs</label>
                    <textarea
                      rows={4}
                      value={formData.message}
                      onChange={(e) =>
                        setFormData({ ...formData, message: e.target.value })
                      }
                      placeholder="Tell us about the policies or document formats your firm needs indexed..."
                      className="w-full bg-surface-raised border border-surface-border rounded-xl p-4 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-emerald-500/25 active:scale-[0.99] cursor-pointer"
                  >
                    <span>Submit Request</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
