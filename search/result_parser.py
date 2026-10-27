"""
Search result parsing engine.
Extracts search entries from varied search engine markups and decodes redirects.
"""

from typing import List, Optional
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field
from safety.url_validator import URLValidator


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source_provider: str = "web"
    relevance_score: float = 0.0
    rank_explanation: str = ""


class SearchResultParser:
    """Parses diverse search result page HTML into standardized SearchResult models."""

    def __init__(self, url_validator: Optional[URLValidator] = None):
        self.validator = url_validator or URLValidator()

    def parse_results(
        self,
        html_content: str,
        base_url: str = "https://html.duckduckgo.com",
        provider_name: str = "duckduckgo"
    ) -> List[SearchResult]:
        """Parse HTML string and return extracted, decoded candidate search results."""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        results: List[SearchResult] = []

        if provider_name == "duckduckgo":
            results = self._parse_duckduckgo(soup, base_url)
        elif provider_name == "google":
            results = self._parse_google(soup, base_url)
        elif provider_name == "bing":
            results = self._parse_bing(soup, base_url)
        elif provider_name == "wikipedia":
            results = self._parse_wikipedia(soup, base_url)
        elif provider_name == "amazon_in":
            results = self._parse_amazon(soup, base_url)

        # Fallback to generic heuristic parser if site-specific returned nothing
        if not results:
            results = self._parse_generic_heuristics(soup, base_url)

        return results

    def _unwrap_redirect(self, raw_url: str) -> str:
        """Unwrap tracking redirects from search providers (e.g. DDG, Google)."""
        if not raw_url:
            return ""

        try:
            parsed = urlparse(raw_url)

            # DuckDuckGo redirect: /l/?uddg=https%3A%2F%2F...
            if "duckduckgo.com" in parsed.netloc and "uddg" in parsed.query:
                qs = parse_qs(parsed.query)
                if "uddg" in qs:
                    return unquote(qs["uddg"][0])

            # Google redirect: /url?q=https://...
            if "google." in parsed.netloc and "url" in parsed.path:
                qs = parse_qs(parsed.query)
                if "q" in qs:
                    return qs["q"][0]
                if "url" in qs:
                    return qs["url"][0]

        except Exception:
            pass

        return raw_url

    def _clean_and_validate_url(self, raw_url: str, base_url: str) -> Optional[str]:
        """Resolve, unwrap, normalize, and ensure safety of a result URL."""
        unwrapped = self._unwrap_redirect(raw_url)
        normalized = self.validator.normalize_url(unwrapped, base_url=base_url)
        
        is_safe, _ = self.validator.is_safe_url(normalized)
        if not is_safe:
            return None

        # Exclude anchor links or search pagination links
        if not normalized or normalized.startswith("javascript:"):
            return None

        return normalized

    def _parse_duckduckgo(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        # ddg html markup typically uses .result or .web-result
        containers = soup.select(".result, .web-result")
        for c in containers:
            title_elem = c.select_one(".result__title a, a.result__url, a.result-title")
            snippet_elem = c.select_one(".result__snippet")

            if not title_elem:
                continue

            raw_href = title_elem.get("href", "")
            title = title_elem.get_text(strip=True)
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            clean_url = self._clean_and_validate_url(raw_href, base_url)
            if clean_url and title:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet,
                    source_provider="duckduckgo"
                ))
        return results

    def _parse_google(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        # Google search results
        containers = soup.select("div.g, div[data-hveid]")
        for c in containers:
            title_elem = c.select_one("h3")
            link_elem = c.select_one("a[href]")
            snippet_elem = c.select_one(".VwiC3b, .yXK7lf, span.aCOpRe")

            if not link_elem or not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            raw_href = link_elem.get("href", "")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            clean_url = self._clean_and_validate_url(raw_href, base_url)
            if clean_url and title and "google.com" not in clean_url:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet,
                    source_provider="google"
                ))
        return results

    def _parse_bing(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        containers = soup.select("li.b_algo")
        for c in containers:
            title_elem = c.select_one("h2 a")
            snippet_elem = c.select_one(".b_caption p")

            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            raw_href = title_elem.get("href", "")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            clean_url = self._clean_and_validate_url(raw_href, base_url)
            if clean_url and title:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet,
                    source_provider="bing"
                ))
        return results

    def _parse_wikipedia(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        containers = soup.select(".mw-search-result")
        for c in containers:
            heading = c.select_one(".mw-search-result-heading a")
            snippet_elem = c.select_one(".searchresult")

            if not heading:
                continue

            title = heading.get_text(strip=True)
            raw_href = heading.get("href", "")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            clean_url = self._clean_and_validate_url(raw_href, "https://en.wikipedia.org")
            if clean_url and title:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet,
                    source_provider="wikipedia"
                ))
        return results

    def _parse_amazon(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        containers = soup.select('div[data-component-type="s-search-result"]')
        for c in containers:
            title_elem = c.select_one("h2 a")
            price_elem = c.select_one(".a-price .a-offscreen")

            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            raw_href = title_elem.get("href", "")
            price = price_elem.get_text(strip=True) if price_elem else ""
            snippet = f"Price: {price}" if price else ""

            clean_url = self._clean_and_validate_url(raw_href, "https://www.amazon.in")
            if clean_url and title:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet,
                    source_provider="amazon_in"
                ))
        return results

    def _parse_generic_heuristics(self, soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        """Generic fallback extractor for any search engine or directory page."""
        results: List[SearchResult] = []
        for a_tag in soup.select("h2 a, h3 a, a.result"):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
            if not href or not title or len(title) < 5:
                continue

            clean_url = self._clean_and_validate_url(href, base_url)
            if clean_url:
                results.append(SearchResult(
                    title=title,
                    url=clean_url,
                    snippet="",
                    source_provider="generic"
                ))
        return results
