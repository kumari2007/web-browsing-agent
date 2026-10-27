"""
Unit tests for ContentCleaner, PageExtractor, and StructuredExtractor.
Tests HTML cleanup, table formatting, and structured specification extraction.
"""

from extraction.content_cleaner import ContentCleaner
from extraction.page_extractor import PageExtractor
from extraction.structured_extractor import StructuredExtractor
from tests.conftest import MOCK_COURSE1_HTML, MOCK_PRODUCT_HTML


def test_content_cleaner_table_and_markdown():
    cleaner = ContentCleaner()
    html = """
    <html>
    <body>
        <script>alert("malicious script");</script>
        <header><nav><a href="#">Navigation</a></nav></header>
        <h1>Main Article</h1>
        <p>Paragraph text content.</p>
        <table>
            <tr><th>Plan</th><th>Cost</th></tr>
            <tr><td>Standard</td><td>Free</td></tr>
        </table>
        <footer>Footer content</footer>
    </body>
    </html>
    """
    clean_text = cleaner.clean_html_to_markdown(html)

    assert "alert" not in clean_text
    assert "Navigation" not in clean_text
    assert "Footer content" not in clean_text
    assert "# Main Article" in clean_text
    assert "| Plan | Cost |" in clean_text
    assert "| Standard | Free |" in clean_text


def test_page_extractor_metadata_and_body():
    extractor = PageExtractor()
    extracted = extractor.extract(MOCK_COURSE1_HTML, url="http://example.com/course1")

    assert "Python for Beginners" in extracted.title
    assert "absolute beginners" in extracted.clean_text
    assert "10 hours" in extracted.clean_text
    assert len(extracted.headings["h1"]) >= 1


def test_structured_extractor_course_and_product_specs():
    structured = StructuredExtractor()

    # Course extraction
    course_facts = structured.extract_structured_facts(MOCK_COURSE1_HTML, html_content=MOCK_COURSE1_HTML)
    assert any("free" in p.lower() or "0" in p for p in course_facts["prices_found"])
    assert any("4.8" in r for r in course_facts["ratings_found"])
    assert len(course_facts["key_bullets"]) >= 3

    # Product extraction
    product_facts = structured.extract_structured_facts(MOCK_PRODUCT_HTML, html_content=MOCK_PRODUCT_HTML)
    assert any("44,990" in p for p in product_facts["prices_found"])
    assert any("4.3" in r for r in product_facts["ratings_found"])
    assert "ram" in product_facts["specs"]
    assert any("16" in s for s in product_facts["specs"]["ram"])
    assert "storage" in product_facts["specs"]
    assert any("512" in s for s in product_facts["specs"]["storage"])
    assert "processor" in product_facts["specs"]
    assert any("i5" in s.lower() for s in product_facts["specs"]["processor"])
