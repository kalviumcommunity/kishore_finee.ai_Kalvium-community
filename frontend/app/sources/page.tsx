"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  ShieldCheck,
  CheckCircle2,
  Filter,
  ArrowRight,
  Database,
  ExternalLink,
  Layers,
  Calendar,
  Building,
} from "lucide-react";
import { ragApi } from "@/services/ragApi";
import { DocumentRecord } from "@/types";

export default function SourcesPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("All");

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await ragApi.getDocuments();
        setDocuments(res || []);
      } catch (err) {
        console.warn("Could not fetch documents:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  const docTypes = ["All", ...Array.from(new Set(documents.map((d) => d.metadata?.document_type || "Policy")))];

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (doc.metadata?.title && doc.metadata.title.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType =
      selectedType === "All" || (doc.metadata?.document_type || "Policy") === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background text-gray-100 p-6 sm:p-8 max-w-6xl mx-auto w-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-6">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Approved Knowledge Corpus</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">
            Compliance Sources &amp; Manuals
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 font-sans">
            Authoritative documents indexed in the FINEE.ai vector database and available for retrieval.
          </p>
        </div>

        <Link
          href="/chatask"
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-md self-start sm:self-auto cursor-pointer"
        >
          <span>Ask Question on Sources</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 rounded-2xl bg-surface border border-surface-border">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search policies by filename or topic..."
            className="w-full bg-surface-raised border border-surface-border rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        {/* Category Type Filter */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          {docTypes.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap cursor-pointer ${
                selectedType === t
                  ? "bg-emerald-600 text-white font-semibold"
                  : "bg-surface-raised text-gray-400 hover:text-gray-200 border border-surface-border"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Documents List / Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-gray-500 font-mono">
          Loading approved compliance sources...
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-surface border border-surface-border space-y-3">
          <FileText className="w-10 h-10 text-gray-600 mx-auto" />
          <h3 className="text-base font-bold text-white font-sans">No matching policies found</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto font-sans">
            {searchTerm || selectedType !== "All"
              ? "Try adjusting your search terms or filter selection."
              : "No compliance manuals have been approved in the knowledge base yet."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredDocs.map((doc) => (
            <div
              key={doc.document_id}
              className="p-5 rounded-2xl bg-surface border border-surface-border hover:border-surface-borderLight transition-all shadow-lg space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-white truncate" title={doc.original_filename}>
                        {doc.original_filename}
                      </h4>
                      <p className="text-[11px] text-gray-400 font-mono">
                        {doc.metadata?.document_type || "Policy"} · v{doc.metadata?.version || "1.0"}
                      </p>
                    </div>
                  </div>

                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 shrink-0 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Approved</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-gray-400 bg-surface-raised p-3 rounded-xl border border-surface-border">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-gray-500" />
                    <span>{doc.chunks_indexed || doc.chunks_created || 0} Chunks Indexed</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-gray-500" />
                    <span>Active in Chroma</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-surface-border flex items-center justify-between text-xs">
                <span className="text-[10px] font-mono text-gray-500">
                  ID: {doc.document_id.substring(0, 8)}...
                </span>
                <Link
                  href={`/chatask?q=Tell+me+about+the+contents+of+${encodeURIComponent(doc.original_filename)}`}
                  className="text-emerald-400 hover:underline font-mono text-[11px] flex items-center gap-1"
                >
                  <span>Query this Document</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
