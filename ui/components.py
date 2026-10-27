"""
Streamlit UI presentation components.
Renders dashboard metrics, evidence cards, execution logs, and intervention modals.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from agent.task_state import TaskState, TaskStatus


def render_header():
    """Render application branding and header."""
    st.markdown("""
    <div style="padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; color: #1E3A8A; display: flex; align-items: center; gap: 0.5rem;">
            🌐 Autonomous Web Browsing Agent
        </h1>
        <p style="margin: 0.3rem 0 0 0; color: #4B5563; font-size: 1.05rem;">
            Autonomous multi-website research with hybrid RAG, self-correction, evidence extraction, and grounded citations.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(state: TaskState):
    """Render top performance metrics row."""
    m = state.metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Duration", f"{m.total_duration_seconds:.1f}s")
    with col2:
        st.metric("Task Steps", f"{m.step_count}")
    with col3:
        st.metric("Pages Visited", f"{m.pages_visited}")
    with col4:
        st.metric("Retried Actions", f"{m.actions_retried}")
    with col5:
        conf = state.verification_report.confidence_score if state.verification_report else 0.0
        st.metric("Confidence", f"{conf * 100:.0f}%")


def render_status_badge(status: TaskStatus):
    """Render a colored status badge."""
    color_map = {
        TaskStatus.COMPLETED: "#10B981",         # Green
        TaskStatus.PARTIAL_COMPLETION: "#F59E0B", # Amber
        TaskStatus.RUNNING: "#3B82F6",            # Blue
        TaskStatus.VERIFYING: "#6366F1",          # Indigo
        TaskStatus.PAUSED_FOR_INTERVENTION: "#EF4444", # Red
        TaskStatus.FAILED: "#DC2626",             # Red
        TaskStatus.CANCELLED: "#6B7280",          # Gray
        TaskStatus.PENDING: "#9CA3AF"             # Light gray
    }
    color = color_map.get(status, "#6B7280")
    st.markdown(
        f'<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">'
        f'{status.value}'
        f'</span>',
        unsafe_allow_html=True
    )


def render_search_results_table(search_results: List[Dict[str, Any]]):
    """Render candidate search results with relevance scores and ranking explanations."""
    if not search_results:
        st.info("No search results captured yet.")
        return

    for i, res in enumerate(search_results, 1):
        with st.expander(f"#{i} {res.get('title', 'Unknown')} (Score: {res.get('relevance_score', 0):.2f})", expanded=(i == 1)):
            st.markdown(f"**URL:** [{res.get('url')}]({res.get('url')})")
            st.markdown(f"**Provider:** `{res.get('source_provider', 'web')}`")
            if res.get("rank_explanation"):
                st.markdown(f"**Selection Rationale:** *{res.get('rank_explanation')}*")
            if res.get("snippet"):
                st.markdown(f"**Snippet:** {res.get('snippet')}")


def render_evidence_cards(evidence_items: list):
    """Render extracted evidence cards including pricing, ratings, and specifications."""
    if not evidence_items:
        st.info("No evidence collected yet.")
        return

    for i, item in enumerate(evidence_items, 1):
        with st.expander(f"📄 Evidence #{i}: {item.title}", expanded=True):
            st.markdown(f"**Source URL:** [{item.url}]({item.url})")
            st.markdown(f"**Observed At:** `{item.observed_at}`")

            # Structured Facts
            sdata = item.structured_data or {}
            if sdata.get("prices_found"):
                st.markdown(f"💰 **Prices Detected:** `{'`, `'.join(sdata['prices_found'])}`")
            if sdata.get("ratings_found"):
                st.markdown(f"⭐ **Ratings Detected:** `{'`, `'.join(sdata['ratings_found'])}`")
            if sdata.get("specs"):
                st.markdown("**⚙️ Extracted Specs:**")
                for k, v in sdata["specs"].items():
                    st.markdown(f"- **{k.upper()}:** {', '.join(v)}")
            if sdata.get("key_bullets"):
                st.markdown("**📋 Key Features / Bullets:**")
                for bullet in sdata["key_bullets"][:5]:
                    st.markdown(f"- {bullet}")

            # Preview content
            preview = item.content[:600] + "..." if len(item.content) > 600 else item.content
            st.text_area("Extracted Text Preview", preview, height=120, disabled=True, key=f"prev_{i}")


def render_verification_report(report):
    """Render verification report card."""
    if not report:
        return

    with st.container():
        st.subheader("Audit & Verification Verdict")
        if report.is_successful:
            st.success(f"Verified: {report.status_verdict.value}")
        else:
            st.warning(f"Audit Status: {report.status_verdict.value}")

        if report.reasons:
            st.markdown("**Verified Achievements:**")
            for r in report.reasons:
                st.markdown(f"- ✅ {r}")

        if report.missing_information:
            st.markdown("**Missing / Incomplete Criteria:**")
            for m in report.missing_information:
                st.markdown(f"- ⚠️ {m}")

        if report.limitations:
            st.markdown("**Disclosed Limitations:**")
            for l in report.limitations:
                st.markdown(f"- ℹ️ {l}")
