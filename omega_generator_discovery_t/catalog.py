"""Streaming API for the Ω-GENERATOR-DISCOVERY R0.2 massive atlas."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True, slots=True)
class GeneratorRecord:
    id: str
    domain: str
    family: str
    scale: str
    representation: str
    status: str
    invariant: str
    risk: str
    parameter_count: int
    supports_inverse: bool
    oak_gate: str
    benchmark_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "GeneratorRecord":
        return cls(
            id=str(raw["id"]),
            domain=str(raw["domain"]),
            family=str(raw["family"]),
            scale=str(raw["scale"]),
            representation=str(raw["representation"]),
            status=str(raw["status"]),
            invariant=str(raw["invariant"]),
            risk=str(raw["risk"]),
            parameter_count=int(raw["parameter_count"]),
            supports_inverse=bool(raw["supports_inverse"]),
            oak_gate=str(raw["oak_gate"]),
            benchmark_ids=tuple(str(value) for value in raw["benchmark_ids"]),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    id: str
    generator_id: str
    variant: int
    input_seed: int
    parameters: dict[str, float]
    expected: dict[str, object]
    negative_control: str
    oak_status: str

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "BenchmarkRecord":
        return cls(
            id=str(raw["id"]),
            generator_id=str(raw["generator_id"]),
            variant=int(raw["variant"]),
            input_seed=int(raw["input_seed"]),
            parameters={str(key): float(value) for key, value in dict(raw["parameters"]).items()},
            expected=dict(raw["expected"]),
            negative_control=str(raw["negative_control"]),
            oak_status=str(raw["oak_status"]),
        )


@dataclass(frozen=True, slots=True)
class CatalogAudit:
    valid: bool
    generators: int
    benchmarks: int
    linked_generators: int
    duplicate_generator_ids: tuple[str, ...]
    missing_generator_links: tuple[str, ...]
    wrong_benchmark_coverage: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_root() -> Path:
    return Path(__file__).resolve().parents[1] / "generated" / "omega_generator_discovery_r02"


def _paths(root: Path, subdirectory: str, pattern: str) -> tuple[Path, ...]:
    paths = tuple(sorted((root / subdirectory).glob(pattern)))
    if not paths:
        raise FileNotFoundError(f"No {pattern} files below {root / subdirectory}")
    return paths


def _iter_jsonl(paths: tuple[Path, ...]) -> Iterator[dict[str, object]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected JSON object")
                yield value


def iter_generators(root: str | Path | None = None) -> Iterator[GeneratorRecord]:
    atlas = Path(root) if root is not None else default_root()
    for raw in _iter_jsonl(_paths(atlas, "catalogs", "generator_catalog_*.jsonl")):
        yield GeneratorRecord.from_dict(raw)


def iter_benchmarks(root: str | Path | None = None) -> Iterator[BenchmarkRecord]:
    atlas = Path(root) if root is not None else default_root()
    for raw in _iter_jsonl(_paths(atlas, "benchmarks", "benchmark_matrix_*.jsonl")):
        yield BenchmarkRecord.from_dict(raw)


def query_generators(
    *,
    domain: str | None = None,
    family: str | None = None,
    scale: str | None = None,
    status: str | None = None,
    limit: int | None = 100,
    root: str | Path | None = None,
) -> tuple[GeneratorRecord, ...]:
    result: list[GeneratorRecord] = []
    for record in iter_generators(root):
        if domain is not None and record.domain != domain:
            continue
        if family is not None and record.family != family:
            continue
        if scale is not None and record.scale != scale:
            continue
        if status is not None and record.status != status:
            continue
        result.append(record)
        if limit is not None and len(result) >= limit:
            break
    return tuple(result)


def catalog_statistics(root: str | Path | None = None) -> dict[str, object]:
    domains: Counter[str] = Counter()
    families: Counter[str] = Counter()
    scales: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    count = 0
    for record in iter_generators(root):
        count += 1
        domains[record.domain] += 1
        families[record.family] += 1
        scales[record.scale] += 1
        statuses[record.status] += 1
    return {
        "generators": count,
        "domains": dict(sorted(domains.items())),
        "families": dict(sorted(families.items())),
        "scales": dict(sorted(scales.items())),
        "statuses": dict(sorted(statuses.items())),
    }


def audit_catalog(root: str | Path | None = None) -> CatalogAudit:
    atlas = Path(root) if root is not None else default_root()
    generator_paths = _paths(atlas, "catalogs", "generator_catalog_*.jsonl")
    benchmark_paths = _paths(atlas, "benchmarks", "benchmark_matrix_*.jsonl")
    generator_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for record in iter_generators(atlas):
        if record.id in generator_ids:
            duplicate_ids.add(record.id)
        generator_ids.add(record.id)
    links: Counter[str] = Counter(record.generator_id for record in iter_benchmarks(atlas))
    missing = tuple(sorted(generator_ids - links.keys()))
    wrong = tuple(sorted(record_id for record_id, coverage in links.items() if coverage != 2))
    digest = hashlib.sha256()
    for path in (*generator_paths, *benchmark_paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    benchmark_count = sum(links.values())
    return CatalogAudit(
        valid=(
            len(generator_ids) == 8192
            and benchmark_count == 16384
            and not duplicate_ids
            and not missing
            and not wrong
        ),
        generators=len(generator_ids),
        benchmarks=benchmark_count,
        linked_generators=len(links),
        duplicate_generator_ids=tuple(sorted(duplicate_ids)),
        missing_generator_links=missing,
        wrong_benchmark_coverage=wrong,
        fingerprint=digest.hexdigest(),
    )
