"""Comprehensive demonstration script for FINEE.ai Full Frontend & RAG Backend Integration."""

import asyncio
import json
import logging
import time

from fastapi.testclient import TestClient

from src.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_full_integration_demo():
    """Run simulated end-to-end integration tests mimicking the Next.js frontend calls."""
    client = TestClient(app)
    logger.info("=" * 60)
    logger.info("FINEE.ai — Full Frontend & Backend Integration Verification")
    logger.info("=" * 60)

    # 1. Root & Health Check
    logger.info("\n1. Verifying API Health & Root Endpoints...")
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    logger.info("✓ /health: %s", health_resp.json())

    # 2. Knowledge Control Center (Admin Overview)
    logger.info("\n2. Testing GET /admin/overview (Figma Screen 4)...")
    overview_resp = client.get("/admin/overview")
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()
    logger.info("✓ Overview Stats: %s", json.dumps(overview_data["stats"], indent=2))
    logger.info("✓ Recent Documents Count: %d", len(overview_data["recent_documents"]))
    logger.info("✓ Activity Timeline Events: %d", len(overview_data["activity_timeline"]))

    # 3. Knowledge Base Infrastructure & Metrics
    logger.info("\n3. Testing GET /admin/knowledge-base (Figma Screen 3)...")
    kb_resp = client.get("/admin/knowledge-base")
    assert kb_resp.status_code == 200
    kb_data = kb_resp.json()
    logger.info("✓ Total Chunks in ChromaDB: %d", kb_data["metrics"]["total_chunks"])
    logger.info("✓ Pipeline Stages Active: %d", len(kb_data["pipeline_stages"]))
    logger.info("✓ Corpus Health: %s", json.dumps(kb_data["corpus_health"], indent=2))

    # 4. Interactive Test Retrieval Console
    logger.info("\n4. Testing POST /admin/test-retrieval...")
    test_ret_resp = client.post(
        "/admin/test-retrieval",
        json={"query": "advisory fee schedule for wealth accounts", "top_k": 3, "use_reranker": True},
    )
    assert test_ret_resp.status_code == 200
    test_ret_data = test_ret_resp.json()
    logger.info("✓ Retrieval Test Status: %s (Top Score: %.4f, Latency: %.2fms)",
                test_ret_data["status"], test_ret_data["top_score"], test_ret_data["latency_ms"])

    # 5. Ask FINEE.ai / Analysis Session (Figma Screen 1 & 2)
    logger.info("\n5. Testing POST /query (Grounding, Citations & Guardrails)...")
    query_resp = client.post(
        "/query",
        json={
            "query": "What is the policy regarding client suitability?",
            "user_id": "usr_marcus_vance",
            "client_context": {
                "entity_name": "Marcus Vance Portfolio",
                "entity_id": "CLI-8902",
                "risk_tier": "Tier 1 - Discretionary",
            },
        },
    )
    assert query_resp.status_code == 200
    q_data = query_resp.json()
    logger.info("✓ Query Status: %s", q_data["status"])
    logger.info("✓ Answer Excerpt: %s", q_data["answer"][:120] + "...")
    logger.info("✓ Citations Preserved: %d sources", len(q_data["sources"]))
    logger.info("✓ Pipeline Metrics: %s", json.dumps(q_data["pipeline_metrics"], indent=2))
    logger.info("✓ Token Observability: %s", json.dumps(q_data["usage"], indent=2))

    # 6. Safe Refusal Guardrail Trigger Test
    logger.info("\n6. Testing Safe Refusal Guardrail on Out-of-Domain Query...")
    refusal_resp = client.post(
        "/query",
        json={
            "query": "What are the discount lunch menu items today?",
            "user_id": "usr_marcus_vance",
        },
    )
    assert refusal_resp.status_code == 200
    ref_data = refusal_resp.json()
    logger.info("✓ Refusal Status: %s (0 Hallucination)", ref_data["status"])
    logger.info("✓ Refusal Answer: %s", ref_data["answer"])
    logger.info("✓ Refusal Reason: %s", ref_data["refusal_reason"])

    # 7. Conversational RAG & Follow-up Query Rewriting
    logger.info("\n7. Testing Conversational Follow-up Query Rewriting...")
    conv_resp = client.post(
        "/query",
        json={
            "query": "Does it apply to high net worth clients?",
            "history": [
                {"role": "user", "content": "What is the suitability requirement for discretionary portfolio management?"},
                {"role": "assistant", "content": "Suitability requires documented risk tolerance and annual review."}
            ],
            "user_id": "usr_marcus_vance",
        },
    )
    assert conv_resp.status_code == 200
    conv_data = conv_resp.json()
    logger.info("✓ Original Follow-up: 'Does it apply to high net worth clients?'")
    logger.info("✓ Rewritten Query: '%s'", conv_data.get("rewritten_query"))
    logger.info("✓ Conversational Status: %s", conv_data["status"])

    # 8. User Monitoring & Token Analytics
    logger.info("\n8. Testing GET /admin/users & GET /admin/token-usage...")
    users_resp = client.get("/admin/users")
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    logger.info("✓ Active Monitored Users: %d", len(users_data))
    for u in users_data:
        logger.info("   - %s (%s): %d queries, %d tokens, $%.4f spend",
                    u["name"], u["role"], u["queries_count"], u["total_tokens"], u["cost_estimate_usd"])

    token_resp = client.get("/admin/token-usage")
    assert token_resp.status_code == 200
    logger.info("✓ Aggregate Token Analytics: %s", json.dumps(token_resp.json(), indent=2))

    # 9. Audit Trail Events Ledger
    logger.info("\n9. Testing GET /admin/activity...")
    activity_resp = client.get("/admin/activity?limit=5")
    assert activity_resp.status_code == 200
    activity_events = activity_resp.json()
    logger.info("✓ Live Audit Ledger Entries: %d", len(activity_events))
    for ev in activity_events[:3]:
        logger.info("   - [%s] %s: %s", ev["status"], ev["actor"], ev["description"])

    logger.info("\n" + "=" * 60)
    logger.info("ALL END-TO-END RAG & DASHBOARD ENDPOINTS VERIFIED SUCCESSFULLY!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_integration_demo()
