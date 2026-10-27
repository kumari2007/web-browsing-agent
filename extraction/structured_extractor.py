"""
Structured data extractor for product, course, and technical specifications.
Pulls prices, ratings, key-value specifications, and bulleted features.
"""

import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup


class StructuredExtractor:
    """Extracts structured entities like prices, specifications, ratings, and course attributes."""

    PRICE_PATTERN = re.compile(r"(?:₹|\$|€|£|INR|USD)\s*[\d,]+(?:\.\d{2})?|(?:Free|No cost)", re.I)
    RATING_PATTERN = re.compile(r"(\d(?:\.\d)?)\s*(?:out of 5|\/5|\s*stars)", re.I)

    SPEC_PATTERNS = {
        "ram": re.compile(r"\b(\d{1,2}\s*(?:GB|TB))\s*(?:RAM|Unified Memory|LPDDR\w*)?", re.I),
        "storage": re.compile(r"\b(\d{3,4}\s*GB|\d{1,2}\s*TB)\s*(?:SSD|HDD|eMMC|Storage|NVMe)?", re.I),
        "processor": re.compile(r"\b(Intel\s+(?:Core\s+)?i\d[\w-]*|Ryzen\s+\d[\w-]*|Apple\s+M\d[\w-]*|Snapdragon\s+[\w-]+)", re.I),
        "price": re.compile(r"(?:₹|\$)\s*([\d,]+)", re.I),
        "duration": re.compile(r"\b(\d{1,3}\s*(?:hours|weeks|months|days|hrs))\b", re.I),
    }

    def extract_structured_facts(self, text: str, html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze text and optional HTML to extract key entity data.
        """
        facts: Dict[str, Any] = {
            "prices_found": [],
            "ratings_found": [],
            "specs": {},
            "key_bullets": []
        }

        # 1. Price discovery
        prices = self.PRICE_PATTERN.findall(text)
        if prices:
            # Deduplicate preserving order
            facts["prices_found"] = list(dict.fromkeys(prices))[:5]

        # 2. Rating discovery
        ratings = self.RATING_PATTERN.findall(text)
        if ratings:
            facts["ratings_found"] = list(dict.fromkeys(ratings))[:3]

        # 3. Hardware / Technical Specs
        for spec_key, pattern in self.SPEC_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                facts["specs"][spec_key] = list(dict.fromkeys(matches))[:3]

        # 4. Extract bullet points if HTML is present
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            bullets = []
            for li in soup.find_all("li"):
                item_text = li.get_text(strip=True)
                if 20 <= len(item_text) <= 250:
                    bullets.append(item_text)
            facts["key_bullets"] = bullets[:8]

        return facts
