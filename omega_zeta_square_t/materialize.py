"""Deterministic materialization of Ω-RH-PROOF-OS-T∞ research state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .bibliography import validate_bibliography_ledger
from .cvcd import cvcd_support_report
from .obligations import export_obligation_bundle, obligations_from_proof_graph
from .proof_graph import validate_proof_graph


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> str:
    data = _canonical_bytes(value)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def materialize_research_bundle(
    graph: dict[str, Any],
    bibliography: dict[str, Any],
    output_dir: str | Path,
    *,
    cvcd_target: str = "rh",
    theorem_specs: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Write deterministic public-safe proof-research artifacts and manifest.

    The bundle records current research state. Proved derived criteria may be
    included, but ``solution_claimed`` remains false unless a separate explicit
    RH-solution gate is ever satisfied.
    """

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    graph_errors = validate_proof_graph(graph)
    bibliography_errors = validate_bibliography_ledger(graph, bibliography)
    obligations = export_obligation_bundle(obligations_from_proof_graph(graph))
    cvcd = cvcd_support_report(graph, cvcd_target)
    theorem_specs = {} if theorem_specs is None else dict(theorem_specs)
    theorem_errors: list[str] = []
    for name, spec in theorem_specs.items():
        if not isinstance(spec, dict):
            theorem_errors.append(f"{name}: theorem spec must be an object")
            continue
        if spec.get("solution_claimed") is not False:
            theorem_errors.append(f"{name}: theorem spec must explicitly set solution_claimed=false")
        if not isinstance(spec.get("status"), str):
            theorem_errors.append(f"{name}: theorem spec status must be a string")

    oak = {
        "schema": "omega-rh-proof-os-oak-receipt/2",
        "solution_claimed": False,
        "proof_graph_valid": not graph_errors,
        "bibliography_valid": not bibliography_errors,
        "theorem_specs_valid": not theorem_errors,
        "graph_errors": graph_errors,
        "bibliography_errors": bibliography_errors,
        "theorem_errors": theorem_errors,
        "theorem_spec_count": len(theorem_specs),
        "cvcd_structural_only": True,
        "cvcd_proves_target": False,
        "proof_obligations_remaining": obligations["obligation_count"],
        "promotion": (
            "RESEARCH_BUNDLE_VALID"
            if not graph_errors and not bibliography_errors and not theorem_errors
            else "BLOCK"
        ),
    }

    artifacts: dict[str, Any] = {
        "proof_graph.json": graph,
        "bibliography_ledger.json": bibliography,
        "proof_obligations.json": obligations,
        "cvcd_support.json": cvcd,
        "oak_receipt.json": oak,
    }
    for name, spec in theorem_specs.items():
        artifacts[f"theorems/{name}"] = spec

    hashes: dict[str, str] = {}
    for name in sorted(artifacts):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        hashes[name] = _write_json(path, artifacts[name])

    manifest = {
        "schema": "omega-rh-proof-os-bundle/2",
        "solution_claimed": False,
        "cvcd_target": cvcd_target,
        "artifact_sha256": hashes,
        "theorem_specs": sorted(theorem_specs),
        "oak_promotion": oak["promotion"],
        "proof_obligations_remaining": obligations["obligation_count"],
    }
    manifest_hash = _write_json(out / "manifest.json", manifest)
    return {
        "manifest": manifest,
        "manifest_sha256": manifest_hash,
        "output_dir": str(out),
        "proves_rh": False,
    }


def materialize_from_files(
    graph_path: str | Path,
    bibliography_path: str | Path,
    output_dir: str | Path,
    *,
    cvcd_target: str = "rh",
) -> dict[str, Any]:
    graph_path = Path(graph_path)
    bibliography_path = Path(bibliography_path)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    bibliography = json.loads(bibliography_path.read_text(encoding="utf-8"))
    theorem_specs: dict[str, dict[str, Any]] = {}
    for path in sorted(graph_path.parent.glob("*_theorem.json")):
        theorem_specs[path.name] = json.loads(path.read_text(encoding="utf-8"))
    return materialize_research_bundle(
        graph,
        bibliography,
        output_dir,
        cvcd_target=cvcd_target,
        theorem_specs=theorem_specs,
    )
