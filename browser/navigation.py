"""
Navigation engine with smart content waits, redirect tracking, and obstacle detection.
Avoids fragile arbitrary sleeps in favor of bounded DOM and content state checks.
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from safety.url_validator import URLValidator
from safety.human_intervention import HumanInterventionManager, ObstacleType
from browser.locators import Locators
from config import settings

logger = logging.getLogger("agent.navigation")


class NavigationResult:
    def __init__(
        self,
        success: bool,
        url: str,
        title: str = "",
        status_code: Optional[int] = None,
        html_content: str = "",
        text_content: str = "",
        obstacle: ObstacleType = ObstacleType.NONE,
        error_message: Optional[str] = None,
        elapsed_seconds: float = 0.0
    ):
        self.success = success
        self.url = url
        self.title = title
        self.status_code = status_code
        self.html_content = html_content
        self.text_content = text_content
        self.obstacle = obstacle
        self.error_message = error_message
        self.elapsed_seconds = elapsed_seconds


class Navigator:
    """Manages resilient navigation, URL sanitization, and obstacle detection."""

    def __init__(
        self,
        url_validator: Optional[URLValidator] = None,
        intervention_manager: Optional[HumanInterventionManager] = None
    ):
        self.url_validator = url_validator or URLValidator(
            block_private_ips=settings.block_private_ips
        )
        self.intervention_manager = intervention_manager or HumanInterventionManager()

    def navigate_to(
        self,
        page: Page,
        target_url: str,
        timeout_ms: Optional[int] = None,
        dismiss_cookies: bool = True
    ) -> NavigationResult:
        """
        Navigate safely to a target URL, waiting for DOM readiness and meaningful text.
        """
        start_time = time.time()
        timeout = timeout_ms or settings.browser_timeout_ms

        # 1. URL Safety Check
        is_safe, safety_reason = self.url_validator.is_safe_url(target_url)
        if not is_safe:
            logger.warning(f"Blocked unsafe navigation to {target_url}: {safety_reason}")
            return NavigationResult(
                success=False,
                url=target_url,
                error_message=f"Safety policy rejected URL: {safety_reason}",
                elapsed_seconds=time.time() - start_time
            )

        try:
            # 2. Issue Navigation
            response = page.goto(target_url, wait_until="domcontentloaded", timeout=timeout)
            status_code = response.status if response else None

            # Bounded check for content rendering
            self._wait_for_meaningful_content(page, max_wait_sec=4.0)

            # 3. Dismiss Cookie Modals if present
            if dismiss_cookies:
                self._try_dismiss_overlays(page)

            # 4. Extract Title, Final URL, and Text Sample
            current_url = page.url
            title = page.title() or ""
            html = page.content()
            try:
                body_text = page.inner_text("body", timeout=1500)
            except Exception:
                body_text = ""

            # 5. Obstacle / CAPTCHA Detection
            obstacle = self.intervention_manager.detect_obstacle(
                title=title,
                text_sample=body_text[:2000],
                url=current_url
            )

            if obstacle != ObstacleType.NONE:
                logger.warning(f"Obstacle detected ({obstacle.value}) at {current_url}")
                self.intervention_manager.request_intervention(
                    obstacle_type=obstacle,
                    url=current_url,
                    message=f"Human intervention required: {obstacle.value} encountered."
                )

            elapsed = time.time() - start_time
            return NavigationResult(
                success=True,
                url=current_url,
                title=title,
                status_code=status_code,
                html_content=html,
                text_content=body_text,
                obstacle=obstacle,
                elapsed_seconds=elapsed
            )

        except PlaywrightTimeoutError as e:
            elapsed = time.time() - start_time
            logger.error(f"Navigation timed out for {target_url}: {e}")
            return NavigationResult(
                success=False,
                url=target_url,
                error_message=f"Page load timed out after {timeout/1000:.1f}s",
                elapsed_seconds=elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Navigation error for {target_url}: {e}")
            return NavigationResult(
                success=False,
                url=target_url,
                error_message=str(e),
                elapsed_seconds=elapsed
            )

    def extract_candidate_links(
        self,
        page: Page,
        base_url: str,
        allowed_domains: Optional[List[str]] = None,
        max_links: int = 20
    ) -> List[Dict[str, str]]:
        """
        Discover actionable links from current DOM state for deep site exploration.
        Filters anchors, javascript, mailto, unallowed domains, and non-http schemes.
        """
        discovered = []
        seen = set()

        base_parsed = urlparse(base_url)
        base_netloc = base_parsed.netloc.lower()

        try:
            links = page.query_selector_all("a[href]")
            for link in links:
                if len(discovered) >= max_links:
                    break
                href = link.get_attribute("href")
                if not href:
                    continue

                href = href.strip()
                if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue

                full_url = urljoin(base_url, href)
                # Strip fragments
                full_url = full_url.split("#")[0]

                if not full_url.startswith(("http://", "https://")):
                    continue

                parsed = urlparse(full_url)
                link_netloc = parsed.netloc.lower()

                # Domain restriction check
                if allowed_domains:
                    if not any(d.lower() in link_netloc for d in allowed_domains):
                        continue
                
                # Check safety
                is_safe, _ = self.url_validator.is_safe_url(full_url)
                if not is_safe:
                    continue

                if full_url in seen or full_url == base_url:
                    continue

                text = (link.inner_text() or "").strip()
                title = (link.get_attribute("title") or "").strip()
                label = text or title or href

                seen.add(full_url)
                discovered.append({
                    "url": full_url,
                    "anchor_text": label[:120],
                    "domain": link_netloc
                })
        except Exception as e:
            logger.debug(f"Link discovery encountered minor exception: {e}")

        return discovered

    def _wait_for_meaningful_content(self, page: Page, max_wait_sec: float = 3.0) -> None:
        """Poll boundedly until body has content or timeout elapses."""
        start = time.time()
        while time.time() - start < max_wait_sec:
            try:
                # Check for any main container
                for selector in Locators.MAIN_CONTENT_SELECTORS:
                    elem = page.query_selector(selector)
                    if elem:
                        text = elem.inner_text()
                        if text and len(text.strip()) > 80:
                            return
            except Exception:
                pass
            time.sleep(0.3)

    def _try_dismiss_overlays(self, page: Page) -> None:
        """Dismiss common cookie prompts or consent dialogs if visible."""
        for selector in Locators.COOKIE_DISMISS_SELECTORS:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click(timeout=1000)
                    logger.debug(f"Dismissed overlay using {selector}")
                    time.sleep(0.3)
                    break
            except Exception:
                continue
