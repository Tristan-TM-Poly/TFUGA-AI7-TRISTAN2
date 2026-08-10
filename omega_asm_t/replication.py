from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re
from typing import Iterable

from .benchmark import summarize_samples


_DERIVED_METRICS = (
    "ipc",
    "cycles_per_instruction",
    "branch_miss_rate",
    "cache_miss_rate",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _cache_identity(caches: object) -> list[dict[str, object]]:
    if not isinstance(caches, list):
        return []
    rows: list[dict[str, object]] = []
    for item in caches:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "level": item.get("level"),
                "cache_type": item.get("cache_type"),
                "size_bytes": item.get("size_bytes"),
                "line_size_bytes": item.get("line_size_bytes"),
                "ways_of_associativity": item.get("ways_of_associativity"),
                "number_of_sets": item.get("number_of_sets"),
            }
        )
    rows.sort(
        key=lambda row: (
            str(row.get("level")),
            str(row.get("cache_type")),
            str(row.get("size_bytes")),
            str(row.get("line_size_bytes")),
        )
    )
    return rows


def canonical_machine_identity(machine: dict[str, object]) -> dict[str, object]:
    """Return the stable target identity subset used for P6 grouping.

    Ephemeral runner names, current frequency, governor, OS patch level and toolchain
    versions are intentionally excluded from *identity* while remaining available in
    the original P5 reports as execution-condition provenance.
    """

    features = machine.get("isa_features")
    feature_list = sorted(str(item) for item in features) if isinstance(features, list) else []
    feature_digest = hashlib.sha256("\n".join(feature_list).encode("utf-8")).hexdigest()
    return {
        "architecture": machine.get("architecture"),
        "vendor": machine.get("vendor"),
        "family": machine.get("family"),
        "model": machine.get("model"),
        "stepping": machine.get("stepping"),
        "model_name": machine.get("model_name"),
        "isa_features_sha256": feature_digest,
        "caches": _cache_identity(machine.get("caches")),
    }


def machine_fingerprint(machine: dict[str, object]) -> str:
    canonical = canonical_machine_identity(machine)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _identity_is_informative(identity: dict[str, object]) -> bool:
    architecture = identity.get("architecture")
    if not isinstance(architecture, str) or not architecture or architecture == "unknown":
        return False
    return any(identity.get(key) not in (None, "", "unknown") for key in ("vendor", "model", "model_name"))


def _binary_sha(report: dict[str, object]) -> str | None:
    binary = report.get("binary")
    if not isinstance(binary, dict) or binary.get("exists") is not True:
        return None
    sha = binary.get("sha256")
    if not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
        return None
    return sha


def validate_p5_replication_input(report: object) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ("report is not an object",)
    if report.get("evidence_level") != "P5-hardware-counters":
        errors.append("evidence_level is not P5-hardware-counters")
    if report.get("availability") not in {"available", "partial", "unavailable"}:
        errors.append("invalid availability")
    if report.get("authority") != "review_only":
        errors.append("authority is not review_only")
    machine = report.get("machine")
    if not isinstance(machine, dict):
        errors.append("machine manifest missing")
    if report.get("availability") == "available" and _binary_sha(report) is None:
        errors.append("available P5 evidence lacks measured-binary SHA-256")
    return tuple(errors)


@dataclass(frozen=True)
class ReplicationGroup:
    replication_key: str
    machine_fingerprint: str
    machine_identity: dict[str, object]
    binary_sha256: str
    input_count: int
    available_count: int
    partial_count: int
    unavailable_count: int
    qualifies_for_identified_target_replication: bool
    source_indexes: tuple[int, ...]
    metrics: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["source_indexes"] = list(self.source_indexes)
        return data


def _replication_key(machine_sha: str, binary_sha: str) -> str:
    return hashlib.sha256(f"{machine_sha}:{binary_sha}".encode("ascii")).hexdigest()


