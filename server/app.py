"""
NEXUS FastAPI Application Server.
Mounts REST endpoints, WebSockets, CORS, and screenshot asset serving.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings

from server.routes.tasks import router as tasks_router
from server.routes.metrics import router as metrics_router
from server.routes.memory import router as memory_router
from server.routes.knowledge import router as knowledge_router
from server.routes.safety import router as safety_router
from server.routes.health import router as health_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("server.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and teardown tasks."""
    logger.info("Initializing NEXUS Autonomous Web Intelligence Agent Server...")
    settings.ensure_directories()
    yield
    logger.info("Shutting down NEXUS server...")


app = FastAPI(
    title="NEXUS — Autonomous Web Intelligence Agent",
    description="Production-grade autonomous web browsing agent with RAG, self-correction, and safety policies.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount screenshots directory for live browser view
settings.screenshots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/screenshots", StaticFiles(directory=str(settings.screenshots_dir)), name="screenshots")

# Register routers
app.include_router(tasks_router)
app.include_router(metrics_router)
app.include_router(memory_router)
app.include_router(knowledge_router)
app.include_router(safety_router)
app.include_router(health_router)

# Mount compiled React frontend if present
dist_dir = settings.base_dir / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False
    )
