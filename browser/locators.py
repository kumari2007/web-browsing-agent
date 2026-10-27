"""
Resilient locator definitions and accessibility-first selectors for diverse websites.
Supports search boxes, content bodies, product details, and navigation links.
"""

from typing import List, Dict


class Locators:
    """Central repository of robust selectors with fallback hierarchies."""

    # Generic & Accessible search inputs
    SEARCH_INPUT_SELECTORS: List[str] = [
        'input[type="search"]',
        'input[role="searchbox"]',
        'input[name="q"]',
        'input[name="query"]',
        'input[name="search"]',
        'input[name="field-keywords"]',          # Amazon India & US
        'input[id="searchInput"]',               # Wikipedia
        'input[placeholder*="search" i]',
        'input[placeholder*="find" i]',
        'textarea[name="q"]',                    # Modern Google search box
        'input[aria-label*="search" i]',
        'input.search-input',
    ]

    # Content body containers
    MAIN_CONTENT_SELECTORS: List[str] = [
        'main',
        'article',
        '[role="main"]',
        '#mw-content-text',                      # Wikipedia article body
        '#dp-container',                         # Amazon product details
        '#centerCol',                            # Amazon center column
        '.article-body',
        '.post-content',
        '.entry-content',
        '.content',
        '#content',
        'body',
    ]

    # Search result links
    SEARCH_RESULT_LINKS: List[str] = [
        'a[data-testid="result-title-a"]',       # DuckDuckGo HTML
        'h2 a',                                  # Common search header links
        'h3 a',                                  # Common search header links
        '.yuRUbf a',                             # Google classic
        '.b_algo h2 a',                          # Bing classic
        '.mw-search-result-heading a',           # Wikipedia search results
        'div[data-component-type="s-search-result"] h2 a', # Amazon India products
        'a.result__url',
        'a.result-title',
    ]

    # Cookie & Modal dismiss buttons
    COOKIE_DISMISS_SELECTORS: List[str] = [
        'button:has-text("Accept all")',
        'button:has-text("Accept All Cookies")',
        'button:has-text("I agree")',
        'button:has-text("Agree")',
        'button:has-text("Allow all")',
        'button:has-text("Dismiss")',
        'button:has-text("Close")',
        '[aria-label="Close"]',
    ]

    # Specialized site selectors
    SITE_PATTERNS: Dict[str, Dict[str, str]] = {
        "wikipedia.org": {
            "search_box": 'input[name="search"]',
            "content": "#mw-content-text",
            "title": "#firstHeading",
        },
        "amazon.in": {
            "search_box": "#twotabsearchtextbox",
            "results": 'div[data-component-type="s-search-result"]',
            "product_title": "#productTitle",
            "price": ".a-price .a-offscreen",
        },
        "google.com": {
            "search_box": 'textarea[name="q"], input[name="q"]',
            "results": ".g",
        },
        "bing.com": {
            "search_box": 'input[name="q"]',
            "results": ".b_algo",
        },
        "duckduckgo.com": {
            "search_box": 'input[name="q"]',
            "results": ".result",
        }
    }