def _metric_summaries(reports: list[dict[str, object]]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for metric in _DERIVED_METRICS:
        values: list[float] = []
        for report in reports:
            derived = report.get("derived")
            if not isinstance(derived, dict):
                continue
            value = derived.get(metric)
            if isinstance(value, (int, float)) and math.isfinite(float(value)) and float(value) >= 0.0:
                values.append(float(value))
        if values:
            result[metric] = summarize_samples(values).to_dict()
    return result


def aggregate_p5_reports(
    reports: Iterable[dict[str, object]], *, min_replicates: int = 3
) -> dict[str, object]:
    if min_replicates < 2:
        raise ValueError("min_replicates must be at least 2")

    rows = list(reports)
    excluded: list[dict[str, object]] = []
    buckets: dict[tuple[str, str], list[tuple[int, dict[str, object]]]] = {}

    for index, report in enumerate(rows):
        errors = validate_p5_replication_input(report)
        if errors:
            excluded.append({"index": index, "reasons": list(errors)})
            continue
        machine = report["machine"]
        assert isinstance(machine, dict)
        identity = canonical_machine_identity(machine)
        if not _identity_is_informative(identity):
            excluded.append({"index": index, "reasons": ["machine identity is not informative enough for P6"]})
            continue
        binary_sha = _binary_sha(report)
        if binary_sha is None:
            excluded.append({"index": index, "reasons": ["measured-binary SHA-256 missing"]})
            continue
        machine_sha = machine_fingerprint(machine)
        buckets.setdefault((machine_sha, binary_sha), []).append((index, report))

    groups: list[ReplicationGroup] = []
    for (machine_sha, binary_sha), entries in sorted(buckets.items()):
        group_reports = [report for _, report in entries]
        available = [report for report in group_reports if report.get("availability") == "available"]
        partial_count = sum(report.get("availability") == "partial" for report in group_reports)
        unavailable_count = sum(report.get("availability") == "unavailable" for report in group_reports)
        first_machine = group_reports[0]["machine"]
        assert isinstance(first_machine, dict)
        groups.append(
            ReplicationGroup(
                replication_key=_replication_key(machine_sha, binary_sha),
                machine_fingerprint=machine_sha,
                machine_identity=canonical_machine_identity(first_machine),
                binary_sha256=binary_sha,
                input_count=len(group_reports),
                available_count=len(available),
                partial_count=partial_count,
                unavailable_count=unavailable_count,
                qualifies_for_identified_target_replication=len(available) >= min_replicates,
                source_indexes=tuple(index for index, _ in entries),
                metrics=_metric_summaries(available),
            )
        )

    qualified = [group for group in groups if group.qualifies_for_identified_target_replication]
    if len(qualified) == 1 and len(groups) == 1:
        status = "replicated_identified_target"
    elif len(qualified) == 1:
        status = "replicated_target_with_additional_groups"
    elif len(qualified) > 1:
        status = "multiple_replicated_targets"
    elif len(groups) > 1:
        status = "mixed_or_insufficient_targets"
    else:
        status = "insufficient_replication"

    eligible_reports = sum(group.input_count for group in groups)
    available_reports = sum(group.available_count for group in groups)
    return {
        "schema_version": 1,
        "evidence_level": "P6-replication-campaign",
        "status": status,
        "claim_scope": "replicated_identified_target_only",
        "authority": "review_only",
        "warning": (
            "P6 grouping supports target-specific replicated evidence only; it is not a universal ISA or language performance claim"
        ),
        "minimum_available_replicates": min_replicates,
        "input_report_count": len(rows),
        "eligible_report_count": eligible_reports,
        "available_report_count": available_reports,
        "excluded_reports": excluded,
        "groups": [group.to_dict() for group in groups],
        "promotion_contract": {
            "same_machine_fingerprint_required": True,
            "same_binary_sha256_required": True,
            "available_p5_reports_required": min_replicates,
            "partial_or_unavailable_reports_count_toward_threshold": False,
            "universal_claim_allowed": False,
            "automatic_authority_promotion": False,
        },
    }
