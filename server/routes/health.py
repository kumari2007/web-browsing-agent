"""
Health and system diagnostics API endpoints.
Verifies browser subsystem, database accessibility, and LLM readiness.
"""

import time
import sqlite3
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from config import settings
from rag.llm_provider import get_llm_provider

router = APIRouter(prefix="/api", tags=["Health & Config"])
SERVER_START_TIME = time.time()


class UpdateConfigModel(BaseModel):
    llm_provider: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    browser_headless: Optional[bool] = None
    default_search_provider: Optional[str] = None
    read_only_mode: Optional[bool] = None


@router.get("/health")
async def health_check():
    """Application health check across storage, vector database, and browser subsystem."""
    # Check SQLite
    db_ok = False
    try:
        with sqlite3.connect(settings.sqlite_db_path) as conn:
            conn.execute("SELECT 1")
            db_ok = True
    except Exception:
        pass

    # Check Vector Store
    vdb_ok = False
    try:
        with sqlite3.connect(settings.data_dir / "sqlite_vector_store.db") as conn:
            conn.execute("SELECT 1")
            vdb_ok = True
    except Exception:
        pass

    # Check LLM Provider
    provider = get_llm_provider()
    llm_available = provider.is_available()

    uptime_seconds = round(time.time() - SERVER_START_TIME, 1)

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": "NEXUS — Autonomous Web Intelligence Agent",
        "version": "2.0.0",
        "uptime_seconds": uptime_seconds,
        "database_connected": db_ok,
        "vector_store_ready": vdb_ok,
        "llm_provider": settings.llm_provider,
        "llm_available": llm_available,
        "browser_headless": settings.browser_headless
    }


@router.get("/config")
async def get_config():
    """Retrieve non-sensitive runtime configuration parameters."""
    return {
        "llm_provider": settings.llm_provider,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "openai_model": settings.openai_model,
        "has_openai_key": bool(settings.openai_api_key),
        "browser_headless": settings.browser_headless,
        "browser_timeout_ms": settings.browser_timeout_ms,
        "default_search_provider": settings.default_search_provider,
        "max_search_results": settings.max_search_results,
        "default_inspect_pages": settings.default_inspect_pages,
        "max_task_steps": settings.max_task_steps,
        "read_only_mode": settings.read_only_mode,
        "block_private_ips": settings.block_private_ips
    }


@router.post("/config")
async def update_config(update: UpdateConfigModel):
    """Update runtime configuration parameters."""
    if update.llm_provider is not None:
        settings.llm_provider = update.llm_provider
    if update.ollama_base_url is not None:
        settings.ollama_base_url = update.ollama_base_url
    if update.ollama_model is not None:
        settings.ollama_model = update.ollama_model
    if update.openai_api_key is not None:
        settings.openai_api_key = update.openai_api_key
    if update.openai_base_url is not None:
        settings.openai_base_url = update.openai_base_url
    if update.openai_model is not None:
        settings.openai_model = update.openai_model
    if update.browser_headless is not None:
        settings.browser_headless = update.browser_headless
    if update.default_search_provider is not None:
        settings.default_search_provider = update.default_search_provider
    if update.read_only_mode is not None:
        settings.read_only_mode = update.read_only_mode

    return {"status": "updated", "message": "Configuration parameters successfully saved"}
