"""
Autonomous Web Browsing Agent - Streamlit Application Entrypoint.
Provides an interactive dashboard for task dispatch, live action tracking,
evidence review, RAG answer display, and memory management.
"""

import time
import streamlit as st
from config import settings
from agent.agent import AutonomousWebAgent
from agent.task_state import TaskState, TaskStatus
from memory.experience_memory import ExperienceMemory
from memory.task_history import TaskHistoryRepository
from ui.components import (
    render_header,
    render_metrics,
    render_status_badge,
    render_search_results_table,
    render_evidence_cards,
    render_verification_report
)

# Page configuration
st.set_page_config(
    page_title="Autonomous Web Browsing Agent",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "task_input" not in st.session_state:
    st.session_state.task_input = ""

memory = ExperienceMemory()
history = TaskHistoryRepository()

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ Agent Controls")

browser_headless = st.sidebar.checkbox(
    "Run Browser Headless",
    value=True,
    help="When unchecked, launches a visible Chromium browser window on Windows."
)

selected_model = st.sidebar.text_input(
    "Ollama Model",
    value=settings.ollama_model,
    help="Configured local model in Ollama (e.g. llama3.2:3b)"
)

selected_provider = st.sidebar.selectbox(
    "Preferred Search Provider",
    options=["duckduckgo", "bing", "google", "wikipedia", "amazon_in"],
    index=0
)

max_pages = st.sidebar.slider(
    "Max Candidate Pages to Inspect",
    min_value=1,
    max_value=5,
    value=3
)

max_steps = st.sidebar.slider(
    "Max Task Steps",
    min_value=5,
    max_value=25,
    value=settings.max_task_steps
)

read_only_mode = st.sidebar.checkbox(
    "Read-Only Browsing",
    value=True,
    help="Enforces strict protection against purchases, form submissions, and logins."
)

st.sidebar.divider()
st.sidebar.markdown("### 🛠️ Memory Management")
if st.sidebar.button("Clear Experience Memory"):
    memory.clear_memory()
    st.sidebar.success("Cleared experience memory!")

if st.sidebar.button("Clear Task History"):
    history.clear_history()
    st.sidebar.success("Cleared task history!")

# --- MAIN PAGE HEADER ---
render_header()

# Example Task Prompt Helpers
st.markdown("**Quick Example Tasks:**")
col_e1, col_e2, col_e3 = st.columns(3)
with col_e1:
    if st.button("🐍 Best Python Beginner Courses"):
        st.session_state.task_input = (
            "Search Google for the best beginner Python courses, open three relevant websites, "
            "compare their course features and prices, and recommend the best option for a beginner."
        )
with col_e2:
    if st.button("💻 Amazon India Laptops Under ₹50k"):
        st.session_state.task_input = (
            "Search Amazon India for laptops under ₹50,000, open relevant product pages, "
            "and compare price, RAM, storage, processor, and ratings."
        )
with col_e3:
    if st.button("🔬 Wikipedia Quantum Computing"):
        st.session_state.task_input = (
            "Search Wikipedia for Quantum Computing, open the main article page, "
            "and summarize its key principles and applications."
        )

# Task Input
user_query = st.text_area(
    "Enter Natural-Language Research / Browsing Goal:",
    value=st.session_state.task_input,
    height=90,
    placeholder="e.g. Compare pricing and features for beginner Python courses across Coursera, Udemy, and edX."
)

btn_col1, btn_col2 = st.columns([1, 4])
with btn_col1:
    start_btn = st.button("🚀 Start Autonomous Task", type="primary", use_container_width=True)
with btn_col2:
    stop_btn = st.button("🛑 Stop Task", use_container_width=False)

# Task Execution Handler
if start_btn and user_query.strip():
    st.session_state.is_running = True
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    logs_expander = st.expander("📜 Live Execution Log", expanded=True)
    logs_placeholder = logs_expander.empty()

    # Create Agent
    agent = AutonomousWebAgent(
        headless=browser_headless,
        max_steps=max_steps
    )
    # Apply user overrides
    settings.ollama_model = selected_model
    settings.default_search_provider = selected_provider
    settings.read_only_mode = read_only_mode

    def on_step_update(state: TaskState):
        st.session_state.agent_state = state
        with status_placeholder.container():
            st.markdown(f"**Current Status:** {state.status.value} (Step {state.metrics.step_count})")
        with logs_placeholder.container():
            st.code("\n".join(state.logs[-12:]), language="text")

    try:
        final_state = agent.run_task(
            query=user_query.strip(),
            max_inspect_pages=max_pages,
            step_callback=on_step_update
        )
        st.session_state.agent_state = final_state
    finally:
        agent.close()
        st.session_state.is_running = False

# Render Dashboard if state exists
state: TaskState = st.session_state.agent_state

if state:
    st.divider()
    render_metrics(state)
    st.markdown(f"**Task Status:** ")
    render_status_badge(state.status)

    tabs = st.tabs([
        "📝 Grounded Answer & Audit",
        "📂 Collected Evidence",
        "🔍 Search Candidates",
        "🧠 Experience Memory",
        "📜 Task History"
    ])

    with tabs[0]:
        if state.final_answer:
            st.markdown(state.final_answer)
        else:
            st.info("No final answer generated yet.")

        st.divider()
        render_verification_report(state.verification_report)

    with tabs[1]:
        st.subheader(f"Extracted Evidence ({len(state.evidence_items)} Items)")
        render_evidence_cards(state.evidence_items)

    with tabs[2]:
        st.subheader(f"Search Results ({len(state.search_results)} Ranked)")
        render_search_results_table(state.search_results)

    with tabs[3]:
        st.subheader("Persistent Experience Memory")
        experiences = memory.get_all_experiences()
        if experiences:
            st.dataframe(experiences, use_container_width=True)
        else:
            st.info("No experience memory entries stored yet.")

    with tabs[4]:
        st.subheader("Historical Trajectories")
        recent_tasks = history.list_recent_tasks()
        if recent_tasks:
            st.dataframe(recent_tasks, use_container_width=True)
        else:
            st.info("No previous task history found.")
