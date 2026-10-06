"""Security, SSRF Guard, and SQL Safety Enforcement for Phase 17 Enterprise Connectors."""

import ipaddress
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class SSRFSecurityError(Exception):
    """Raised when a connector target URL violates SSRF protection boundaries."""

    pass


class SQLSecurityError(Exception):
    """Raised when a database query contains dangerous or destructive statements."""

    pass


class SSRFGuard:
    """Blocks SSRF attacks targeting localhost, internal RFC-1918 subnets, cloud metadata, and link-local endpoints."""

    BLOCKED_HOSTNAMES = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "instance-data",
        "169.254.169.254",
        "kubernetes.default",
        "kubernetes.default.svc",
    }

    BLOCKED_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("224.0.0.0/4"),  # Multicast
        ipaddress.ip_network("240.0.0.0/4"),  # Reserved
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),  # Unique local
        ipaddress.ip_network("fe80::/10"),  # Link-local
    ]

    @classmethod
    def check_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """Checks if a URL is safe. Returns (is_safe, reason_if_unsafe)."""
        if not url:
            return False, "URL cannot be empty."

        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in ("http", "https"):
                return False, f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid URL: missing hostname."

            hostname_lower = hostname.lower()
            if hostname_lower in cls.BLOCKED_HOSTNAMES:
                return False, f"Access to restricted hostname '{hostname}' is blocked by security policy."

            # Check if direct IP literal
            try:
                ip_obj = ipaddress.ip_address(hostname_lower)
                if ip_obj.is_loopback:
                    return False, f"Access to loopback address '{ip_obj}' is prohibited."
                if ip_obj.is_private:
                    return False, f"Access to private RFC-1918 network address '{ip_obj}' is prohibited."
                if ip_obj.is_link_local:
                    return False, f"Access to link-local address '{ip_obj}' is prohibited."
                if ip_obj.is_multicast:
                    return False, f"Access to multicast address '{ip_obj}' is prohibited."
                if ip_obj.is_reserved:
                    return False, f"Access to reserved address '{ip_obj}' is prohibited."
                for net in cls.BLOCKED_NETWORKS:
                    if ip_obj in net:
                        return False, f"IP address '{ip_obj}' falls within restricted network boundary '{net}'."
            except ValueError:
                # Domain name: if mock or test domain or public domain, resolve or check known blocked names
                pass

            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """Alias for check_url returning (bool, Optional[str])."""
        return cls.check_url(url)

    @classmethod
    def enforce_safe_url(cls, url: str) -> str:
        """Throws SSRFSecurityError if URL is unsafe."""
        is_safe, reason = cls.check_url(url)
        if not is_safe:
            raise SSRFSecurityError(reason or "URL failed SSRF validation.")
        return url.strip()

    @classmethod
    def assert_safe_url(cls, url: str) -> str:
        """Alias for enforce_safe_url."""
        return cls.enforce_safe_url(url)


class SQLSafetyValidator:
    """Enforces read-only database query execution and rejects destructive DDL/DML operations."""

    DISALLOWED_KEYWORDS = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bINSERT\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bCREATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bATTACH\b",
        r"\bDETACH\b",
        r"\bCOPY\b",
        r"\bINTO\s+OUTFILE\b",
        r"\bLOAD_FILE\b",
        r"\bSHUTDOWN\b",
    ]

    @classmethod
    def validate_query(cls, query: str, max_row_limit: int = 10000) -> Tuple[bool, Optional[str]]:
        """Validates that a SQL query is read-only (SELECT / WITH / EXPLAIN) and contains no destructive clauses."""
        clean_q = query.strip()
        if not clean_q:
            return False, "Query cannot be empty."

        # Remove comments (single line and multi-line)
        no_comments = re.sub(r"--.*$", "", clean_q, flags=re.MULTILINE)
        no_comments = re.sub(r"/\*.*?\*/", "", no_comments, flags=re.DOTALL).strip()

        # Check for multiple statements (semicolon followed by non-whitespace)
        statements = [s.strip() for s in no_comments.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are not permitted in a single query."

        # Must start with SELECT, WITH, or EXPLAIN
        upper_q = no_comments.upper()
        if not (upper_q.startswith("SELECT") or upper_q.startswith("WITH") or upper_q.startswith("EXPLAIN")):
            return False, "Only read-only SELECT, WITH, or EXPLAIN statements are permitted."

        # Check for disallowed mutation keywords
        for pattern in cls.DISALLOWED_KEYWORDS:
            if re.search(pattern, no_comments, flags=re.IGNORECASE):
                match = re.search(pattern, no_comments, flags=re.IGNORECASE).group(0)
                return False, f"Destructive or modifying SQL keyword '{match}' is strictly prohibited."

        return True, None

    @classmethod
    def validate_sql(cls, query: str) -> Tuple[bool, Optional[str]]:
        """Alias for validate_query."""
        return cls.validate_query(query)

    @classmethod
    def enforce_read_only(cls, query: str) -> None:
        """Throws SQLSecurityError if query is not read-only."""
        valid, reason = cls.validate_query(query)
        if not valid:
            raise SQLSecurityError(reason or "Query violated SQL safety policies.")
