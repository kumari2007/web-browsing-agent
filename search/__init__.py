"""Search module with providers, result parsers, relevance filters, and manager."""

from .providers import SearchProvider, get_provider
from .result_parser import SearchResultParser, SearchResult
from .relevance_filter import RelevanceFilter
from .search_manager import SearchManager

__all__ = [
    "SearchProvider",
    "get_provider",
    "SearchResultParser",
    "SearchResult",
    "RelevanceFilter",
    "SearchManager",
]
