"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  Upload,
  Plus,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  FileCheck,
  RefreshCw,
  X,
  Eye,
  ArrowRight,
  Shield,
  Layers,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { DocumentRecord } from "@/types";

export default function DocumentsManagementPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Upload Modal State
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const docs = await ragApi.getDocuments();
      setDocuments(docs || []);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFilesSelect = (selected: FileList | null) => {
    if (!selected) return;
    const newFiles = Array.from(selected);
    setUploadFiles((prev) => [...prev, ...newFiles]);
  };

  const removeSelectedFile = (index: number) => {
    setUploadFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadFiles.length === 0) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadProgress(`Processing 1 of ${uploadFiles.length}...`);

    try {
      if (uploadFiles.length === 1) {
        const res = await ragApi.uploadDocument(uploadFiles[0]);
        setUploadSuccess(`Document '${uploadFiles[0].name}' indexed successfully (${res.summary?.chunks_indexed || 1} chunks).`);
      } else {
        const batchRes = await ragApi.uploadBatchDocuments(uploadFiles);
        const successCount = batchRes.successful || 0;
        const failedCount = batchRes.failed || 0;
        if (failedCount === 0) {
          setUploadSuccess(`Successfully ingested and indexed all ${successCount} documents into ChromaDB.`);
        } else {
          setUploadSuccess(`Processed ${successCount} documents successfully. ${failedCount} files encountered errors.`);
        }
      }

      setUploadFiles([]);
      await fetchDocuments();
      setTimeout(() => {
        setIsUploadModalOpen(false);
        setUploadSuccess(null);
        setUploadProgress(null);
      }, 2000);
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload documents.");
    } finally {
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.document_id.toLowerCase().includes(searchQuery.toLowerCase());
    const docStatus = (doc.metadata?.approval_status || doc.status).toLowerCase();
    const matchesStatus = statusFilter === "all" || docStatus === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Document Ingestion & Management"
        subtitle="Upload Policies • Dynamic ChromaDB Indexing • Lifecycle Approval"
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Compliance Policy Corpus ({documents.length})</h2>
            <p className="text-xs text-gray-400 font-mono">
              Manage uploaded policies, inspect chunk boundaries, and enforce compliance approval
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={fetchDocuments}
              className="px-3.5 py-2 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border text-xs text-gray-300 flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => {
                setUploadFiles([]);
                setUploadError(null);
                setUploadSuccess(null);
                setIsUploadModalOpen(true);
              }}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-md"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Documents</span>
            </button>
          </div>
        </div>

        {/* Search & Filters Bar */}
        <div className="bg-surface border border-surface-border rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by document name or ID..."
              className="w-full bg-surface-raised border border-surface-border rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Status Filter Tabs */}
          <div className="flex items-center gap-1.5 self-start md:self-auto overflow-x-auto w-full md:w-auto">
            {["all", "approved", "processing", "uploaded", "review_requested", "archived"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                  statusFilter === st
                    ? "bg-surface-raised text-white border border-surface-borderLight font-semibold"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {st.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-surface border border-surface-border rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-surface-raised/80 border-b border-surface-border text-gray-400 font-mono">
                  <th className="py-3 px-4 font-medium">Document ID & Name</th>
                  <th className="py-3 px-4 font-medium">Version</th>
                  <th className="py-3 px-4 font-medium">Approval Status</th>
                  <th className="py-3 px-4 font-medium">Size</th>
                  <th className="py-3 px-4 font-medium">Chunks Indexed</th>
                  <th className="py-3 px-4 font-medium">Upload Date</th>
                  <th className="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-gray-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
                      Loading policy corpus...
                    </td>
                  </tr>
                ) : filteredDocs.length > 0 ? (
                  filteredDocs.map((doc) => (
                    <tr key={doc.document_id} className="hover:bg-surface-raised/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                          <div className="min-w-0">
                            <p className="font-semibold text-white truncate max-w-[240px]">
                              {doc.original_filename}
                            </p>
                            <p className="text-[10px] font-mono text-gray-500 truncate">
                              {doc.document_id}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-300">
                        v{doc.metadata?.version || "1.0"}
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={doc.metadata?.approval_status || doc.status} size="sm" />
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-400">
                        {doc.file_size_bytes > 0
                          ? `${(doc.file_size_bytes / 1024).toFixed(1)} KB`
                          : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-emerald-400 font-semibold bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                          {doc.chunks_indexed || doc.chunks_created || 0} chunks
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-400 text-[11px]">
                        {doc.upload_timestamp
                          ? new Date(doc.upload_timestamp).toLocaleDateString()
                          : "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/admin/documents/${doc.document_id}`}
                          className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-emerald-400 font-medium inline-flex items-center gap-1.5 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-gray-500">
                      {documents.length === 0
                        ? "No documents uploaded yet. Click 'Upload Documents' to add institutional policies."
                        : `No documents found matching "${searchQuery}".`}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Upload Document Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
            onClick={() => !uploading && setIsUploadModalOpen(false)}
          />

          <div className="relative bg-surface border border-surface-border rounded-2xl max-w-lg w-full p-6 shadow-2xl z-10 space-y-5">
            <div className="flex items-center justify-between border-b border-surface-border pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-emerald-400" />
                Upload Compliance Documents (Single / Multi-PDF)
              </h3>
              <button
                onClick={() => !uploading && setIsUploadModalOpen(false)}
                disabled={uploading}
                className="p-1 rounded-lg text-gray-400 hover:text-white disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-surface-border hover:border-emerald-500/60 rounded-xl p-6 text-center space-y-3 transition-colors bg-surface-raised/40">
                <FileText className="w-8 h-8 mx-auto text-emerald-400" />
                <div>
                  <p className="text-xs text-gray-200 font-medium">
                    {uploadFiles.length > 0
                      ? `${uploadFiles.length} file(s) selected`
                      : "Select or drag & drop policy documents (supports multiple files)"}
                  </p>
                  <p className="text-[11px] text-gray-500 font-mono mt-1">
                    Supports .pdf, .md, .txt, .html (Max 10 MB per file)
                  </p>
                </div>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt,.html,.htm"
                  onChange={(e) => handleFilesSelect(e.target.files)}
                  className="hidden"
                  id="file-input"
                  disabled={uploading}
                />
                <label
                  htmlFor="file-input"
                  className="inline-block px-3.5 py-1.5 rounded-lg bg-surface-raised border border-surface-border text-xs text-emerald-400 hover:text-emerald-300 font-medium cursor-pointer"
                >
                  Browse Files (Select Multiple)
                </label>
              </div>

              {/* Selected Files List */}
              {uploadFiles.length > 0 && (
                <div className="max-h-36 overflow-y-auto space-y-1.5 p-2 bg-surface-raised/60 rounded-xl border border-surface-border">
                  {uploadFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-xs px-2.5 py-1.5 bg-surface rounded-lg border border-surface-border"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span className="text-white truncate max-w-[240px]">{file.name}</span>
                        <span className="text-[10px] font-mono text-gray-400">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      {!uploading && (
                        <button
                          type="button"
                          onClick={() => removeSelectedFile(idx)}
                          className="text-gray-400 hover:text-red-400 ml-2"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {uploadProgress && (
                <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-800 text-blue-300 text-xs flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
                  <span>{uploadProgress}</span>
                </div>
              )}

              {uploadError && (
                <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadSuccess && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(false)}
                  disabled={uploading}
                  className="px-4 py-2 text-xs text-gray-400 hover:text-white disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || uploadFiles.length === 0}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-raised disabled:text-gray-600 text-white font-medium text-xs flex items-center gap-2 shadow-md transition-colors"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Indexing into ChromaDB...</span>
                    </>
                  ) : (
                    <span>Upload & Index {uploadFiles.length > 0 ? `(${uploadFiles.length})` : ""}</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
