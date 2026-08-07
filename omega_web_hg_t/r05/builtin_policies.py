"""Initial executable policy registry derived from the governed R0.4 catalog.

These profiles are technical snapshots observed on 2026-08-03. They are not a
substitute for legal review and deliberately expire into human review.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import (
    AttributionPolicy,
    PolicyProfile,
    RequestRatePolicy,
    RequiredIdentityPolicy,
    RetentionPolicy,
    ReviewPolicy,
)

OBSERVED_AT = "2026-08-03"
COMMON_FIELDS = (
    "source_id",
    "record_id",
    "canonical_url",
    "title",
    "record_type",
    "issued",
    "updated",
    "license",
    "identifiers",
    "topics",
    "request_receipt_id",
    "source_payload_sha256",
    "epistemic_status",
    "digest",
)
FORBIDDEN_FIELDS = (
    "abstract",
    "abstracts",
    "author",
    "authors",
    "body",
    "content",
    "explanation",
    "full_text",
    "fulltext",
    "pdf",
    "raw_body",
    "raw_response",
)


def _profile(
    source_id: str,
    policy_url: str,
    routes: tuple[str, ...],
    *,
    recommended_rps: float,
    maximum_rps: float | None = None,
    required_environment: tuple[str, ...] = (),
    contact_email: str = "recommended",
    status: str = "verified",
    notes: tuple[str, ...] = (),
    jurisdiction: str | None = None,
) -> PolicyProfile:
    return PolicyProfile(
        source_id=source_id,
        policy_url=policy_url,
        policy_observed_at=OBSERVED_AT,
        policy_status=status,
        allowed_routes=routes,
        allowed_content=("metadata",),
        allowed_fields=COMMON_FIELDS,
        forbidden_content=("full_text", "raw_response", "binary_asset"),
        forbidden_fields=FORBIDDEN_FIELDS,
        required_environment=required_environment,
        request_rate=RequestRatePolicy(
            recommended_rps=recommended_rps,
            maximum_rps=maximum_rps,
            burst=1,
            retry_after_required=True,
        ),
        required_identity=RequiredIdentityPolicy(
            user_agent_required=True,
            contact_email=contact_email,
        ),
        retention=RetentionPolicy(
            raw_response="forbidden",
            normalized_metadata="allowed",
            maximum_days=None,
            encrypted_at_rest=False,
        ),
        attribution=AttributionPolicy(
            required=True,
            required_fields=("source_id", "canonical_url"),
        ),
        review=ReviewPolicy(review_after_days=30, next_review_at="2026-09-02"),
        enforcement_mode="reject",
        jurisdiction=jurisdiction,
        notes=notes,
    )


BUILTIN_POLICIES: tuple[PolicyProfile, ...] = (
    _profile(
        "wikimedia",
        "https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy",
        ("mediawiki_api", "official_dump"),
        recommended_rps=1.0,
        notes=("descriptive user agent required", "attribution and project license retained"),
    ),
    _profile(
        "crossref",
        "https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/",
        ("rest_api",),
        recommended_rps=0.5,
        contact_email="recommended",
        notes=("metadata only", "abstract fields are blocked by the runtime gate"),
    ),
    _profile(
        "pubmed",
        "https://www.ncbi.nlm.nih.gov/books/NBK25497/",
        ("eutils", "baseline_metadata"),
        recommended_rps=0.3,
        maximum_rps=3.0,
        contact_email="recommended",
        jurisdiction="US",
    ),
    _profile(
        "pmc_open",
        "https://pmc.ncbi.nlm.nih.gov/tools/oai/",
        ("oai_pmh",),
        recommended_rps=0.2,
        maximum_rps=1.0,
        notes=("R0.5 stores OAI metadata only", "full text requires a separate explicit rights profile"),
        jurisdiction="US",
    ),
    _profile(
        "nist_pdr",
        "https://data.nist.gov/rmm/",
        ("rmm_api",),
        recommended_rps=0.5,
        jurisdiction="US",
    ),
    _profile(
        "nasa_open",
        "https://api.nasa.gov/",
        ("rest_api",),
        recommended_rps=0.2,
        required_environment=("NASA_API_KEY",),
        contact_email="optional",
        jurisdiction="US",
    ),
    _profile(
        "cern_open_data",
        "https://opendata.cern.ch/docs/about",
        ("rest_api", "oai_pmh"),
        recommended_rps=0.3,
        notes=("record-level citation and license must be preserved",),
        jurisdiction="CH",
    ),
    _profile(
        "usgs",
        "https://earthquake.usgs.gov/fdsnws/event/1",
        ("fdsn_event_api", "official_feed"),
        recommended_rps=0.2,
        jurisdiction="US",
    ),
    _profile(
        "esa_cci",
        "https://climate.esa.int/data/apis",
        ("opensearch", "official_catalog"),
        recommended_rps=0.2,
        notes=("dataset-specific license remains authoritative",),
        jurisdiction="EU",
    ),
    _profile(
        "canada_open",
        "https://open.canada.ca/en/working-data-api/best-practices",
        ("ckan_api", "dcat"),
        recommended_rps=0.5,
        jurisdiction="CA",
        notes=("bilingual provenance retained", "record-level license retained"),
    ),
    _profile(
        "openalex",
        "https://developers.openalex.org/api-reference/authentication",
        ("rest_api", "official_snapshot"),
        recommended_rps=1.0,
        required_environment=("OPENALEX_API_KEY",),
        contact_email="optional",
        notes=("metadata only",),
    ),
    _profile(
        "arxiv",
        "https://info.arxiv.org/help/api/index.html",
        ("api", "bulk_data"),
        recommended_rps=0.2,
        status="human_review_required",
        notes=("cataloged but execution remains disabled until explicit current policy review",),
    ),
)


def policy_by_id(source_id: str) -> PolicyProfile:
    for profile in BUILTIN_POLICIES:
        if profile.source_id == source_id:
            return profile
    raise KeyError(source_id)


def executable_policies() -> tuple[PolicyProfile, ...]:
    return tuple(profile for profile in BUILTIN_POLICIES if profile.policy_status == "verified")


def with_required_environment(profile: PolicyProfile, values: Iterable[str]) -> PolicyProfile:
    return replace(profile, required_environment=tuple(sorted(set(values))))
