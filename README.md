# NEXUS — Autonomous Web Intelligence Agent

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB.svg)](https://react.dev/)
[![Playwright](https://img.shields.io/badge/Automation-Playwright%20Chromium-45ba4b.svg)](https://playwright.dev/)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-40%20Passed-brightgreen.svg)](https://pytest.org/)

**NEXUS** is an industrial-grade, full-stack autonomous web intelligence and research agent. It accepts natural-language goals, formulates structured execution plans, searches the web across multiple providers, navigates deep into destination websites using Playwright, extracts structured facts (specs, prices, ratings, tables), indexes content in a persistent hybrid RAG vector store, self-corrects failures, and synthesizes evidence-grounded answers with clickable source citations.

---

## 🏗️ System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                 NEXUS FRONTEND (React + Vite + TypeScript)                        |
|   [Overview] [New Task] [Live Browser] [Task History] [Knowledge Base] [Memory] [Analytics] [Safety] |
+--------------------------------------------------+------------------------------------------------+
                                                   |  REST APIs + WebSockets
                                                   v
+---------------------------------------------------------------------------------------------------+
|                                      FASTAPI REST & WEBSOCKET GATEWAY                             |
|        (/api/tasks, /api/metrics, /api/memory, /api/knowledge, /api/safety, /api/health)         |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|                                  BACKGROUND TASK MANAGER & ORCHESTRATOR                           |
|       Non-blocking AsyncIO worker thread dispatch, real-time WebSocket state broadcaster          |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|                                      CORE AUTONOMOUS AGENT LOOP                                   |
|             PERCEIVE ──> PLAN ──> ASSESS RISK ──> ACT ──> OBSERVE ──> VERIFY ──> REPEAT           |
+---------------------------------------------------------------------------------------------------+
      |                    |                      |                        |
      v                    v                      v                        v
+------------+     +--------------+      +---------------+      +-------------------+
|  PLANNER   |     |   EXECUTOR   |      |   OBSERVER    |      |  SELF-CORRECTION  |
| - Decompose|     | - Telemetry  |      | - DOM State   |      | - Bounded retries |
| - Classify |     | - Dispatch   |      | - CAPTCHA det |      | - Alternative loc |
| - Criteria |     | - Risk gate  |      | - Barriers    |      | - URL adjustments |
+------------+     +--------------+      +---------------+      +-------------------+
                          |                      |                        |
                          v                      v                        v
            +--------------------------------------------------------------------+
            |                      BROWSER AUTOMATION LAYER                      |
            |        Playwright Chromium (Headless / Headed), Smart Content      |
            |        Waits, Cookie Overlays, Deep Link Discovery Queue           |
            +--------------------------------------------------------------------+
                          |
                          v
            +--------------------------------------------------------------------+
            |                    SEARCH & RELEVANCE FILTERING                    |
            |     DuckDuckGo / Bing / Google / Wikipedia Multi-Provider Search   |
            |     Lexical + BM25 + Cosine Semantic Filtering & Deduplication     |
            +--------------------------------------------------------------------+
                          |
                          v
            +--------------------------------------------------------------------+
            |                       EXTRACTION ENGINE                            |
            |      HTML Boilerplate Cleaning, Article Extraction, Price/Spec     |
            |      Regex & Tabular Data Formatter (JSON & CSV Export)            |
            +--------------------------------------------------------------------+
                          |
                          v
            +--------------------------------------------------------------------+
            |                    HYBRID RAG & EMBEDDING PIPELINE                 |
            |     SentenceTransformers (all-MiniLM-L6-v2) + SQLite Vector Store  |
            |     Document Ingestion (TXT, MD, PDF), Cosine Similarity Retrieval |
            |     Configurable LLM: Ollama / OpenAI / Groq / OpenRouter / Fallback|
            +--------------------------------------------------------------------+
                          |
                          v
            +--------------------------------------------------------------------+
            |                    EXPERIENCE MEMORY & TASK HISTORY                |
            |      SQLite Task Trajectory History, Performance Metrics, and      |
            |      Learned Domain Navigation Strategies / Failure Avoidance      |
            +--------------------------------------------------------------------+
```

---

## 🌟 The 10 Advanced Capabilities

1. **Self-Correction Engine**: Detects failed clicks, navigation timeouts, missing selectors, and empty extraction buffers. Executes alternative locator strategies and records diagnostic outcomes in telemetry.
2. **Relevance-Based Search Filtering**: Scores candidate URLs using combined lexical token overlap and semantic similarity. Rejects tracking redirects, spam domains, and duplicate paths.
3. **Deep Website Navigation**: Multi-hop candidate link discovery from current DOM states with domain boundary enforcement, crawl queue management, and depth limits.
4. **Evidence-Based Answers**: All factual statements are grounded in retrieved vector chunks with clickable markdown citations `[Source Title](URL)` and explicit disclosure of missing facts.
5. **Task Verification**: Converts original objectives into binary audit checklists; computes confidence score and evidence coverage before marking tasks completed.
6. **Experience Memory**: SQLite-persisted repository of successful locator patterns, navigation rules, and error modes to guide future planner decisions.
7. **CAPTCHA Detection & Safe Handling**: Heuristic detection of reCAPTCHA, Cloudflare Turnstile, and login barriers. Pauses execution safely without solving or evading, and alerts the operator.
8. **Risk-Aware Browsing**: Read-only guard blocks consequential clicks (buy, checkout, delete, pay) and sensitive form field inputs (passwords, card numbers).
9. **Structured Data Extraction**: Regex and DOM table parser extracting prices, ratings, hardware specs, release dates, and custom schemas with JSON/CSV export.
10. **Performance Monitoring**: Tracks execution durations (search, nav, extraction, RAG, LLM), page visit counts, retry frequencies, and success trends.

---

## 🖥️ Frontend Views (NEXUS AI Laboratory Dashboard)

The application features a dark navy / charcoal AI research laboratory aesthetic with subtle cyan and indigo accents, generous card spacing, collapsible sidebar, and 9 dedicated views:

1. **Overview Dashboard**: High-level KPIs (Total tasks, success rate, avg duration, recovery rate, evidence coverage), trend charts, and 10 capability health badges.
2. **New Task Workspace**: Large natural-language goal input, optional starting URL, max depth, max pages, execution timeout, structured schema keys, risk preferences, and 5 interactive preset templates.
3. **Live Agent Execution**: Real-time status badge, active URL bar, step counter, live event timeline stream, Playwright viewport screenshot, pause/resume/cancel controls, and CAPTCHA alert banner.
4. **Task History & Results Explorer**: Master-detail view with 5 tabs: *Answer & Synthesis*, *Extracted Data Table*, *Evidence Cards*, *Verification Report*, and *Execution Logs*. Plus one-click JSON & CSV exports.
5. **Knowledge Base & RAG Explorer**: Drag-and-drop document upload (TXT, MD, PDF), chunk count inspection, provenance tracking (local document, browsed webpage, experience), and semantic vector search test bench.
6. **Experience Memory Manager**: Stored locator patterns, failure recoveries, domain advice query form, and pruning controls.
7. **Analytics & Performance Monitoring**: Interactive Recharts visualizations (Task Completion Trends, Task Type Distribution, and duration metrics).
8. **Safety Center**: Active policy indicators (Read-only mode, SSRF loopback blocking, allowed/blocked schemes, sensitive keywords), pending human intervention alerts, and historical barrier log.
9. **System Settings**: Model provider selector (Ollama, OpenAI, Groq, OpenRouter, Gemini, Deterministic), API key input, base URL, headless mode toggle, and timeouts.

---

## ⚡ Windows Quickstart & Execution Guide

### Prerequisites
- Windows 10 or 11
- Python 3.11 or higher
- Node.js v18+ and npm

### 1. Clone & Enter Project Directory
```powershell
cd C:\Users\ADILAKSHMI\autonomous-web-browsing-agent
```

### 2. Set Up Python Virtual Environment
```powershell
# Create venv if not already present
python -m venv .venv

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3. Build Frontend Assets
```powershell
cd frontend
npm install
npm run build
cd ..
```

### 4. Configure Environment (.env)
```powershell
# Copy template if .env does not exist
Copy-Item .env.example .env
```
Edit `.env` to configure your preferred LLM provider:
- For local Ollama: set `LLM_PROVIDER=ollama` (requires `ollama run llama3.2:3b`)
- For OpenAI: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...`
- For Groq: set `LLM_PROVIDER=groq` and `OPENAI_API_KEY=gsk_...`
- For offline demo without API keys: set `LLM_PROVIDER=deterministic`

### 5. Launch Application
Double-click `run_nexus.bat` or run in PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Open your browser to:
- **NEXUS Dashboard**: `http://127.0.0.1:8000/`
- **Interactive API Swagger Docs**: `http://127.0.0.1:8000/docs`

*(Optional) If developing frontend with hot-reload:*
```powershell
cd frontend
npm run dev
# Access via http://localhost:5173/ (proxies /api to 8000)
```

---

## 🧪 Automated Testing

The project includes an automated test suite covering end-to-end execution, API routes, planning, navigation, safety, RAG, and extraction:

```powershell
# Run the complete test suite
.\.venv\Scripts\pytest -v

# Run API-specific integration tests
.\.venv\Scripts\pytest tests/test_api.py -v
```

**Test Suite Status: 40 Passed, 0 Failed.**

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check (DB, vector store, LLM readiness) |
| `GET` | `/api/config` | Non-sensitive runtime configuration parameters |
| `POST` | `/api/config` | Update runtime settings (LLM provider, headless, timeouts) |
| `POST` | `/api/tasks` | Create and launch an autonomous browsing task |
| `GET` | `/api/tasks` | List recent tasks and metrics |
| `GET` | `/api/tasks/{task_id}` | Retrieve full task state and execution trajectory |
| `POST` | `/api/tasks/{task_id}/pause` | Pause an active agent loop |
| `POST` | `/api/tasks/{task_id}/resume` | Resume a paused agent loop |
| `POST` | `/api/tasks/{task_id}/cancel` | Terminate a running agent loop |
| `GET` | `/api/tasks/{task_id}/events` | Retrieve telemetry logs and step events |
| `GET` | `/api/tasks/{task_id}/results` | Final grounded answer, checklist, and structured data |
| `GET` | `/api/tasks/{task_id}/evidence`| Extracted text snippets with relevance scores |
| `GET` | `/api/tasks/{task_id}/export/{fmt}` | Download structured records as `json` or `csv` |
| `WS` | `/api/tasks/{task_id}/ws` | WebSocket for real-time live telemetry stream |
| `GET` | `/api/metrics` | System analytics summary & 14-day trend history |
| `GET` | `/api/memory` | List experience memory records |
| `GET` | `/api/memory/advice` | Query recommended strategies and failure avoidance |
| `DELETE`| `/api/memory/{id}` | Delete a single experience entry |
| `DELETE`| `/api/memory` | Clear all experience records |
| `POST` | `/api/knowledge/upload` | Ingest TXT, MD, or PDF file into RAG vector store |
| `GET` | `/api/knowledge` | List indexed knowledge documents and chunk counts |
| `DELETE`| `/api/knowledge/{doc_id}` | Delete document and chunks from vector store |
| `POST` | `/api/knowledge/search` | Semantic cosine similarity search across chunks |
| `GET` | `/api/safety` | Safety policies, SSRF status, and blocked triggers |
| `GET` | `/api/safety/interventions` | List active and historical barrier challenges |
| `POST` | `/api/safety/interventions/resolve` | Resolve active CAPTCHA / human intervention |

---

## 🎬 Step-by-Step Demonstration Script

### Demo 1: Autonomous Web Research & Evidence Citations
1. Open the dashboard at `http://127.0.0.1:8000/`.
2. Navigate to **New Task**. Click the template *"1. Technical Research & Summarization"*.
3. Click **Launch Autonomous Agent**.
4. Observe the **Live Browser** view: Watch the real-time event logs, step counter, visited URL updates, and diagnostic browser viewport.
5. Once completed, navigate to **Task History**. Inspect the **Answer & Synthesis** tab to review the grounded response with clickable markdown citations.
6. Open the **Extracted Data** or **Evidence** tab to verify source snippet provenance.

### Demo 2: Direct Destination URL & Structured CSV Export
1. In **New Task**, click *"3. Structured Data Extraction"*.
2. Notice the starting URL `https://docs.python.org/3/whatsnew/3.12.html` is pre-populated.
3. Click **Launch Autonomous Agent**.
4. Once completed, click the **CSV** export button to download the structured fact sheet.

### Demo 3: Knowledge Base RAG Ingestion & Vector Search
1. Navigate to **Knowledge Base**.
2. Upload any local `.txt` or `.pdf` research file.
3. Observe the chunk count and status update to `Indexed`.
4. Use the **Semantic Vector Query Explorer** on the right to search across stored chunks and view cosine similarity scores.

### Demo 4: Safety Guard & Consequential Action Interception
1. Navigate to **Safety Center**.
2. Verify that **Read-Only Guard** and **SSRF Loopback Shield** are enforced.
3. Review the blocked schemes (`file://`, `javascript:`) and consequential action triggers.

---

## 📄 License
This project is licensed under the MIT License.
