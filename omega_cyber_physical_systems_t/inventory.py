from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import DOMAINS


TEXT_SUFFIXES = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt"}
EXCLUDED_TOP_LEVEL = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    "generated",
    "node_modules",
    "dist",
    "build",
}
PHYSICAL_DOMAINS = {
    "mechanical_translational",
    "mechanical_rotational",
    "electrical_power",
    "electronic_signal",
    "thermal",
    "fluid",
}
DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mechanical_translational": (
        "mechanical",
        "motion",
        "position",
        "velocity",
        "acceleration",
        "force",
        "mass",
        "spring",
        "actuator",
        "robot",
        "vehicle",
        "mechanism",
        "solid",
        "stress",
        "strain",
    ),
    "mechanical_rotational": (
        "rotor",
        "rotation",
        "rotational",
        "torque",
        "rpm",
        "angular",
        "shaft",
        "motor",
        "gear",
        "turbine",
        "propulsion",
    ),
    "electrical_power": (
        "electrical",
        "voltage",
        "current",
        "battery",
        "bms",
        "inverter",
        "converter",
        "power electronics",
        "rlc",
        "circuit",
        "electrochem",
    ),
    "electronic_signal": (
        "electronic",
        "sensor",
        "adc",
        "dac",
        "pwm",
        "signal",
        "firmware",
        "embedded",
        "microcontroller",
        "fpga",
        "telemetry",
    ),
    "thermal": (
        "thermal",
        "temperature",
        "heat",
        "cooling",
        "thermodynamic",
        "runaway",
        "dissipation",
    ),
    "fluid": (
        "fluid",
        "flow",
        "pressure",
        "hydro",
        "aero",
        "plasma",
        "pump",
        "valve",
        "cavitation",
    ),
    "software": (
        "software",
        "python",
        "cli",
        "api",
        "controller",
        "algorithm",
        "simulation",
        "agent",
        "runtime",
    ),
    "data": (
        "data",
        "json",
        "schema",
        "telemetry",
        "dataset",
        "ledger",
        "manifest",
        "report",
    ),
}


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class InventoryConfig:
    max_files_per_system: int = 256
    max_bytes_per_file: int = 128_000
    include_nested_prototypes: bool = True

    def validate(self) -> None:
        if self.max_files_per_system < 1 or self.max_bytes_per_file < 1:
            raise ValueError("finite scan budgets must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["scope"] = "finite execution budget; not a permanent repository or system cap"
        return payload


@dataclass(frozen=True)
class RepositorySystemRecord:
    path: str
    file_count_scanned: int
    domains: tuple[str, ...]
    physical_domains: tuple[str, ...]
    matched_keywords: tuple[str, ...]
    software_present: bool
    data_present: bool
    cyberphysical_candidate: bool
    integrated_candidate: bool
    confidence: float
    evidence_paths: tuple[str, ...]
    evidence_hash: str
    manual_review_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "file_count_scanned": self.file_count_scanned,
            "domains": list(self.domains),
            "physical_domains": list(self.physical_domains),
            "matched_keywords": list(self.matched_keywords),
            "software_present": self.software_present,
            "data_present": self.data_present,
            "cyberphysical_candidate": self.cyberphysical_candidate,
            "integrated_candidate": self.integrated_candidate,
            "confidence": self.confidence,
            "evidence_paths": list(self.evidence_paths),
            "evidence_hash": self.evidence_hash,
            "manual_review_required": self.manual_review_required,
        }


@dataclass(frozen=True)
class RepositoryInventoryReport:
    root: str
    records: tuple[RepositorySystemRecord, ...]
    cyberphysical_candidate_count: int
    integrated_candidate_count: int
    physical_only_candidate_count: int
    software_only_candidate_count: int
    domain_counts: dict[str, int]
    scan_config: InventoryConfig
    evidence_hash: str
    permanent_total_cap: None = None
    exhaustive_claim: bool = False
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "records": [item.to_dict() for item in self.records],
            "record_count": len(self.records),
            "cyberphysical_candidate_count": self.cyberphysical_candidate_count,
            "integrated_candidate_count": self.integrated_candidate_count,
            "physical_only_candidate_count": self.physical_only_candidate_count,
            "software_only_candidate_count": self.software_only_candidate_count,
            "domain_counts": dict(self.domain_counts),
            "scan_config": self.scan_config.to_dict(),
            "evidence_hash": self.evidence_hash,
            "permanent_total_cap": self.permanent_total_cap,
            "exhaustive_claim": self.exhaustive_claim,
            "physics_certified": self.physics_certified,
            "limitations": [
                "keyword evidence is a discovery heuristic, not semantic proof",
                "finite file and byte budgets can miss relevant content",
                "generated, binary, private and external artifacts are outside this scan",
                "manual review is mandatory before canonical classification",
            ],
        }


def _candidate_directories(root: Path, include_nested: bool) -> tuple[Path, ...]:
    candidates: set[Path] = set()
    for child in root.iterdir():
        if not child.is_dir() or child.name in EXCLUDED_TOP_LEVEL or child.name.startswith("."):
            continue
        if child.name in {"tests", "docs", "schemas", "examples", "configs", "scripts", "tools", "safety", "reports", "atlas", "canon", "paper"}:
            continue
        candidates.add(child)
        if include_nested and child.name in {"prototypes", "projects", "packages", "src"}:
            for nested in child.iterdir():
                if nested.is_dir() and not nested.name.startswith("."):
                    candidates.add(nested)
    return tuple(sorted(candidates, key=lambda item: item.as_posix()))


