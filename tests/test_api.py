"""
Automated tests for NEXUS FastAPI backend endpoints.
Verifies task creation, listings, metric calculations, memory operations,
knowledge base ingestion and search, export functions, and safety status.
"""

import pytest
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_frontend_serving():
    """Verify frontend static single page application is mounted and accessible."""
    res = client.get("/")
    assert res.status_code == 200
    assert "NEXUS" in res.text


def test_health_check():
    """Verify health endpoint reports application status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["app_name"] == "NEXUS — Autonomous Web Intelligence Agent"
    assert "uptime_seconds" in data
    assert "database_connected" in data


def test_get_config():
    """Verify config endpoint returns configuration."""
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "llm_provider" in data
    assert "browser_headless" in data


def test_update_config():
    """Verify runtime configuration update."""
    res = client.post("/api/config", json={"browser_headless": True})
    assert res.status_code == 200
    assert res.json()["status"] == "updated"


def test_list_tasks():
    """Verify task listing returns an array."""
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_task_not_found():
    """Verify 404 for nonexistent task."""
    res = client.get("/api/tasks/nonexistent-task-id-12345")
    assert res.status_code == 404


def test_metrics_summary():
    """Verify metrics summary endpoint calculates proper fields."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_tasks" in data
    assert "success_rate" in data
    assert "avg_duration_seconds" in data
    assert "recovery_rate" in data
    assert "evidence_coverage_avg" in data


def test_experience_memory_endpoints():
    """Verify experience memory listing and advice."""
    res = client.get("/api/memory")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    advice_res = client.get("/api/memory/advice?topic=wikipedia")
    assert advice_res.status_code == 200
    adv = advice_res.json()
    assert "recommended" in adv
    assert "avoid" in adv


def test_safety_endpoints():
    """Verify safety center configuration and intervention listing."""
    res = client.get("/api/safety")
    assert res.status_code == 200
    data = res.json()
    assert data["captcha_detection_active"] is True
    assert "allowed_schemes" in data
    assert "blocked_schemes" in data

    iv_res = client.get("/api/safety/interventions")
    assert iv_res.status_code == 200
    assert "total_requests" in iv_res.json()


def test_knowledge_base_ingestion_and_search():
    """Verify document upload, listing, search, and deletion in RAG."""
    # 1. Ingest sample text document
    file_content = (
        "NEXUS is an autonomous web intelligence and research agent developed for deep exploration. "
        "It supports 10 advanced features including self-correction, relevance search, and RAG."
    )
    files = {"file": ("nexus_overview.txt", file_content.encode("utf-8"), "text/plain")}
    upload_res = client.post("/api/knowledge/upload", files=files)
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert upload_data["status"] == "indexed"
    assert upload_data["chunk_count"] > 0
    doc_id = upload_data["doc_id"]

    # 2. List documents
    list_res = client.get("/api/knowledge")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["doc_id"] == doc_id or "nexus_overview.txt" in d["title"] for d in docs)

    # 3. Search knowledge
    search_res = client.post("/api/knowledge/search", json={"query": "autonomous web intelligence agent", "top_k": 3})
    assert search_res.status_code == 200
    sdata = search_res.json()
    assert sdata["count"] > 0
    assert "NEXUS" in sdata["results"][0]["text"]
    assert sdata["results"][0]["source_type"] == "local_document"

    # 4. Clean up / delete document
    del_res = client.delete(f"/api/knowledge/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
