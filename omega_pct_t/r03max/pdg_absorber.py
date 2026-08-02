from __future__ import annotations

"""Version-pinned PDG-style snapshot normalizer.

The module does not silently scrape or claim authority. It ingests an explicit
upstream payload supplied by a caller, records hashes and emits quarantines for
incomplete records. Production connectors can be layered on top later.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REQUIRED_PARTICLE_KEYS = {"pdg_id", "name", "status"}


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    edition: str
    cutoff_date: str
    source_locator: str
    source_sha256: str
    record_count: int
    accepted_count: int
    quarantine_count: int
    schema_version: str = "omega-pct-pdg-snapshot-0.3"


@dataclass(frozen=True, slots=True)
class NormalizedParticle:
    pdg_id: int
    name: str
    anti_name: str | None
    status: str
    mass_gev: float | None
    width_gev: float | None
    lifetime_s: float | None
    charge_e: float | None
    spin: str | None
    parity: str | None
    source_version: str
    raw_digest: str


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    index: int
    reason: str
    raw_digest: str
    raw: Mapping[str, Any]


def payload_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _optional_float(record: Mapping[str, Any], key: str) -> float | None:
    value = record.get(key)
    if value in (None, "", "unknown"):
        return None
    return float(value)


def normalize_record(record: Mapping[str, Any], *, edition: str) -> NormalizedParticle:
    missing = REQUIRED_PARTICLE_KEYS.difference(record)
    if missing:
        raise ValueError(f"missing required keys: {', '.join(sorted(missing))}")
    pdg_id = int(record["pdg_id"])
    if pdg_id == 0:
        raise ValueError("pdg_id 0 is reserved and not accepted")
    return NormalizedParticle(
        pdg_id=pdg_id,
        name=str(record["name"]),
        anti_name=(None if record.get("anti_name") is None else str(record["anti_name"])),
        status=str(record["status"]),
        mass_gev=_optional_float(record, "mass_gev"),
        width_gev=_optional_float(record, "width_gev"),
        lifetime_s=_optional_float(record, "lifetime_s"),
        charge_e=_optional_float(record, "charge_e"),
        spin=(None if record.get("spin") is None else str(record["spin"])),
        parity=(None if record.get("parity") is None else str(record["parity"])),
        source_version=edition,
        raw_digest=payload_hash(record),
    )


def absorb_snapshot(
    records: Iterable[Mapping[str, Any]],
    *,
    edition: str,
    cutoff_date: str,
    source_locator: str,
    output_directory: str | Path,
) -> SnapshotManifest:
    materialized = list(records)
    source_sha = payload_hash(materialized)
    accepted: list[NormalizedParticle] = []
    quarantined: list[QuarantineRecord] = []
    seen_ids: set[int] = set()
    for index, record in enumerate(materialized):
        try:
            particle = normalize_record(record, edition=edition)
            if particle.pdg_id in seen_ids:
                raise ValueError(f"duplicate pdg_id {particle.pdg_id}")
            seen_ids.add(particle.pdg_id)
            accepted.append(particle)
        except (TypeError, ValueError) as error:
            quarantined.append(
                QuarantineRecord(index, str(error), payload_hash(record), dict(record))
            )
    root = Path(output_directory)
    root.mkdir(parents=True, exist_ok=True)
    particles_path = root / "particles.jsonl"
    quarantine_path = root / "quarantine.jsonl"
    particles_path.write_text(
        "".join(json.dumps(asdict(item), sort_keys=True) + "\n" for item in accepted),
        encoding="utf-8",
    )
    quarantine_path.write_text(
        "".join(json.dumps(asdict(item), sort_keys=True) + "\n" for item in quarantined),
        encoding="utf-8",
    )
    manifest = SnapshotManifest(
        edition=edition,
        cutoff_date=cutoff_date,
        source_locator=source_locator,
        source_sha256=source_sha,
        record_count=len(materialized),
        accepted_count=len(accepted),
        quarantine_count=len(quarantined),
    )
    (root / "manifest.json").write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
