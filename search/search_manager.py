"""
Search manager orchestrating query execution across providers, fallback handling,
page detection, and relevance filtering.
"""

import time
import logging
import requests
from typing import List, Optional, Tuple
from playwright.sync_api import Page
from .providers import get_provider, SearchProvider
from .result_parser import SearchResultParser, SearchResult
from .relevance_filter import RelevanceFilter
from safety.url_validator import URLValidator
from config import settings

logger = logging.getLogger("agent.search")


class SearchManager:
    """Orchestrates search queries across providers, handles fallbacks, and filters results."""

    def __init__(
        self,
        parser: Optional[SearchResultParser] = None,
        filter_engine: Optional[RelevanceFilter] = None,
        url_validator: Optional[URLValidator] = None
    ):
        self.validator = url_validator or URLValidator(block_private_ips=settings.block_private_ips)
        self.parser = parser or SearchResultParser(url_validator=self.validator)
        self.filter_engine = filter_engine or RelevanceFilter()

    def search(
        self,
        query: str,
        provider_name: str = "duckduckgo",
        max_results: int = 5,
        page: Optional[Page] = None
    ) -> List[SearchResult]:
        """
        Execute search query. If Playwright page is provided, navigates using browser;
        otherwise performs resilient HTTP query.
        """
        provider = get_provider(provider_name)
        search_url = provider.build_search_url(query)
        html_content = ""

        # 1. Try Browser Navigation if Page provided
        if page and not page.is_closed():
            try:
                logger.info(f"Navigating browser to search URL: {search_url}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=settings.browser_timeout_ms)
                time.sleep(1.0)
                html_content = page.content()
            except Exception as e:
                logger.warning(f"Browser search navigation failed ({e}), falling back to HTTP: {search_url}")

        # 2. HTTP Fallback
        if not html_content:
            html_content = self._fetch_via_http(search_url)

        # 3. If primary provider failed or yielded empty content, try DuckDuckGo or Bing fallback
        raw_results = self.parser.parse_results(html_content, base_url=search_url, provider_name=provider.name)
        if not raw_results and provider.name != "duckduckgo":
            logger.info("Primary search returned 0 results; falling back to DuckDuckGo HTML")
            ddg_provider = get_provider("duckduckgo")
            ddg_url = ddg_provider.build_search_url(query)
            fallback_html = self._fetch_via_http(ddg_url)
            raw_results = self.parser.parse_results(fallback_html, base_url=ddg_url, provider_name="duckduckgo")

        # 4. Filter, score, explain, and rank
        ranked = self.filter_engine.filter_and_rank(
            query=query,
            results=raw_results,
            max_results=max_results
        )

        logger.info(f"Search for '{query}' found {len(raw_results)} raw results, ranked top {len(ranked)}")
        return ranked

    def is_search_results_page(self, url: str, title: str) -> bool:
        """Determine whether current page is a search result listing rather than an article/product."""
        url_lower = url.lower()
        title_lower = title.lower()

        search_patterns = [
            "/search", "q=", "search?", "s?k=", "query=",
            "special:search", "/find", "duckduckgo.com"
        ]
        if any(pat in url_lower for pat in search_patterns):
            return True

        if "search results" in title_lower or "results for" in title_lower:
            return True

        return False

    def _fetch_via_http(self, url: str) -> str:
        """Fetch page markup via HTTP GET with browser user agent headers."""
        try:
            headers = {
                "User-Agent": settings.user_agent,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            logger.error(f"HTTP search fetch failed for {url}: {e}")
        return ""
