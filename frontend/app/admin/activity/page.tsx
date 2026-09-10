"use client";

import React, { useState, useEffect } from "react";
import {
  History,
  Shield,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  AlertTriangle,
  CheckCircle,
  FileText,
  Database,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { AuditEvent } from "@/types";

export default function ActivityAuditTrailPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchEvents = async (eventType?: string) => {
    try {
      setLoading(true);
      const res = await ragApi.getActivityLog(eventType === "all" ? undefined : eventType);
      setEvents(res);
    } catch (err) {
      console.error("Failed to load audit events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents(filterType);
  }, [filterType]);

  const filteredEvents = events.filter((ev) => {
    const matchesSearch =
      ev.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.event_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="Audit Trail & System Activity"
        subtitle="Compliance Trace Logs • Guardrail Decisions • Execution Provenance"
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">System Audit & Trace Log</h2>
            <p className="text-xs text-gray-400 font-mono">
              Immutable ledger of advisory queries, guardrail refusals, and document lifecycle events
            </p>
          </div>
          <button
            onClick={() => fetchEvents(filterType)}
            className="px-3.5 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-xs text-gray-300 flex items-center gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Ledger</span>
          </button>
        </div>

        {/* Filter & Search */}
        <div className="bg-surface border border-surface-border rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search audit descriptions, actors, queries..."
              className="w-full bg-surface-raised border border-surface-border rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex items-center gap-1.5 self-start md:self-auto overflow-x-auto w-full md:w-auto">
            {["all", "QUERY_EXECUTED", "GUARDRAIL_TRIGGERED", "CONFLICT_DETECTED", "DOCUMENT_UPLOADED", "DOCUMENT_APPROVED"].map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono uppercase tracking-wider transition-colors ${
                  filterType === t
                    ? "bg-surface-raised text-emerald-400 border border-emerald-800/60 font-semibold"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {t === "all" ? "All Events" : t.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Events Table */}
        <div className="bg-surface border border-surface-border rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-surface-raised/80 border-b border-surface-border text-gray-400 font-mono">
                  <th className="py-3 px-4 font-medium">Timestamp</th>
                  <th className="py-3 px-4 font-medium">Actor</th>
                  <th className="py-3 px-4 font-medium">Event Type</th>
                  <th className="py-3 px-4 font-medium">Description & Diagnostic Detail</th>
                  <th className="py-3 px-4 font-medium">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
                      Loading audit ledger...
                    </td>
                  </tr>
                ) : filteredEvents.length > 0 ? (
                  filteredEvents.map((ev) => (
                    <tr key={ev.id} className="hover:bg-surface-raised/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-gray-400 text-[11px] whitespace-nowrap">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : "Just now"}
                      </td>
                      <td className="py-3 px-4 font-semibold text-white whitespace-nowrap flex items-center gap-2">
                        <User className="w-3.5 h-3.5 text-gray-400" />
                        <span>{ev.actor}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-surface-raised border border-surface-border text-emerald-400">
                          {ev.event_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-200 leading-relaxed max-w-lg">
                        <p>{ev.description}</p>
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={ev.status} size="sm" />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-500">
                      No audit events found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
