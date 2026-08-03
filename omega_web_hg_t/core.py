"""Compatibility surface for Ω-WEB-HG-T∞ R0.1.

The implementation is split into models, policy, extraction and crawler modules.
"""

from .crawler import WebHypergraphCrawler
from .extract import SemanticHTMLParser, parse_html
from .models import (
    CrawlConfig,
    CrawlResult,
    EdgeRecord,
    EvidenceRecord,
    FetchResponse,
    PageRecord,
    ParsedHTML,
    PolicyDecision,
    SafeRedirectHandler,
    SectionRecord,
    canonicalize_url,
    stable_id,
    utc_now,
)
from .policy import PolicyGate, PoliteHTTPFetcher

__all__ = [
    "CrawlConfig",
    "CrawlResult",
    "EdgeRecord",
    "EvidenceRecord",
    "FetchResponse",
    "PageRecord",
    "ParsedHTML",
    "PolicyDecision",
    "PolicyGate",
    "PoliteHTTPFetcher",
    "SafeRedirectHandler",
    "SectionRecord",
    "SemanticHTMLParser",
    "WebHypergraphCrawler",
    "canonicalize_url",
    "parse_html",
    "stable_id",
    "utc_now",
]
