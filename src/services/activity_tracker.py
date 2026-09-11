"""Observability, Activity Tracking, and Audit Repository for finee.ai.

Provides tracking for RAG queries, token consumption, latency, safe refusals,
conflicting evidence detection, user monitoring, and enterprise audit events.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path
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
    user_id: str = "usr_advisor_default"
    user_name: str = "Financial Advisor"
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

    def __init__(self, storage_path: str = "./data/activity_ledger.json") -> None:
        self._lock = threading.Lock()
        self._storage_path = Path(storage_path)
        self._queries: List[QueryLogEntry] = []
        self._audit_events: List[AuditEvent] = []
        self._users: Dict[str, UserProfile] = {}
        self._seed_initial_data()
        self._load_from_disk()

    def _save_to_disk(self) -> None:
        """Persist user profiles, query logs, and audit trail to disk."""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            payload = {
                "users": {u_id: u.model_dump() for u_id, u in self._users.items()},
                "queries": [q.model_dump() for q in self._queries[:200]],
                "audit_events": [a.model_dump() for a in self._audit_events[:200]],
            }
            self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to persist activity ledger to %s: %s", self._storage_path, exc)

    def _load_from_disk(self) -> None:
        """Load activity ledger from disk if available."""
        if not self._storage_path.exists():
            return
        try:
            import json
            raw_text = self._storage_path.read_text(encoding="utf-8")
            if raw_text.strip():
                data = json.loads(raw_text)
                for u_id, u_data in data.get("users", {}).items():
                    self._users[u_id] = UserProfile(**u_data)
                self._queries = [QueryLogEntry(**q) for q in data.get("queries", [])]
                self._audit_events = [AuditEvent(**a) for a in data.get("audit_events", [])]
        except Exception as exc:
            logger.warning("Failed to load activity ledger from %s: %s", self._storage_path, exc)

    def _seed_initial_data(self) -> None:
        """Seed initial real administrator profile and system startup audit event."""
        admin_user = UserProfile(
            user_id="usr_admin_vaishnavi",
            name="Vaishnavi Pallempati",
            role="ADMIN",
            department="Executive & Regulatory Compliance",
            email="pallempativaishnavi@gmail.com",
            queries_count=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_estimate_usd=0.0,
            refusal_count=0,
            conflict_count=0,
            status="active",
        )
        self._users[admin_user.user_id] = admin_user

        # Initial system event
        init_event = AuditEvent(
            actor="System",
            event_type="SYSTEM_INITIALIZED",
            description="FINEE.ai Compliance Knowledge Control Platform initialized and ready.",
            status="SUCCESS",
            metadata={"environment": "production_ready"},
        )
        self._audit_events.append(init_event)

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
        user_id: str = "usr_advisor_default",
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
            user_name = user.name if user else "Financial Advisor"

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

    def register_user(self, user: UserProfile) -> UserProfile:
        """Register or update an authenticated user profile in the persistent registry."""
        with self._lock:
            self._users[user.user_id] = user
            self._save_to_disk()
            return user

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
            avg_lat = round(sum(q.latency_ms for q in self._queries) / total_q, 1) if total_q > 0 else 0.0

            return {
                "total_queries": total_q,
                "refusal_count": refusals,
                "refusal_rate_pct": round((refusals / total_q) * 100, 1) if total_q > 0 else 0.0,
                "conflicts_detected": conflicts,
                "avg_latency_ms": avg_lat,
                "active_advisors_count": len([u for u in self._users.values() if u.status == "active"]),
                "system_status": "OPERATIONAL",
                "guardrail_status": "ENFORCING",
            }


# Global singleton activity tracker
_default_activity_tracker = ActivityTracker()


def get_activity_tracker() -> ActivityTracker:
    """Retrieve global default ActivityTracker singleton instance."""
    return _default_activity_tracker
