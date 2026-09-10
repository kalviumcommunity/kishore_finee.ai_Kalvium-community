/**
 * TypeScript Interfaces for FINEE.ai Enterprise Frontend.
 */

export interface CitationSource {
  marker: string;
  source: string;
  document_id: string;
  section: string;
  page: number;
  approval_status: string;
  effective_date: string;
  version: string;
  text: string;
  relevance_score: number;
  is_direct_evidence: boolean;
}

export interface RankedSnippet {
  rank: number;
  type: string;
  source: string;
  section: string;
  page: number;
  approval_status: string;
  score: number;
  text: string;
  marker: string;
}

export interface ConflictSource {
  title: string;
  section: string;
  excerpt: string;
  approval_status: string;
  effective_date: string;
  authority?: string;
}

export interface ConflictDetails {
  title: string;
  description: string;
  source_a: ConflictSource;
  source_b: ConflictSource;
  recommendation: string;
}

export interface PipelineMetrics {
  approved_sources_filtered: number;
  candidates_retrieved: number;
  chunks_synthesized: number;
  top_score: number;
  supporting_chunks_count: number;
  guardrail_status: string;
  reranker_applied: boolean;
}

export interface UsageMetrics {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  cost_usd: number;
  model: string;
}

export interface AuditTrailItem {
  step: string;
  timestamp: string;
  detail: string;
}

export interface MessageHistory {
  role: "user" | "assistant";
  content: string;
}

export interface QueryRequest {
  query: string;
  k?: number;
  min_top_score?: number;
  min_supporting_chunks?: number;
  use_reranker?: boolean;
  history?: MessageHistory[];
  session_id?: string;
  user_id?: string;
  client_context?: {
    entity_name?: string;
    entity_id?: string;
    risk_tier?: string;
    [key: string]: any;
  };
}

export interface QueryResponse {
  answer: string;
  sources: CitationSource[];
  status: "answered" | "refused_weak_context" | "refused_empty_context" | "refused_insufficient_support" | "conflicting_evidence" | string;
  refusal_reason?: string;
  metrics: {
    top_score?: number;
    supporting_chunks_count?: number;
    retrieved_chunks_count?: number;
    llm_called?: boolean;
    [key: string]: any;
  };
  question: string;
  rewritten_query?: string;
  pipeline_metrics?: PipelineMetrics;
  usage?: UsageMetrics;
  has_conflict: boolean;
  conflict_details?: ConflictDetails;
  ranked_snippets: RankedSnippet[];
  audit_trail: AuditTrailItem[];
  history?: MessageHistory[];
}

export interface DocumentRecord {
  document_id: string;
  original_filename: string;
  stored_filename: string;
  upload_timestamp: string;
  status: "uploaded" | "processing" | "indexed" | "failed" | string;
  error_message?: string;
  chunks_created: number;
  chunks_indexed: number;
  file_size_bytes: number;
  content_type?: string;
  completed_at?: string;
  metadata: {
    approval_status?: string;
    version?: string;
    stored_path?: string;
    [key: string]: any;
  };
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  text: string;
  section: string;
  page: number;
  approval_status: string;
  token_count: number;
}

export interface DocumentTimelineItem {
  action: string;
  timestamp: string;
  actor: string;
  status: string;
}

export interface DocumentDetail {
  document_id: string;
  original_filename: string;
  stored_filename: string;
  upload_timestamp: string;
  status: string;
  approval_status: string;
  version: string;
  file_size_bytes: number;
  content_type?: string;
  chunks_count: number;
  chunks: DocumentChunk[];
  metadata: Record<string, any>;
  timeline: DocumentTimelineItem[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  event_type: string;
  description: string;
  status: "SUCCESS" | "WARNING" | "INFO" | "ERROR" | string;
  metadata: Record<string, any>;
}

export interface UserProfile {
  user_id: string;
  name: string;
  role: string;
  department: string;
  email: string;
  queries_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_estimate_usd: number;
  last_active: string;
  refusal_count: number;
  conflict_count: number;
  status: string;
}

export interface OverviewData {
  stats: {
    approved_documents: number;
    processing_documents: number;
    pending_documents: number;
    archived_documents: number;
    total_documents: number;
    total_queries: number;
    refusal_rate_pct: number;
    avg_latency_ms: number;
    conflicts_detected: number;
    active_advisors_count: number;
    system_status: string;
    guardrail_status: string;
    vector_chunks_indexed: number;
  };
  recent_documents: DocumentRecord[];
  activity_timeline: AuditEvent[];
}

export interface PipelineStage {
  name: string;
  status: string;
  throughput: string;
  latency: string;
  health: string;
}

export interface KnowledgeBaseData {
  metrics: {
    total_documents: number;
    total_chunks: number;
    indexed_vectors: number;
    retrieval_ready_pct: number;
    storage_size_kb: number;
    embedding_model: string;
    reranker_enabled: boolean;
    min_guardrail_score: number;
  };
  pipeline_stages: PipelineStage[];
  corpus_health: {
    readiness_pct: number;
    indexed_documents_count: number;
    vector_chunks_count: number;
    approved_chunks_ratio: string;
    average_chunk_token_size: number;
    embedding_dimensions: number;
    distance_metric: string;
    index_type: string;
  };
  chunks: {
    id: string;
    text: string;
    document_id: string;
    source: string;
    chunk_index: number;
    section: string;
    page: number;
    approval_status: string;
    effective_date: string;
    embedding_model: string;
    metadata: Record<string, any>;
  }[];
  total_chunks_count: number;
}

export interface TestRetrievalResult {
  query: string;
  status: string;
  top_score: number;
  supporting_chunks_count: number;
  retrieved_chunks_count: number;
  latency_ms: number;
  chunks: {
    rank: number;
    score: number;
    text: string;
    source: string;
    section: string;
    page: number;
    approval_status: string;
    metadata: Record<string, any>;
  }[];
  refusal_reason?: string;
}
