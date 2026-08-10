from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

from .provenance import ProvenanceRecord, canonical_dataset_hash


@dataclass(frozen=True, slots=True)
class PublicDatasetSpec:
    source_id: str
    publisher: str
    dataset_code: str
    source_url: str
    coverage: str
    last_verified: str
    notes: str

    def __post_init__(self) -> None:
        if not all((self.source_id, self.publisher, self.dataset_code, self.source_url, self.last_verified)):
            raise ValueError("dataset source metadata fields are required")


@dataclass(frozen=True, slots=True)
class DatasetSnapshot:
    spec: PublicDatasetSpec
    records: tuple[dict[str, str], ...]
    provenance: ProvenanceRecord
    claim_boundary: str = "snapshot_provenance_only_source_semantics_must_be_interpreted_separately"


EUROSTAT_ENV_WASMUN = PublicDatasetSpec(
    source_id="eurostat-env-wasmun",
    publisher="Eurostat",
    dataset_code="env_wasmun",
    source_url="https://ec.europa.eu/eurostat/databrowser/view/env_wasmun/default/table?lang=en",
    coverage="municipal waste by waste management operations; source coverage reported as 1995-2024 when verified",
    last_verified="2026-08-10",
    notes="Retain Eurostat metadata and cross-country comparability cautions; differences are not causal effects.",
)

EPA_SMM_FACTS_2018 = PublicDatasetSpec(
    source_id="epa-smm-facts-figures-2018",
    publisher="US EPA",
    dataset_code="Advancing Sustainable Materials Management Facts and Figures 2018",
    source_url="https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/advancing-sustainable-materials-management",
    coverage="United States municipal solid waste; EPA states the most recent national Facts and Figures data are from 2018",
    last_verified="2026-08-10",
    notes="National MSW data; methodology and revisions must travel with any derived snapshot.",
)

PUBLIC_DATASETS: tuple[PublicDatasetSpec, ...] = (EUROSTAT_ENV_WASMUN, EPA_SMM_FACTS_2018)


def ingest_delimited_snapshot(
    spec: PublicDatasetSpec,
    text: str,
    *,
    retrieved_at: str,
    delimiter: str = ",",
    license: str | None = None,
) -> DatasetSnapshot:
    """Parse caller-supplied public data and bind the normalized records to a hash.

    R0.4 deliberately does not fetch over the network. Acquisition, terms,
    revisions and authentication remain explicit outside this pure parser.
    """
    if len(delimiter) != 1:
        raise ValueError("delimiter must be one character")
    reader = csv.DictReader(StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("delimited snapshot requires a header")
    records = tuple(
        {str(key): "" if value is None else str(value) for key, value in row.items()}
        for row in reader
    )
    digest = canonical_dataset_hash(records)
    provenance = ProvenanceRecord(
        source_id=spec.source_id,
        source_url=spec.source_url,
        retrieved_at=retrieved_at,
        sha256=digest,
        license=license,
    )
    return DatasetSnapshot(spec=spec, records=records, provenance=provenance)


def public_dataset_catalog() -> tuple[PublicDatasetSpec, ...]:
    return PUBLIC_DATASETS
