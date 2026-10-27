"""
Page content and metadata extraction engine.
Identifies core content containers, extracts article text, metadata, and tables.
"""

from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .content_cleaner import ContentCleaner
from browser.locators import Locators


class ExtractedPage:
    def __init__(
        self,
        url: str,
        title: str,
        clean_text: str,
        meta_description: str = "",
        headings: Dict[str, list] = None,
        raw_char_count: int = 0
    ):
        self.url = url
        self.title = title
        self.clean_text = clean_text
        self.meta_description = meta_description
        self.headings = headings or {}
        self.raw_char_count = raw_char_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "meta_description": self.meta_description,
            "char_count": len(self.clean_text),
            "headings_count": sum(len(v) for v in self.headings.values()),
        }


class PageExtractor:
    """Extracts main content and metadata from web pages."""

    def __init__(self, cleaner: Optional[ContentCleaner] = None):
        self.cleaner = cleaner or ContentCleaner()

    def extract(self, html_content: str, url: str, fallback_title: str = "") -> ExtractedPage:
        """Extract sanitized main body text and metadata from HTML."""
        if not html_content:
            return ExtractedPage(url=url, title=fallback_title, clean_text="")

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Title Extraction
        title = fallback_title
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # 2. Meta Description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content", "").strip()

        # 3. Headings Index
        headings = {"h1": [], "h2": [], "h3": []}
        for level in ["h1", "h2", "h3"]:
            headings[level] = [h.get_text(strip=True) for h in soup.find_all(level) if h.get_text(strip=True)]

        # 4. Target Main Content Container
        main_html = ""
        for selector in Locators.MAIN_CONTENT_SELECTORS:
            elem = soup.select_one(selector)
            if elem and len(elem.get_text(strip=True)) > 150:
                main_html = str(elem)
                break

        # Fallback to full HTML if no specific container found
        target_html = main_html if main_html else html_content

        # 5. Clean to Markdown
        clean_text = self.cleaner.clean_html_to_markdown(target_html)

        return ExtractedPage(
            url=url,
            title=title,
            clean_text=clean_text,
            meta_description=meta_desc,
            headings=headings,
            raw_char_count=len(html_content)
        )
