"""
Search provider interfaces and query URL builders.
Supports DuckDuckGo, Bing, Google, Wikipedia, Amazon India, and direct URL resolution.
"""

from typing import Dict, Any, Optional
from urllib.parse import quote_plus


class SearchProvider:
    """Base class for search providers."""
    name: str

    def build_search_url(self, query: str) -> str:
        raise NotImplementedError

    def get_search_box_selector(self) -> str:
        raise NotImplementedError


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def build_search_url(self, query: str) -> str:
        encoded = quote_plus(query)
        # Using html.duckduckgo.com for clean server-rendered markup without aggressive JS challenges
        return f"https://html.duckduckgo.com/html/?q={encoded}"

    def get_search_box_selector(self) -> str:
        return 'input[name="q"]'


class GoogleProvider(SearchProvider):
    name = "google"

    def build_search_url(self, query: str) -> str:
        encoded = quote_plus(query)
        return f"https://www.google.com/search?q={encoded}&hl=en"

    def get_search_box_selector(self) -> str:
        return 'textarea[name="q"], input[name="q"]'


class BingProvider(SearchProvider):
    name = "bing"

    def build_search_url(self, query: str) -> str:
        encoded = quote_plus(query)
        return f"https://www.bing.com/search?q={encoded}&setlang=en"

    def get_search_box_selector(self) -> str:
        return 'input[name="q"]'


class WikipediaProvider(SearchProvider):
    name = "wikipedia"

    def build_search_url(self, query: str) -> str:
        encoded = quote_plus(query)
        return f"https://en.wikipedia.org/w/index.php?search={encoded}&title=Special%3ASearch&fulltext=1"

    def get_search_box_selector(self) -> str:
        return 'input[name="search"]'


class AmazonIndiaProvider(SearchProvider):
    name = "amazon_in"

    def build_search_url(self, query: str) -> str:
        encoded = quote_plus(query)
        return f"https://www.amazon.in/s?k={encoded}"

    def get_search_box_selector(self) -> str:
        return '#twotabsearchtextbox, input[name="field-keywords"]'


PROVIDER_REGISTRY: Dict[str, SearchProvider] = {
    "duckduckgo": DuckDuckGoProvider(),
    "google": GoogleProvider(),
    "bing": BingProvider(),
    "wikipedia": WikipediaProvider(),
    "amazon_in": AmazonIndiaProvider(),
}


def get_provider(name: str) -> SearchProvider:
    """Retrieve search provider by name, defaulting to DuckDuckGo."""
    normalized = (name or "").lower().replace("-", "_").replace(" ", "_")
    return PROVIDER_REGISTRY.get(normalized, DuckDuckGoProvider())
