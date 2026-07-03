"""Ω-OSS-DIGEST-T: OAK-safe open-source digestion scaffold."""

from .license_gate import LicenseDecision, classify_license
from .scorer import DigestScore, score_source
from .oak_runner import OakDecision, oak_decision
from .api_layer import GitHubApiClient, GitHubSearchIntent, StackExchangeApiClient

__all__ = [
    "LicenseDecision",
    "classify_license",
    "DigestScore",
    "score_source",
    "OakDecision",
    "oak_decision",
    "GitHubApiClient",
    "GitHubSearchIntent",
    "StackExchangeApiClient",
]

__version__ = "0.2.0"
