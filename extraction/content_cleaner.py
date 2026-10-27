"""
HTML content cleaner and boilerplate remover.
Strips scripts, styling, navigation menus, ads, and footers while preserving semantic headings, tables, and lists.
"""

import re
from bs4 import BeautifulSoup, Comment, Tag


class ContentCleaner:
    """Cleans raw web HTML into concise, readable, and structured text."""

    TAGS_TO_REMOVE = {
        "script", "style", "noscript", "svg", "header", "footer", "nav",
        "aside", "iframe", "embed", "object", "form", "button", "canvas"
    }

    CLASS_OR_ID_PATTERNS_TO_REMOVE = [
        r"cookie", r"banner", r"advert", r"promo", r"social", r"share",
        r"footer", r"navbar", r"sidebar", r"popup", r"modal", r"newsletter"
    ]

    def clean_html_to_markdown(self, html_content: str, max_chars: int = 25000) -> str:
        """
        Transform raw HTML into clean, readable text with markdown-style headings, lists, and tables.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 2. Remove non-content tags
        for tag_name in self.TAGS_TO_REMOVE:
            for elem in soup.find_all(tag_name):
                elem.decompose()

        # 3. Remove elements with boilerplate classes/ids
        for pattern in self.CLASS_OR_ID_PATTERNS_TO_REMOVE:
            regex = re.compile(pattern, re.I)
            for elem in soup.find_all(attrs={"class": regex}):
                elem.decompose()
            for elem in soup.find_all(attrs={"id": regex}):
                elem.decompose()

        # 4. Convert tables to markdown tables
        self._format_tables(soup)

        # 5. Convert headings and lists
        self._format_headings_and_lists(soup)

        # 6. Extract text
        text = soup.get_text(separator="\n")

        # 7. Normalize whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        consecutive_blank = 0
        for line in lines:
            if not line:
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blank = 0
                cleaned_lines.append(line)

        final_text = "\n".join(cleaned_lines).strip()
        if len(final_text) > max_chars:
            final_text = final_text[:max_chars] + "\n... [Content truncated for length]"

        return final_text

    def _format_tables(self, soup: BeautifulSoup) -> None:
        """Convert <table> elements into Markdown pipe-delimited tables."""
        for table in soup.find_all("table"):
            md_table_rows = []
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all(["th", "td"])
                if cols:
                    cell_texts = [re.sub(r"\s+", " ", col.get_text().strip()) for col in cols]
                    md_table_rows.append("| " + " | ".join(cell_texts) + " |")

            if md_table_rows:
                # Add header separator after first row if header exists
                if len(md_table_rows) > 1:
                    header_len = md_table_rows[0].count("|") - 1
                    separator = "| " + " | ".join(["---"] * max(1, header_len)) + " |"
                    md_table_rows.insert(1, separator)

                table_str = "\n" + "\n".join(md_table_rows) + "\n"
                table.replace_with(table_str)

    def _format_headings_and_lists(self, soup: BeautifulSoup) -> None:
        """Add markdown prefixes to headings and list items."""
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text().strip()
                if text:
                    h.string = f"\n{'#' * level} {text}\n"

        for li in soup.find_all("li"):
            text = li.get_text().strip()
            if text:
                li.string = f"- {text}"
