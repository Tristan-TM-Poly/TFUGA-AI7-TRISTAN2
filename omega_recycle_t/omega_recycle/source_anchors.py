from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SourceAnchor:
    source_id:str
    source_url:str
    observed_at:str
    facts:tuple[tuple[str,str],...]
    evidence_kind:str="manual_web_verified_anchor_not_raw_http_snapshot"
    claim_boundary:str="current_source_descriptor_not_immutable_truth_or_causal_evidence"

EUROSTAT_ENV_WASMUN_ANCHOR=SourceAnchor(
    "eurostat-env-wasmun-2026-08-10",
    "https://ec.europa.eu/eurostat/databrowser/view/env_wasmun/default/bar?lang=en",
    "2026-08-10",
    (
        ("last_data_update","2026-03-30T21:00"),
        ("last_structure_update","2026-03-27T22:00"),
        ("coverage","1995-2024"),
        ("cells","18024"),
        ("eu_2024_generated_kg_per_capita","517"),
        ("eu_2024_recycled_kg_per_capita","248"),
        ("eu_2024_recycling_rate_percent","48.1"),
    ),
)
EPA_SMM_ANCHOR=SourceAnchor(
    "epa-smm-facts-figures-2026-08-10",
    "https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/advancing-sustainable-materials-management",
    "2026-08-10",
    (
        ("page_last_updated","2026-01-22"),
        ("latest_national_facts_figures_data_year","2018"),
        ("last_factsheet_release_year","2020"),
        ("default_mass_unit","US short tons unless specified"),
    ),
)
SOURCE_ANCHORS=(EUROSTAT_ENV_WASMUN_ANCHOR,EPA_SMM_ANCHOR)
