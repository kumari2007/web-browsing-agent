"""
Playwright browser manager.
Handles browser lifecycle, resilient context initialization, screenshot captures, and graceful teardown.
"""

import time
import logging
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from config import settings

logger = logging.getLogger("agent.browser")


class PlaywrightBrowserManager:
    """Manages browser instance and tabs with robust error handling and resource reuse."""

    def __init__(
        self,
        headless: Optional[bool] = None,
        timeout_ms: Optional[int] = None,
        user_agent: Optional[str] = None
    ):
        self.headless = headless if headless is not None else settings.browser_headless
        self.timeout_ms = timeout_ms or settings.browser_timeout_ms
        self.user_agent = user_agent or settings.user_agent

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> Page:
        """Launch browser and configure context if not already active."""
        if self._page and not self._page.is_closed():
            return self._page

        try:
            if not self._playwright:
                self._playwright = sync_playwright().start()

            if not self._browser or not self._browser.is_connected():
                self._browser = self._playwright.chromium.launch(
                    headless=self.headless,
                    slow_mo=settings.browser_slow_mo_ms,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars",
                        "--start-maximized"
                    ]
                )

            if not self._context:
                self._context = self._browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                    timezone_id="Asia/Kolkata",
                    accept_downloads=False
                )
                self._context.set_default_timeout(self.timeout_ms)

            self._page = self._context.new_page()
            return self._page

        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {e}", exc_info=True)
            self.close()
            raise

    def get_page(self) -> Page:
        """Retrieve active page or start browser."""
        if not self._page or self._page.is_closed():
            return self.start()
        return self._page

    def capture_screenshot(self, filename_prefix: str = "error") -> Optional[Path]:
        """Capture screenshot of current page state for diagnostic logging."""
        if not self._page or self._page.is_closed():
            return None

        try:
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{timestamp}.png"
            target_path = settings.screenshots_dir / filename
            self._page.screenshot(path=str(target_path), full_page=False)
            logger.info(f"Captured diagnostic screenshot: {target_path}")
            return target_path
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return None

    def close(self) -> None:
        """Safely terminate page, context, and browser."""
        try:
            if self._page and not self._page.is_closed():
                self._page.close()
        except Exception:
            pass
        finally:
            self._page = None

        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        finally:
            self._context = None

        try:
            if self._browser and self._browser.is_connected():
                self._browser.close()
        except Exception:
            pass
        finally:
            self._browser = None

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        finally:
            self._playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
