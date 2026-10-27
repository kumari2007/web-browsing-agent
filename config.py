"""
Central configuration module for the Autonomous Web Browsing Agent.
Loads configuration from environment variables and provides typed settings with defaults.
"""

from pathlib import Path
from typing import Literal, Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    screenshots_dir: Path = BASE_DIR / "data" / "screenshots"
    sqlite_db_path: Path = BASE_DIR / "data" / "agent_memory.db"
    vector_db_dir: Path = BASE_DIR / "data" / "vector_store"
    log_file_path: Path = BASE_DIR / "logs" / "agent.log"

    # LLM Provider Configuration
    llm_provider: Literal["ollama", "openai", "groq", "openrouter", "gemini", "deterministic"] = Field(
        default="ollama"
    )
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2:3b")
    ollama_timeout_seconds: int = Field(default=90)
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # Server & Networking
    server_host: str = Field(default="127.0.0.1")
    server_port: int = Field(default=8000)
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )
    max_navigation_depth: int = Field(default=3)
    execution_timeout_seconds: int = Field(default=180)

    # Embeddings & RAG Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    rag_chunk_size: int = Field(default=600)
    rag_chunk_overlap: int = Field(default=120)
    rag_top_k: int = Field(default=5)
    relevance_threshold: float = Field(default=0.30)

    # Browser Automation Settings
    browser_headless: bool = Field(default=True)
    browser_timeout_ms: int = Field(default=25000)
    browser_navigation_wait_ms: int = Field(default=1500)
    browser_slow_mo_ms: int = Field(default=50)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Search & Exploration Settings
    default_search_provider: Literal["duckduckgo", "bing", "google", "wikipedia"] = Field(
        default="duckduckgo"
    )
    max_search_results: int = Field(default=5)
    default_inspect_pages: int = Field(default=3)

    # Agent Planning & Execution Limits
    max_task_steps: int = Field(default=15)
    max_retry_attempts: int = Field(default=3)
    max_page_chars_to_extract: int = Field(default=25000)

    # Safety & Intervention
    block_private_ips: bool = Field(default=True)
    require_human_confirmation_on_high_risk: bool = Field(default=True)
    read_only_mode: bool = Field(default=True)

    # Logging
    log_level: str = Field(default="INFO")

    def ensure_directories(self) -> None:
        """Create necessary project data and log directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
