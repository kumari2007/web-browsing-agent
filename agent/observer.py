"""
Browser and DOM observation engine.
Assesses current page state, DOM completeness, and detects obstacles.
"""

import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from safety.human_intervention import HumanInterventionManager, ObstacleType
from search.search_manager import SearchManager

logger = logging.getLogger("agent.observer")


class PageObservation:
    def __init__(
        self,
        url: str,
        title: str,
        is_search_page: bool,
        char_count: int,
        obstacle: ObstacleType,
        is_empty_or_broken: bool,
        has_main_content: bool,
        notes: str = ""
    ):
        self.url = url
        self.title = title
        self.is_search_page = is_search_page
        self.char_count = char_count
        self.obstacle = obstacle
        self.is_empty_or_broken = is_empty_or_broken
        self.has_main_content = has_main_content
        self.notes = notes


class Observer:
    """Observes and diagnoses the active browser page."""

    def __init__(
        self,
        intervention_manager: Optional[HumanInterventionManager] = None,
        search_manager: Optional[SearchManager] = None
    ):
        self.intervention = intervention_manager or HumanInterventionManager()
        self.search = search_manager or SearchManager()

    def observe(self, page: Page) -> PageObservation:
        """Inspect the current page and diagnose its content readiness."""
        if not page or page.is_closed():
            return PageObservation(
                url="",
                title="",
                is_search_page=False,
                char_count=0,
                obstacle=ObstacleType.NONE,
                is_empty_or_broken=True,
                has_main_content=False,
                notes="Browser page is closed or unavailable."
            )

        current_url = page.url
        title = page.title() or ""

        try:
            body_text = page.inner_text("body", timeout=1500)
        except Exception:
            body_text = ""

        char_count = len(body_text.strip())

        # 1. Detect obstacles
        obstacle = self.intervention.detect_obstacle(
            title=title,
            text_sample=body_text[:2000],
            url=current_url
        )

        # 2. Check if still on search page
        is_search = self.search.is_search_results_page(current_url, title)

        # 3. Check for empty or broken page (e.g. 404, Server Error)
        lower_body = body_text.lower()
        is_empty = char_count < 80
        is_broken = any(err in lower_body[:500] for err in ["404 not found", "internal server error", "bad gateway", "dns_probe_finished"])

        has_main = char_count >= 150 and not is_search and not is_broken

        notes = []
        if is_search:
            notes.append("Active on search engine results page.")
        if obstacle != ObstacleType.NONE:
            notes.append(f"Obstacle detected: {obstacle.value}")
        if is_empty:
            notes.append("Page has minimal or empty text.")
        if is_broken:
            notes.append("Page indicates HTTP error or broken host.")

        return PageObservation(
            url=current_url,
            title=title,
            is_search_page=is_search,
            char_count=char_count,
            obstacle=obstacle,
            is_empty_or_broken=is_empty or is_broken,
            has_main_content=has_main,
            notes="; ".join(notes) if notes else "Normal content page."
        )
