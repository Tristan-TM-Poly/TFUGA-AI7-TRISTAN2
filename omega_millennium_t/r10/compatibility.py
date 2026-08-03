from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .compiler import _run_campaign
from .model import CELL_SCHEMA, RuntimePolicy, canonical_json, stable_digest
from .store import AtlasStore

R03_MANIFEST_SCHEMA = "omega-problem-atlas-manifest-max/3"
R03_REPORT_SCHEMA = "omega-problem-atlas-report-max/3"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _jsonl_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def verify_r03_max_source(source_dir: str | Path) -> dict[str, Any]:
    source = Path(source_dir)
    manifest = _load_json(source / "manifest.json")
    report = _load_json(source / "report.json")
    blockers: list[str] = []
    if manifest.get("schema") != R03_MANIFEST_SCHEMA:
        blockers.append("r03_manifest_schema_mismatch")
    if report.get("schema") != R03_REPORT_SCHEMA:
        blockers.append("r03_report_schema_mismatch")
    manifest_digest = stable_digest(manifest)
    if report.get("manifest_digest") != manifest_digest:
        blockers.append("r03_manifest_digest_mismatch")

    verified_artifacts: list[dict[str, Any]] = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        blockers.append("r03_manifest_artifacts_invalid")
        artifacts = []
    for receipt in artifacts:
        if not isinstance(receipt, Mapping):
            blockers.append("r03_artifact_receipt_invalid")
            continue
        name = str(receipt.get("path", ""))
        path = source / name
        if not name or not path.exists() or not path.is_file():
            blockers.append(f"r03_artifact_missing:{name}")
            continue
        actual = {
            "path": name,
            "sha256": _sha256_bytes(path),
            "bytes": path.stat().st_size,
            "rows": _jsonl_rows(path) if path.suffix == ".jsonl" else None,
        }
        for key in ("sha256", "bytes", "rows"):
            if actual[key] != receipt.get(key):
                blockers.append(f"r03_artifact_{key}_mismatch:{name}")
        verified_artifacts.append(actual)

    report_without_digest = {key: value for key, value in report.items() if key != "digest"}
    report_digest = stable_digest(report_without_digest)
    if report.get("digest") != report_digest:
        blockers.append("r03_report_digest_mismatch")
    if report.get("research_cell_count") != next(
        (item["rows"] for item in verified_artifacts if item["path"] == "research_cells.jsonl"),
        None,
    ):
        blockers.append("r03_research_cell_count_mismatch")
    for forbidden in (
        "solution_claimed",
        "formal_proof_claimed",
        "scientific_validation_claimed",
        "current_status_certification_claimed",
    ):
        if report.get(forbidden) is not False:
            blockers.append(f"r03_forbidden_claim:{forbidden}")
    if report.get("permanent_total_cap", "missing") is not None:
        blockers.append("r03_permanent_total_cap_not_null")

    receipt = {
        "schema": "omega-problem-r03-compatibility-receipt/10",
        "valid": not blockers,
        "blockers": sorted(set(blockers)),
        "r03_manifest_digest": manifest_digest,
        "r03_report_digest": report_digest,
        "r03_report_stored_digest": report.get("digest"),
        "r03_problem_count": report.get("deduplicated_problem_count"),
        "r03_target_count": report.get("research_target_count"),
        "r03_cell_count": report.get("research_cell_count"),
        "artifacts": sorted(verified_artifacts, key=lambda item: item["path"]),
        "finite_fixture_is_not_unlimited_capacity_proof": True,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    receipt["receipt_digest"] = stable_digest(receipt)
    return receipt


def _priority_integer(value: Any) -> int:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("R0.3 priority_score must be numeric")
    return int(round(float(value) * 1_000_000_000))


def _iter_r03_cells(
    path: Path,
    *,
    start_ordinal: int,
) -> Iterator[tuple[int, Mapping[str, Any], str]]:
    with path.open("r", encoding="utf-8") as handle:
        for ordinal, line in enumerate(handle, start=1):
            if ordinal < start_ordinal:
                continue
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError(f"r03_cell_not_object:{ordinal}")
            methods = raw.get("methods", [])
            method = "+".join(map(str, methods)) if isinstance(methods, list) else str(methods)
            row = {
                "schema": CELL_SCHEMA,
                "cell_id": str(raw["cell_id"]),
                "problem_id": str(raw["problem_id"]),
                "target_id": str(raw["target_id"]),
                "front": str(raw["front"]),
                "method": method,
                "priority": _priority_integer(raw["priority_score"]),
                "source_ref": f"r03max://research_cells.jsonl#{ordinal}",
                "payload": {
                    "r03_max_cell": raw,
                    "r03_source_ordinal": ordinal,
                },
            }
            yield ordinal, row, canonical_json(row) + "\n"


def ingest_r03_max(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    policy: RuntimePolicy | None = None,
    resume: bool = False,
    max_items: int | None = None,
    clean: bool = True,
) -> dict[str, Any]:
    source = Path(source_dir)
    receipt = verify_r03_max_source(source)
    if receipt["valid"] is not True:
        raise ValueError(f"invalid R0.3 source: {receipt['blockers']}")
    runtime = policy or RuntimePolicy()
    output = Path(output_dir)
    start = 1
    if resume and (output / "atlas.sqlite3").exists():
        with AtlasStore(output / "atlas.sqlite3", runtime) as store:
            checkpoint = store.load_checkpoint()
            if checkpoint is not None:
                start = int(checkpoint["next_source_ordinal"])
    rows = _iter_r03_cells(source / "research_cells.jsonl", start_ordinal=start)
    report = _run_campaign(
        output_dir=output,
        source_kind="r03_max",
        source_digest=receipt["r03_manifest_digest"],
        rows=rows,
        policy=runtime,
        resume=resume,
        max_items=max_items,
        expected_total_rows=int(receipt["r03_cell_count"]),
        clean=clean,
    )
    with AtlasStore(output / "atlas.sqlite3", runtime) as store:
        with store.transaction():
            existing = store.get_metadata("r03_compatibility_receipt")
            if existing is not None and existing != receipt:
                raise ValueError("r03_compatibility_receipt_mismatch")
            store.set_metadata("r03_compatibility_receipt", receipt)
    (output / "r03_compatibility.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
