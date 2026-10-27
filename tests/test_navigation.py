"""
Integration tests for Playwright browser navigation and obstacle detection.
Uses the local test fixture server to test real browser operations reliably.
"""

import pytest
from browser.playwright_browser import PlaywrightBrowserManager
from browser.navigation import Navigator
from safety.human_intervention import ObstacleType
from search.search_manager import SearchManager


def test_browser_navigation_and_content_retrieval(test_server, test_url_validator):
    browser_manager = PlaywrightBrowserManager(headless=True)
    navigator = Navigator(url_validator=test_url_validator)

    try:
        page = browser_manager.start()
        result = navigator.navigate_to(page, f"{test_server}/course1")

        assert result.success is True
        assert "Python for Beginners" in result.title
        assert "absolute beginners" in result.text_content
        assert result.obstacle == ObstacleType.NONE
    finally:
        browser_manager.close()


def test_distinguish_search_page_from_article_page(test_server, test_url_validator):
    search_manager = SearchManager()

    # Search page URL
    assert search_manager.is_search_results_page("https://duckduckgo.com/html/?q=python", "DuckDuckGo Search") is True
    assert search_manager.is_search_results_page("https://www.google.com/search?q=laptops", "laptops - Google Search") is True

    # Real destination / article page
    assert search_manager.is_search_results_page("https://en.wikipedia.org/wiki/Python_(programming_language)", "Python - Wikipedia") is False
    assert search_manager.is_search_results_page("https://realpython.com/beginners-guide/", "Beginners Guide to Python") is False


def test_empty_page_handling(test_server, test_url_validator):
    browser_manager = PlaywrightBrowserManager(headless=True)
    navigator = Navigator(url_validator=test_url_validator)

    try:
        page = browser_manager.start()
        result = navigator.navigate_to(page, f"{test_server}/empty")

        assert result.success is True
        assert len(result.text_content.strip()) < 50
    finally:
        browser_manager.close()


def test_captcha_obstacle_detection(test_server, test_url_validator):
    browser_manager = PlaywrightBrowserManager(headless=True)
    navigator = Navigator(url_validator=test_url_validator)

    try:
        page = browser_manager.start()
        result = navigator.navigate_to(page, f"{test_server}/captcha")

        assert result.success is True
        assert result.obstacle in {ObstacleType.CLOUDFLARE_CHALLENGE, ObstacleType.CAPTCHA}
    finally:
        browser_manager.close()


def test_navigation_timeout_handling(test_url_validator):
    browser_manager = PlaywrightBrowserManager(headless=True)
    navigator = Navigator(url_validator=test_url_validator)

    try:
        page = browser_manager.start()
        # Test non-routable port with small timeout to trigger TimeoutError safely
        result = navigator.navigate_to(page, "http://10.255.255.1:9999", timeout_ms=800)
        assert result.success is False
        assert result.error_message is not None
    finally:
        browser_manager.close()