def _text_files(directory: Path, config: InventoryConfig) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix()):
        if len(files) >= config.max_files_per_system:
            break
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        files.append(path)
    return tuple(files)


def _read_text(path: Path, max_bytes: int) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _record_for(directory: Path, root: Path, config: InventoryConfig) -> RepositorySystemRecord | None:
    files = _text_files(directory, config)
    if not files:
        return None
    corpus_parts = [directory.name.lower().replace("_", "-")]
    evidence_paths: list[str] = []
    for path in files:
        text = _read_text(path, config.max_bytes_per_file)
        if text:
            corpus_parts.append(text)
            evidence_paths.append(path.relative_to(root).as_posix())
    corpus = "\n".join(corpus_parts)
    domains: list[str] = []
    matched: set[str] = set()
    domain_strength: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword in corpus]
        if found:
            domains.append(domain)
            matched.update(found)
            domain_strength[domain] = len(found)
    if not domains:
        return None
    physical = tuple(sorted(set(domains) & PHYSICAL_DOMAINS))
    software = "software" in domains
    data = "data" in domains
    cyberphysical = bool(physical) and software
    integrated = cyberphysical and (
        len(physical) >= 2
        or ("electrical_power" in domains and "electronic_signal" in domains)
        or ("mechanical_translational" in domains and "mechanical_rotational" in domains)
    )
    strength = sum(min(value, 8) for value in domain_strength.values())
    confidence = min(1.0, 0.08 * len(domains) + 0.012 * strength + 0.002 * len(files))
    payload = {
        "path": directory.relative_to(root).as_posix(),
        "files": evidence_paths,
        "domains": sorted(domains),
        "matched_keywords": sorted(matched),
        "cyberphysical_candidate": cyberphysical,
        "integrated_candidate": integrated,
    }
    return RepositorySystemRecord(
        path=directory.relative_to(root).as_posix(),
        file_count_scanned=len(files),
        domains=tuple(sorted(domains)),
        physical_domains=physical,
        matched_keywords=tuple(sorted(matched)),
        software_present=software,
        data_present=data,
        cyberphysical_candidate=cyberphysical,
        integrated_candidate=integrated,
        confidence=confidence,
        evidence_paths=tuple(evidence_paths[:32]),
        evidence_hash=_stable_hash(payload),
    )


def discover_repository_systems(
    root: str | Path,
    *,
    config: InventoryConfig | None = None,
) -> RepositoryInventoryReport:
    root_path = Path(root).resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError("inventory root must be an existing directory")
    cfg = config or InventoryConfig()
    cfg.validate()
    records = tuple(
        record
        for directory in _candidate_directories(root_path, cfg.include_nested_prototypes)
        if (record := _record_for(directory, root_path, cfg)) is not None
    )
    ordered = tuple(
        sorted(
            records,
            key=lambda item: (
                -int(item.integrated_candidate),
                -int(item.cyberphysical_candidate),
                -item.confidence,
                item.path,
            ),
        )
    )
    domain_counts = {domain: sum(domain in item.domains for item in ordered) for domain in DOMAINS}
    cyberphysical_count = sum(item.cyberphysical_candidate for item in ordered)
    integrated_count = sum(item.integrated_candidate for item in ordered)
    physical_only = sum(bool(item.physical_domains) and not item.software_present for item in ordered)
    software_only = sum(item.software_present and not item.physical_domains for item in ordered)
    payload = {
        "root": root_path.name,
        "records": [item.to_dict() for item in ordered],
        "config": cfg.to_dict(),
        "domain_counts": domain_counts,
    }
    return RepositoryInventoryReport(
        root=root_path.as_posix(),
        records=ordered,
        cyberphysical_candidate_count=cyberphysical_count,
        integrated_candidate_count=integrated_count,
        physical_only_candidate_count=physical_only,
        software_only_candidate_count=software_only,
        domain_counts=domain_counts,
        scan_config=cfg,
        evidence_hash=_stable_hash(payload),
    )


def summarize_inventory(report: RepositoryInventoryReport) -> dict[str, Any]:
    return {
        "root": report.root,
        "record_count": len(report.records),
        "cyberphysical_candidate_count": report.cyberphysical_candidate_count,
        "integrated_candidate_count": report.integrated_candidate_count,
        "physical_only_candidate_count": report.physical_only_candidate_count,
        "software_only_candidate_count": report.software_only_candidate_count,
        "domain_counts": report.domain_counts,
        "top_integrated_candidates": [
            {
                "path": item.path,
                "domains": list(item.domains),
                "confidence": item.confidence,
                "evidence_hash": item.evidence_hash,
            }
            for item in report.records
            if item.integrated_candidate
        ][:32],
        "evidence_hash": report.evidence_hash,
        "permanent_total_cap": report.permanent_total_cap,
        "exhaustive_claim": report.exhaustive_claim,
        "physics_certified": report.physics_certified,
    }
