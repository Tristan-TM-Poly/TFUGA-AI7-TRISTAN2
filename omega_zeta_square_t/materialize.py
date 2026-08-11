"""Deterministic materialization of Ω-RH-PROOF-OS-T∞ research state."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

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
) -> dict[str, Any]:
    """Write deterministic public-safe proof-research artifacts and manifest.

    The bundle records the current research state; it never promotes an open or
    conjectural mathematical node and always declares ``solution_claimed=false``.
    """

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    graph_errors = validate_proof_graph(graph)
    bibliography_errors = validate_bibliography_ledger(graph, bibliography)
    obligations = export_obligation_bundle(obligations_from_proof_graph(graph))
    cvcd = cvcd_support_report(graph, cvcd_target)
    oak = {
        "schema": "omega-rh-proof-os-oak-receipt/1",
        "solution_claimed": False,
        "proof_graph_valid": not graph_errors,
        "bibliography_valid": not bibliography_errors,
        "graph_errors": graph_errors,
        "bibliography_errors": bibliography_errors,
        "cvcd_structural_only": True,
        "cvcd_proves_target": False,
        "proof_obligations_remaining": obligations["obligation_count"],
        "promotion": "RESEARCH_BUNDLE_VALID" if not graph_errors and not bibliography_errors else "BLOCK",
    }

    artifacts = {
        "proof_graph.json": graph,
        "bibliography_ledger.json": bibliography,
        "proof_obligations.json": obligations,
        "cvcd_support.json": cvcd,
        "oak_receipt.json": oak,
    }
    hashes: dict[str, str] = {}
    for name in sorted(artifacts):
        hashes[name] = _write_json(out / name, artifacts[name])

    manifest = {
        "schema": "omega-rh-proof-os-bundle/1",
        "solution_claimed": False,
        "cvcd_target": cvcd_target,
        "artifact_sha256": hashes,
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
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    bibliography = json.loads(Path(bibliography_path).read_text(encoding="utf-8"))
    return materialize_research_bundle(graph, bibliography, output_dir, cvcd_target=cvcd_target)
