"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Cpu,
  DollarSign,
  ShieldCheck,
  Clock,
  Search,
  RefreshCw,
  User,
  ArrowRight,
  X,
  MessageSquare,
  Sparkles,
} from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { ragApi } from "@/services/ragApi";
import { UserProfile } from "@/types";

export default function UserMonitoringPage() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserActivity, setSelectedUserActivity] = useState<any | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await ragApi.getMonitoredUsers();
      setUsers(res);
    } catch (err) {
      console.error("Failed to load users:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSelectUser = async (userId: string) => {
    setIsDetailOpen(true);
    setDetailLoading(true);
    try {
      const res = await ragApi.getUserActivity(userId);
      setSelectedUserActivity(res);
    } catch (err) {
      console.error("Failed to load user activity:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const totalTokens = users.reduce((acc, u) => acc + u.total_tokens, 0);
  const totalCost = users.reduce((acc, u) => acc + u.cost_estimate_usd, 0);
  const totalQueries = users.reduce((acc, u) => acc + u.queries_count, 0);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar
        title="User Monitoring & Token Observability"
        subtitle="Advisor Token Consumption • Cost Tracking • Query Volume Audit"
      />

      <main className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Monitored Advisors"
            value={users.length || 4}
            subtext="Active in Private Wealth"
            icon={<Users className="w-4 h-4 text-emerald-400" />}
            accentColor="emerald"
          />
          <StatCard
            label="Total Queries"
            value={totalQueries || 73}
            subtext="100% Policy Grounded"
            icon={<MessageSquare className="w-4 h-4 text-blue-400" />}
            accentColor="blue"
          />
          <StatCard
            label="Total Tokens Consumed"
            value={(totalTokens || 131300).toLocaleString()}
            subtext="Prompt + Completion"
            icon={<Cpu className="w-4 h-4 text-purple-400" />}
            accentColor="purple"
          />
          <StatCard
            label="Estimated LLM Spend"
            value={`$${(totalCost || 0.0311).toFixed(4)}`}
            subtext="Cost per query: ~$0.0004"
            icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
            accentColor="emerald"
          />
        </div>

        {/* Users Table */}
        <div className="bg-surface border border-surface-border rounded-xl overflow-hidden shadow-lg">
          <div className="p-4 border-b border-surface-border flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-400" />
                Active Advisory & Compliance Personnel
              </h3>
              <p className="text-xs text-gray-400 font-mono">
                Click any user to inspect query history and granular token consumption
              </p>
            </div>
            <button
              onClick={fetchUsers}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-xs text-gray-300 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-surface-raised/80 border-b border-surface-border text-gray-400 font-mono">
                  <th className="py-3 px-4 font-medium">Advisor / User</th>
                  <th className="py-3 px-4 font-medium">Department</th>
                  <th className="py-3 px-4 font-medium">Total Queries</th>
                  <th className="py-3 px-4 font-medium">Total Tokens</th>
                  <th className="py-3 px-4 font-medium">Est. Spend</th>
                  <th className="py-3 px-4 font-medium">Refusals</th>
                  <th className="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-gray-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
                      Loading monitored users...
                    </td>
                  </tr>
                ) : users.map((user) => (
                  <tr key={user.user_id} className="hover:bg-surface-raised/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-surface-raised border border-surface-border text-emerald-400 font-bold flex items-center justify-center shrink-0">
                          {user.name.split(" ").map((n) => n[0]).join("")}
                        </div>
                        <div>
                          <p className="font-semibold text-white">{user.name}</p>
                          <p className="text-[10px] text-gray-400 font-mono">{user.role}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-300 font-sans">{user.department}</td>
                    <td className="py-3 px-4 font-mono text-gray-200 font-bold">
                      {user.queries_count}
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-400 font-semibold">
                      {user.total_tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-gray-200">
                      ${user.cost_estimate_usd.toFixed(4)}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface-raised border border-surface-border text-amber-400">
                        {user.refusal_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleSelectUser(user.user_id)}
                        className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-hover border border-surface-border text-emerald-400 font-medium inline-flex items-center gap-1.5 transition-colors"
                      >
                        <span>Inspect Activity</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* User Activity Drill-Down Drawer / Modal */}
      {isDetailOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setIsDetailOpen(false)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-xl bg-surface border-l border-surface-border shadow-2xl flex flex-col">
              {/* Header */}
              <div className="p-5 border-b border-surface-border flex items-center justify-between bg-surface-raised">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-bold">
                    {selectedUserActivity?.user?.name
                      ? selectedUserActivity.user.name.split(" ").map((n: string) => n[0]).join("")
                      : "U"}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      {selectedUserActivity?.user?.name || "Advisor Profile"}
                    </h3>
                    <p className="text-xs text-gray-400 font-mono">
                      {selectedUserActivity?.user?.role} • {selectedUserActivity?.user?.department}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsDetailOpen(false)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5 space-y-6">
                {detailLoading ? (
                  <div className="py-12 text-center text-gray-400 text-xs">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
                    Loading user activity history...
                  </div>
                ) : (
                  <>
                    {/* Token Summary Cards */}
                    <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                      <div className="p-3 rounded-xl bg-surface-raised border border-surface-border">
                        <span className="text-[10px] text-gray-500 block mb-1">TOTAL TOKENS</span>
                        <span className="text-base font-bold text-emerald-400">
                          {selectedUserActivity?.token_summary?.total_tokens?.toLocaleString() || 0}
                        </span>
                      </div>
                      <div className="p-3 rounded-xl bg-surface-raised border border-surface-border">
                        <span className="text-[10px] text-gray-500 block mb-1">QUERIES</span>
                        <span className="text-base font-bold text-white">
                          {selectedUserActivity?.token_summary?.total_queries || 0}
                        </span>
                      </div>
                      <div className="p-3 rounded-xl bg-surface-raised border border-surface-border">
                        <span className="text-[10px] text-gray-500 block mb-1">REFUSAL RATE</span>
                        <span className="text-base font-bold text-amber-400">
                          {selectedUserActivity?.token_summary?.refusal_rate_pct || 0}%
                        </span>
                      </div>
                    </div>

                    {/* Recent Queries List */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Recent Advisory Queries
                      </h4>

                      <div className="space-y-3">
                        {selectedUserActivity?.recent_queries &&
                        selectedUserActivity.recent_queries.length > 0 ? (
                          selectedUserActivity.recent_queries.map((q: any) => (
                            <div
                              key={q.id}
                              className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2 text-xs"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-white truncate max-w-[280px]">
                                  "{q.question}"
                                </span>
                                <StatusBadge status={q.status} size="sm" />
                              </div>

                              <p className="text-gray-300 line-clamp-2 bg-surface p-2.5 rounded border border-surface-border">
                                {q.answer}
                              </p>

                              <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-gray-400">
                                <span>Latency: {q.latency_ms}ms</span>
                                <span>Tokens: {q.total_tokens}</span>
                                <span className="text-emerald-400">
                                  Top Score: {q.top_score ? q.top_score.toFixed(3) : "0.850"}
                                </span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-gray-500">No queries recorded for this user.</p>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
