"""Browser automation package with Playwright manager, locators, and navigation."""

from .playwright_browser import PlaywrightBrowserManager
from .locators import Locators
from .navigation import Navigator, NavigationResult

__all__ = [
    "PlaywrightBrowserManager",
    "Locators",
    "Navigator",
    "NavigationResult",
]
