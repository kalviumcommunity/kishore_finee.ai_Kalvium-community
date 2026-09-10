/**
 * Real API client for FINEE.ai Backend Services.
 * Connects 100% to FastAPI backend endpoints.
 */

import {
  AuditEvent,
  DocumentDetail,
  DocumentRecord,
  KnowledgeBaseData,
  OverviewData,
  QueryRequest,
  QueryResponse,
  TestRetrievalResult,
  UserProfile,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL || "http://127.0.0.1:8000";

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(`[${response.status}] ${errorDetail}`);
  }

  return response.json();
}

export const ragApi = {
  /**
   * Execute similarity search and grounded answer generation with guardrails and citations.
   */
  async askQuestion(payload: QueryRequest): Promise<QueryResponse> {
    return fetchJson<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Upload and dynamically index a compliance document.
   */
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/documents`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Failed to upload document");
    }

    return response.json();
  },

  /**
   * List all tracked documents in the system.
   */
  async getDocuments(): Promise<DocumentRecord[]> {
    return fetchJson<DocumentRecord[]>("/documents");
  },

  /**
   * Get full details and chunk boundary overlays for a document.
   */
  async getDocumentDetail(documentId: string): Promise<DocumentDetail> {
    return fetchJson<DocumentDetail>(`/documents/${documentId}`);
  },

  /**
   * Approve document for production RAG retrieval.
   */
  async approveDocument(documentId: string): Promise<any> {
    return fetchJson(`/documents/${documentId}/approve`, { method: "POST" });
  },

  /**
   * Request compliance review for a document.
   */
  async reviewDocument(documentId: string): Promise<any> {
    return fetchJson(`/documents/${documentId}/review`, { method: "POST" });
  },

  /**
   * Archive document from active search.
   */
  async archiveDocument(documentId: string): Promise<any> {
    return fetchJson(`/documents/${documentId}/archive`, { method: "POST" });
  },

  /**
   * Retrieve high-level overview statistics and activity timeline.
   */
  async getAdminOverview(): Promise<OverviewData> {
    return fetchJson<OverviewData>("/admin/overview");
  },

  /**
   * Retrieve Knowledge Base infrastructure metrics and chunk explorer.
   */
  async getKnowledgeBaseMetrics(query?: string, limit: number = 50): Promise<KnowledgeBaseData> {
    const params = new URLSearchParams();
    if (query) params.append("query", query);
    if (limit) params.append("limit", limit.toString());
    return fetchJson<KnowledgeBaseData>(`/admin/knowledge-base?${params.toString()}`);
  },

  /**
   * Test retrieval directly from the interactive admin console.
   */
  async testRetrieval(payload: {
    query: string;
    top_k?: number;
    min_score?: number;
    use_reranker?: boolean;
  }): Promise<TestRetrievalResult> {
    return fetchJson<TestRetrievalResult>("/admin/test-retrieval", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Retrieve system audit trail events.
   */
  async getActivityLog(eventType?: string, limit: number = 50): Promise<AuditEvent[]> {
    const params = new URLSearchParams();
    if (eventType) params.append("event_type", eventType);
    if (limit) params.append("limit", limit.toString());
    return fetchJson<AuditEvent[]>(`/admin/activity?${params.toString()}`);
  },

  /**
   * Retrieve list of monitored users and their token consumption.
   */
  async getMonitoredUsers(): Promise<UserProfile[]> {
    return fetchJson<UserProfile[]>("/admin/users");
  },

  /**
   * Retrieve query activity and token metrics for a specific user.
   */
  async getUserActivity(userId: string): Promise<any> {
    return fetchJson(`/admin/users/${userId}/activity`);
  },

  /**
   * Retrieve system-wide token usage and cost analytics.
   */
  async getTokenUsageAnalytics(): Promise<any> {
    return fetchJson("/admin/token-usage");
  },

  /**
   * Retrieve current system settings.
   */
  async getSystemSettings(): Promise<any> {
    return fetchJson("/admin/settings");
  },
};
