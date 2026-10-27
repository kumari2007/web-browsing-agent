"""
Unit tests for SearchResultParser and RelevanceFilter.
Tests link extraction, redirect decoding, deduplication, URL exclusion, and relevance ranking.
"""

from search.result_parser import SearchResultParser, SearchResult
from search.relevance_filter import RelevanceFilter
from safety.url_validator import URLValidator


def test_result_parser_ddg_html(test_server):
    parser = SearchResultParser(url_validator=URLValidator(block_private_ips=False, allow_localhost_for_tests=True))
    
    mock_html = f"""
    <div class="result">
        <h2 class="result__title"><a class="result-title" href="{test_server}/course1">Python for Beginners</a></h2>
        <div class="result__snippet">Introductory Python coding tutorials.</div>
    </div>
    <div class="result">
        <h2 class="result__title"><a class="result-title" href="javascript:void(0)">Invalid Script Link</a></h2>
    </div>
    """
    
    results = parser.parse_results(mock_html, base_url=test_server, provider_name="duckduckgo")
    assert len(results) == 1
    assert results[0].title == "Python for Beginners"
    assert results[0].url.endswith("/course1")


def test_redirect_unwrapping():
    parser = SearchResultParser()
    wrapped_ddg = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Frealpython.com%2Flearning-path%2F&rut=1"
    unwrapped = parser._unwrap_redirect(wrapped_ddg)
    assert unwrapped == "https://realpython.com/learning-path/"

    wrapped_google = "https://www.google.com/url?q=https://docs.python.org/3/&sa=U&ved=2ahU"
    unwrapped_google = parser._unwrap_redirect(wrapped_google)
    assert unwrapped_google == "https://docs.python.org/3/"


def test_relevance_filter_deduplication_and_ranking():
    filter_engine = RelevanceFilter()
    query = "beginner python courses free"

    results = [
        SearchResult(title="Python For Beginners Course Free Tutorial", url="https://example.com/python-course", snippet="Best free Python course for absolute beginners"),
        SearchResult(title="Python For Beginners Course Free Tutorial", url="https://example.com/python-course/", snippet="Duplicate URL with trailing slash"),
        SearchResult(title="Terms of Service & Privacy Policy", url="https://example.com/terms-of-service", snippet="Legal conditions"),
        SearchResult(title="Unrelated Cooking Recipes", url="https://example.com/recipes", snippet="Italian pasta sauces"),
        SearchResult(title="Official Python Documentation", url="https://docs.python.org/3/tutorial/", snippet="The Python tutorial covering basics"),
    ]

    ranked = filter_engine.filter_and_rank(query=query, results=results, max_results=5)

    # Must deduplicate identical url
    assert len(ranked) <= 3

    # Disqualifying page (/terms-of-service) must be excluded
    assert not any("terms-of-service" in r.url for r in ranked)

    # Top result should be the Python for Beginners Course
    assert "Python For Beginners" in ranked[0].title
    assert ranked[0].relevance_score > 0.4
    assert "matched" in ranked[0].rank_explanation.lower()
