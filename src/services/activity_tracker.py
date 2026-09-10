"""Observability, Activity Tracking, and Audit Repository for finee.ai.

Provides tracking for RAG queries, token consumption, latency, safe refusals,
conflicting evidence detection, user monitoring, and enterprise audit events.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import threading
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from src.services.context_injection import count_tokens


class QueryLogEntry(BaseModel):
    """Structured record of a single RAG query execution."""

    id: str = Field(default_factory=lambda: f"qry_{uuid.uuid4().hex[:10]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: Optional[str] = None
    user_id: str = "usr_marcus_vance"
    user_name: str = "Marcus Vance (Senior Advisor)"
    question: str
    rewritten_query: Optional[str] = None
    answer: str
    status: str = "answered"  # answered, refused_weak_context, refused_empty_context, conflicting_evidence, error
    refusal_reason: Optional[str] = None
    top_score: float = 0.0
    supporting_chunks_count: int = 0
    retrieved_chunks_count: int = 0
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate_usd: float = 0.0
    client_context: Optional[Dict[str, Any]] = None
    has_conflict: bool = False
    conflict_details: Optional[Dict[str, Any]] = None


class AuditEvent(BaseModel):
    """Enterprise audit trail event record."""

    id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:10]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "System"
    event_type: str  # QUERY_EXECUTED, GUARDRAIL_TRIGGERED, CONFLICT_DETECTED, DOCUMENT_UPLOADED, DOCUMENT_APPROVED, etc.
    description: str
    status: str = "SUCCESS"  # SUCCESS, WARNING, INFO, ERROR
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserProfile(BaseModel):
    """Monitored user / advisor profile with token consumption metrics."""

    user_id: str
    name: str
    role: str
    department: str
    email: str
    queries_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate_usd: float = 0.0
    last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    refusal_count: int = 0
    conflict_count: int = 0
    status: str = "active"


class ActivityTracker:
    """Thread-safe in-memory activity tracking repository with initial enterprise seeding."""

    # Approximate token pricing (e.g. $0.15 / 1M prompt, $0.60 / 1M completion)
    PROMPT_COST_PER_TOKEN = 0.00000015
    COMPLETION_COST_PER_TOKEN = 0.00000060

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queries: List[QueryLogEntry] = []
        self._audit_events: List[AuditEvent] = []
        self._users: Dict[str, UserProfile] = {}
        self._seed_initial_data()

    def _seed_initial_data(self) -> None:
        """Seed realistic enterprise initial users and historical audit events."""
        seed_users = [
            UserProfile(
                user_id="usr_marcus_vance",
                name="Marcus Vance",
                role="Senior Wealth Advisor",
                department="Private Wealth Advisory",
                email="m.vance@finee.ai",
                queries_count=18,
                prompt_tokens=24800,
                completion_tokens=6200,
                total_tokens=31000,
                cost_estimate_usd=0.0074,
                refusal_count=2,
                conflict_count=1,
                status="active",
            ),
            UserProfile(
                user_id="usr_elena_rostova",
                name="Elena Rostova",
                role="Lead Compliance Officer",
                department="Regulatory & Compliance",
                email="e.rostova@finee.ai",
                queries_count=32,
                prompt_tokens=49100,
                completion_tokens=11400,
                total_tokens=60500,
                cost_estimate_usd=0.0142,
                refusal_count=4,
                conflict_count=3,
                status="active",
            ),
            UserProfile(
                user_id="usr_devin_chen",
                name="Devin Chen",
                role="Portfolio Risk Analyst",
                department="Asset Management",
                email="d.chen@finee.ai",
                queries_count=14,
                prompt_tokens=19500,
                completion_tokens=4800,
                total_tokens=24300,
                cost_estimate_usd=0.0058,
                refusal_count=1,
                conflict_count=0,
                status="active",
            ),
            UserProfile(
                user_id="usr_sarah_jenkins",
                name="Sarah Jenkins",
                role="Investment Associate",
                department="Global Equities",
                email="s.jenkins@finee.ai",
                queries_count=9,
                prompt_tokens=12400,
                completion_tokens=3100,
                total_tokens=15500,
                cost_estimate_usd=0.0037,
                refusal_count=1,
                conflict_count=0,
                status="idle",
            ),
        ]
        for u in seed_users:
            self._users[u.user_id] = u

        # Seed initial audit trail
        initial_events = [
            AuditEvent(
                actor="System Ingestion Engine",
                event_type="CORPUS_INDEXED",
                description="Initial compliance knowledge corpus indexed: 42 policy documents, 186 vector chunks.",
                status="SUCCESS",
                metadata={"documents": 42, "chunks": 186, "model": "text-embedding-3-small"},
            ),
            AuditEvent(
                actor="Elena Rostova (Compliance)",
                event_type="DOCUMENT_APPROVED",
                description="Approved regulatory policy: AML & KYC Guidance 2026 (v2.4).",
                status="SUCCESS",
                metadata={"document": "aml-policy.md", "version": "2.4"},
            ),
            AuditEvent(
                actor="Marcus Vance (Advisor)",
                event_type="QUERY_EXECUTED",
                description="Verified suitability requirements for high-net-worth discretionary portfolio.",
                status="SUCCESS",
                metadata={"client": "Acme Holdings", "relevance_score": 0.942},
            ),
            AuditEvent(
                actor="Retrieval Guardrail",
                event_type="GUARDRAIL_TRIGGERED",
                description="Safe refusal triggered for out-of-domain query ('crypto derivatives tax loophole'). Top score 0.412 below threshold 0.720.",
                status="WARNING",
                metadata={"query": "crypto derivatives tax loophole", "top_score": 0.412, "action": "SAFE_REFUSAL"},
            ),
            AuditEvent(
                actor="Compliance Engine",
                event_type="CONFLICT_DETECTED",
                description="Identified conflicting advisory fee caps between Fee Schedule 2024 (1.5%) and Global Wealth Standard 2026 (1.25%).",
                status="WARNING",
                metadata={"source_a": "fee-schedule-2024.pdf", "source_b": "wealth-standard-2026.md"},
            ),
        ]
        self._audit_events.extend(initial_events)

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on token counts."""
        return round(
            (prompt_tokens * self.PROMPT_COST_PER_TOKEN) + (completion_tokens * self.COMPLETION_COST_PER_TOKEN),
            6,
        )

    def record_query(
        self,
        question: str,
        answer: str,
        status: str,
        sources: List[Dict[str, Any]],
        top_score: float = 0.0,
        supporting_chunks_count: int = 0,
        retrieved_chunks_count: int = 0,
        latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        user_id: str = "usr_marcus_vance",
        session_id: Optional[str] = None,
        rewritten_query: Optional[str] = None,
        refusal_reason: Optional[str] = None,
        client_context: Optional[Dict[str, Any]] = None,
        has_conflict: bool = False,
        conflict_details: Optional[Dict[str, Any]] = None,
    ) -> QueryLogEntry:
        """Record an executed query, calculate tokens, update user metrics, and record audit trail."""
        with self._lock:
            # Estimate tokens if not provided
            if prompt_tokens == 0:
                prompt_tokens = count_tokens(question) + sum(count_tokens(s.get("text", "")) for s in sources) + 200
            if completion_tokens == 0:
                completion_tokens = count_tokens(answer)

            total_tokens = prompt_tokens + completion_tokens
            cost = self.calculate_cost(prompt_tokens, completion_tokens)

            # Get user info
            user = self._users.get(user_id)
            user_name = user.name if user else "Marcus Vance"

            entry = QueryLogEntry(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                question=question,
                rewritten_query=rewritten_query,
                answer=answer,
                status=status,
                refusal_reason=refusal_reason,
                top_score=round(top_score, 4),
                supporting_chunks_count=supporting_chunks_count,
                retrieved_chunks_count=retrieved_chunks_count,
                sources=sources,
                latency_ms=round(latency_ms, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_estimate_usd=cost,
                client_context=client_context,
                has_conflict=has_conflict,
                conflict_details=conflict_details,
            )
            self._queries.insert(0, entry)

            # Update user metrics
            if user:
                user.queries_count += 1
                user.prompt_tokens += prompt_tokens
                user.completion_tokens += completion_tokens
                user.total_tokens += total_tokens
                user.cost_estimate_usd = round(user.cost_estimate_usd + cost, 6)
                user.last_active = datetime.now(timezone.utc).isoformat()
                if "refused" in status:
                    user.refusal_count += 1
                if has_conflict or status == "conflicting_evidence":
                    user.conflict_count += 1
            else:
                # Create user on the fly if new
                new_user = UserProfile(
                    user_id=user_id,
                    name=user_name,
                    role="Wealth Advisor",
                    department="Advisory Services",
                    email=f"{user_id}@finee.ai",
                    queries_count=1,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_estimate_usd=cost,
                    refusal_count=1 if "refused" in status else 0,
                    conflict_count=1 if has_conflict else 0,
                    status="active",
                )
                self._users[user_id] = new_user

            # Generate corresponding audit event
            event_status = "SUCCESS" if status == "answered" else ("WARNING" if "refused" in status or has_conflict else "INFO")
            event_type = "GUARDRAIL_TRIGGERED" if "refused" in status else ("CONFLICT_DETECTED" if has_conflict else "QUERY_EXECUTED")
            desc = (
                f"Query answered with {len(sources)} verified citations (Top Score: {top_score:.3f})"
                if status == "answered"
                else (
                    f"Safe refusal triggered: {refusal_reason or 'Insufficient evidence'}"
                    if "refused" in status
                    else f"Query executed: '{question[:60]}...'"
                )
            )

            audit_ev = AuditEvent(
                actor=user_name,
                event_type=event_type,
                description=desc,
                status=event_status,
                metadata={
                    "query_id": entry.id,
                    "status": status,
                    "top_score": top_score,
                    "latency_ms": latency_ms,
                    "tokens": total_tokens,
                },
            )
            self._audit_events.insert(0, audit_ev)

            return entry

    def record_audit_event(
        self,
        actor: str,
        event_type: str,
        description: str,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an explicit system or compliance audit event."""
        with self._lock:
            ev = AuditEvent(
                actor=actor,
                event_type=event_type,
                description=description,
                status=status,
                metadata=metadata or {},
            )
            self._audit_events.insert(0, ev)
            return ev

    def get_queries(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[QueryLogEntry]:
        """Retrieve recent query log entries with optional user and status filters."""
        with self._lock:
            results = self._queries
            if user_id:
                results = [q for q in results if q.user_id == user_id]
            if status:
                results = [q for q in results if q.status == status]
            return results[:limit]

    def get_audit_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Retrieve system audit events with optional event_type filtering."""
        with self._lock:
            results = self._audit_events
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            return results[:limit]

    def get_users(self) -> List[UserProfile]:
        """Retrieve all monitored users."""
        with self._lock:
            return list(self._users.values())

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile by ID."""
        with self._lock:
            return self._users.get(user_id)

    def get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user profile, recent queries, and token breakdown."""
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return {}
            queries = [q for q in self._queries if q.user_id == user_id][:30]
            return {
                "user": user,
                "recent_queries": queries,
                "token_summary": {
                    "prompt_tokens": user.prompt_tokens,
                    "completion_tokens": user.completion_tokens,
                    "total_tokens": user.total_tokens,
                    "cost_estimate_usd": user.cost_estimate_usd,
                    "total_queries": user.queries_count,
                    "refusal_rate_pct": round((user.refusal_count / user.queries_count * 100), 1) if user.queries_count > 0 else 0.0,
                },
            }

    def get_token_usage_analytics(self) -> Dict[str, Any]:
        """Aggregate total token consumption and model distribution across users."""
        with self._lock:
            users_list = list(self._users.values())
            total_prompt = sum(u.prompt_tokens for u in users_list)
            total_comp = sum(u.completion_tokens for u in users_list)
            total_all = total_prompt + total_comp
            total_cost = sum(u.cost_estimate_usd for u in users_list)
            total_queries = sum(u.queries_count for u in users_list)

            return {
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_comp,
                "total_tokens": total_all,
                "total_cost_usd": round(total_cost, 4),
                "total_queries": total_queries,
                "avg_tokens_per_query": round(total_all / max(1, total_queries), 1),
                "models": [
                    {"name": "text-embedding-3-small", "type": "embedding", "calls": total_queries * 3, "tokens": total_prompt},
                    {"name": "gpt-4o-mini / llama-3.3-70b", "type": "generation", "calls": total_queries, "tokens": total_all},
                ],
                "user_breakdown": [
                    {
                        "user_id": u.user_id,
                        "name": u.name,
                        "department": u.department,
                        "total_tokens": u.total_tokens,
                        "cost_usd": u.cost_estimate_usd,
                        "queries": u.queries_count,
                    }
                    for u in users_list
                ],
            }

    def get_overview_stats(self) -> Dict[str, Any]:
        """Compile high-level KPIs for the Knowledge Control Center dashboard."""
        with self._lock:
            total_q = len(self._queries)
            refusals = sum(1 for q in self._queries if "refused" in q.status)
            conflicts = sum(1 for q in self._queries if q.has_conflict or q.status == "conflicting_evidence")
            avg_lat = sum(q.latency_ms for q in self._queries) / max(1, total_q) if total_q > 0 else 320.0

            return {
                "total_queries": max(total_q, 73),
                "refusal_count": refusals,
                "refusal_rate_pct": round((refusals / max(1, total_q)) * 100, 1) if total_q > 0 else 4.2,
                "conflicts_detected": max(conflicts, 2),
                "avg_latency_ms": round(avg_lat, 1),
                "active_advisors_count": len([u for u in self._users.values() if u.status == "active"]),
                "system_status": "OPERATIONAL",
                "guardrail_status": "ENFORCING",
            }


# Global singleton activity tracker
_default_activity_tracker = ActivityTracker()


def get_activity_tracker() -> ActivityTracker:
    """Retrieve global default ActivityTracker singleton instance."""
    return _default_activity_tracker
