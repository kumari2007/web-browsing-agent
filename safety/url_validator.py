"""
URL validator and sanitization engine.
Protects against SSRF, dangerous schemes, loops, private subnet access, and tracking parameters.
"""

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode
from typing import Tuple, Optional


class URLValidator:
    """Validates, sanitizes, and normalizes URLs for safe browser navigation."""

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "gbraid", "wbraid", "msclkid", "ref", "ref_", "_hsenc",
        "_hsmi", "mc_cid", "mc_eid"
    }

    ALLOWED_SCHEMES = {"http", "https"}
    BLOCKED_SCHEMES = {"javascript", "data", "file", "ftp", "blob", "vbscript", "about"}

    PRIVATE_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),       # Private-use
        ipaddress.ip_network("172.16.0.0/12"),    # Private-use
        ipaddress.ip_network("192.168.0.0/16"),   # Private-use
        ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS/GCP/Azure)
        ipaddress.ip_network("::1/128"),          # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),         # IPv6 private
        ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
    ]

    def __init__(self, block_private_ips: bool = True, allow_localhost_for_tests: bool = False):
        self.block_private_ips = block_private_ips
        self.allow_localhost_for_tests = allow_localhost_for_tests

    def normalize_url(self, raw_url: str, base_url: Optional[str] = None) -> str:
        """
        Convert relative URLs to absolute, trim whitespace, and clean tracking tokens.
        """
        if not raw_url:
            return ""

        raw_url = raw_url.strip()

        # Handle base resolution
        if base_url:
            raw_url = urljoin(base_url, raw_url)

        parsed = urlparse(raw_url)
        scheme = parsed.scheme.lower()

        # Strip tracking query params
        if parsed.query:
            filtered_query = [
                (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if k.lower() not in self.TRACKING_PARAMS
            ]
            new_query = urlencode(filtered_query)
        else:
            new_query = ""

        # Normalize path
        path = parsed.path
        if not path:
            path = "/"

        normalized = urlunparse((
            scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            new_query,
            ""  # strip anchor fragment
        ))
        return normalized

    def is_safe_url(self, url: str) -> Tuple[bool, str]:
        """
        Verify that a URL uses safe protocols and doesn't target private/internal subnets.
        Returns: (is_safe, reason_or_error)
        """
        if not url:
            return False, "URL is empty"

        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Malformed URL: {e}"

        scheme = (parsed.scheme or "").lower()

        if scheme in self.BLOCKED_SCHEMES:
            return False, f"Prohibited URL scheme: {scheme}"

        if scheme not in self.ALLOWED_SCHEMES:
            return False, f"Unsupported scheme: '{scheme}'. Only http and https are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL missing valid hostname"

        # Check localhost test exemption
        if self.allow_localhost_for_tests and hostname in {"localhost", "127.0.0.1", "::1"}:
            return True, "Allowed test host"

        # Prevent access to loopback / local names
        if hostname.lower() in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}:
            if not self.allow_localhost_for_tests:
                return False, f"Access to localhost/internal host '{hostname}' is blocked."

        # If block_private_ips is active, resolve hostname and check IP ranges
        if self.block_private_ips:
            try:
                # Resolve IP addresses
                addr_info = socket.getaddrinfo(hostname, None)
                for entry in addr_info:
                    ip_str = entry[4][0]
                    ip_obj = ipaddress.ip_address(ip_str)

                    # Cloud metadata service check (169.254.169.254)
                    if ip_str == "169.254.169.254":
                        return False, "Access to cloud metadata IP (169.254.169.254) is forbidden."

                    for net in self.PRIVATE_NETWORKS:
                        if ip_obj in net:
                            if self.allow_localhost_for_tests and (ip_obj.is_loopback):
                                continue
                            return False, f"Host '{hostname}' resolves to restricted private IP: {ip_str}"
            except (socket.gaierror, ValueError):
                # DNS failure or unresolvable domain
                pass

        return True, "URL is safe"
