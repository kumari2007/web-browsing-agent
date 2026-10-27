"""
Pytest configuration and local HTTP test fixture server.
Provides isolated, deterministic HTTP endpoints for browser navigation, extraction, and end-to-end tests.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import threading
import http.server
import socketserver
import pytest
from typing import Generator
from safety.url_validator import URLValidator


MOCK_SEARCH_PAGE_HTML = """<!DOCTYPE html>
<html>
<head><title>Search Results - SearchEngine</title></head>
<body>
    <div class="search-results">
        <div class="result">
            <h2 class="result__title"><a class="result-title" href="/course1">Python for Beginners - Free Course</a></h2>
            <div class="result__snippet">Learn Python 3 from scratch. Free interactive tutorials, variables, loops, functions.</div>
        </div>
        <div class="result">
            <h2 class="result__title"><a class="result-title" href="/course2">Complete Python Bootcamp - Pro</a></h2>
            <div class="result__snippet">Comprehensive Python bootcamp covering OOP, web development, and data science for ₹3,499.</div>
        </div>
        <div class="result">
            <h2 class="result__title"><a class="result-title" href="/utility-login">Sign In / User Login</a></h2>
            <div class="result__snippet">Log in to your account.</div>
        </div>
    </div>
</body>
</html>
"""

MOCK_COURSE1_HTML = """<!DOCTYPE html>
<html>
<head><title>Python for Beginners - Free Foundation Course</title></head>
<body>
    <header><nav><a href="/">Home</a></nav></header>
    <main>
        <h1>Python for Beginners</h1>
        <p>A comprehensive introductory course on Python programming created for absolute beginners.</p>
        <div class="pricing">Price: Free (₹0)</div>
        <div class="rating">Rating: 4.8 out of 5 stars (12,400 ratings)</div>
        <h2>Course Syllabus</h2>
        <ul>
            <li>Introduction to Python syntax and data types</li>
            <li>Control flow: conditionals and loops</li>
            <li>Functions, modules, and error handling</li>
            <li>Building your first CLI automation project</li>
        </ul>
        <table>
            <tr><th>Feature</th><th>Details</th></tr>
            <tr><td>Duration</td><td>10 hours</td></tr>
            <tr><td>Certificate</td><td>Included</td></tr>
            <tr><td>Level</td><td>Beginner</td></tr>
        </table>
    </main>
    <footer><p>&copy; 2026 Test Academy</p></footer>
</body>
</html>
"""

MOCK_COURSE2_HTML = """<!DOCTYPE html>
<html>
<head><title>Complete Python Bootcamp - Professional Edition</title></head>
<body>
    <main>
        <h1>Complete Python Bootcamp</h1>
        <p>Master Python by building real projects including web scrapers, APIs, and data analysis pipelines.</p>
        <div class="pricing">Price: ₹3,499</div>
        <div class="rating">Rating: 4.6 out of 5 stars</div>
        <h2>Key Topics</h2>
        <ul>
            <li>Object-Oriented Programming (OOP) in depth</li>
            <li>Web development with Flask and FastAPI</li>
            <li>Data analysis with Pandas and NumPy</li>
        </ul>
        <table>
            <tr><th>Feature</th><th>Bootcamp Spec</th></tr>
            <tr><td>Duration</td><td>40 hours</td></tr>
            <tr><td>Certificate</td><td>Professional Certificate</td></tr>
            <tr><td>Prerequisites</td><td>None</td></tr>
        </table>
    </main>
</body>
</html>
"""

MOCK_PRODUCT_HTML = """<!DOCTYPE html>
<html>
<head><title>Dell Inspiron 15 Thin & Light Laptop</title></head>
<body>
    <main id="dp-container">
        <h1 id="productTitle">Dell Inspiron 15 Thin & Light Laptop</h1>
        <div class="a-price"><span class="a-offscreen">₹44,990</span></div>
        <div class="rating">4.3 out of 5 stars</div>
        <h2>Technical Details</h2>
        <table>
            <tr><td>RAM</td><td>16 GB LPDDR5</td></tr>
            <tr><td>Storage</td><td>512 GB SSD</td></tr>
            <tr><td>Processor</td><td>Intel Core i5-1235U</td></tr>
            <tr><td>Display</td><td>15.6 inch FHD</td></tr>
        </table>
    </main>
</body>
</html>
"""

MOCK_EMPTY_HTML = """<!DOCTYPE html><html><head><title>Empty</title></head><body></body></html>"""

MOCK_CAPTCHA_HTML = """<!DOCTYPE html>
<html>
<head><title>Security Check - Cloudflare Challenge</title></head>
<body>
    <h1>Verify you are human</h1>
    <div id="cf-turnstile">Please solve this security check to continue.</div>
</body>
</html>
"""


class MockServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        path = self.path.split("?")[0]
        if path == "/search":
            content = MOCK_SEARCH_PAGE_HTML
        elif path == "/course1":
            content = MOCK_COURSE1_HTML
        elif path == "/course2":
            content = MOCK_COURSE2_HTML
        elif path == "/product":
            content = MOCK_PRODUCT_HTML
        elif path == "/captcha":
            content = MOCK_CAPTCHA_HTML
        elif path == "/empty":
            content = MOCK_EMPTY_HTML
        else:
            content = "<html><body><h1>Default Page</h1></body></html>"

        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging during tests
        pass


@pytest.fixture(scope="session")
def test_server() -> Generator[str, None, None]:
    """Spins up a local HTTP test server on an ephemeral port."""
    server = socketserver.TCPServer(("127.0.0.1", 0), MockServerHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


@pytest.fixture
def test_url_validator() -> URLValidator:
    """URLValidator configured to permit local test server connections."""
    return URLValidator(block_private_ips=False, allow_localhost_for_tests=True)
