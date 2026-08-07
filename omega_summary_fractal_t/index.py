from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

STRUCTURAL_COMPONENTS = ("documented", "implemented", "tested", "linked_ci", "schema_backed")


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _profile_from_metrics(status: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    documented = bool(metrics.get("documented") or int(metrics.get("documents", 0) or 0))
    implemented = bool(metrics.get("implemented") or int(metrics.get("code_files", 0) or 0))
    tested = bool(metrics.get("tested") or int(metrics.get("tests", 0) or 0))
    linked_ci = bool(int(metrics.get("workflows", 0) or 0))
    schema_backed = bool(metrics.get("schema_backed") or int(metrics.get("schemas", 0) or 0))
    components = {
        "documented": documented,
        "implemented": implemented,
        "tested": tested,
        "linked_ci": linked_ci,
        "schema_backed": schema_backed,
    }
    crystallization = sum(int(components[key]) for key in STRUCTURAL_COMPONENTS) / len(STRUCTURAL_COMPONENTS)
    missing: list[str] = []
    if not documented:
        missing.append("documentation")
    if not implemented:
        missing.append("implementation")
    if implemented and not tested:
        missing.append("focused_tests")
    if implemented and not linked_ci:
        missing.append("linked_ci")
    if implemented and not schema_backed:
        missing.append("machine_contract")
    return {
        "status": status,
        "components": components,
        "structural_crystallization": round(crystallization, 4),
        "structural_proof_debt": len(missing),
        "missing": missing,
        "code_files": int(metrics.get("code_files", 0) or 0),
        "tests": int(metrics.get("tests", 0) or 0),
        "workflows": int(metrics.get("workflows", 0) or 0),
        "documents": int(metrics.get("documents", 0) or 0),
        "schemas": int(metrics.get("schemas", 0) or 0),
        "first_seen": str(metrics.get("first_seen", "") or ""),
    }


def normalize_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize repository or corpus summary payload into one index snapshot."""

    entities: dict[str, dict[str, Any]] = {}
    source_kind = "repository"
    fingerprint = str(payload.get("cache_fingerprint", ""))
    root = str(payload.get("root", ""))
    generated_at = str(payload.get("generated_at", ""))
    relations: list[dict[str, str]] = []

    if isinstance(payload.get("repositories"), list):
        source_kind = "corpus"
        fingerprint = str(payload.get("fingerprint", ""))
        root = "corpus"
        for repository in payload.get("repositories", []):
            if not repository.get("available"):
                continue
            repo_name = str(repository.get("name", "repo"))
            for system in repository.get("systems", []):
                key = f"{repo_name}::{system.get('path', '')}"
                entities[key] = _profile_from_metrics(
                    str(system.get("status", "observed")),
                    system.get("metrics", {}),
                )
        for link in payload.get("cross_repo_links", []):
            relations.append(
                {
                    "source": str(link.get("source", "")),
                    "relation": str(link.get("relation", "")),
                    "target": str(link.get("target", "")),
                }
            )
    else:
        id_to_path = {
            str(node.get("id")): str(node.get("path", node.get("id", "")))
            for node in payload.get("nodes", [])
        }
        for node in payload.get("nodes", []):
            if node.get("kind") != "system" or not node.get("path"):
                continue
            entities[str(node["path"])] = _profile_from_metrics(
                str(node.get("status", "observed")),
                node.get("metrics", {}),
            )
        for edge in payload.get("edges", []):
            relation = str(edge.get("relation", ""))
            if not relation or relation == "CONTAINS":
                continue
            relations.append(
                {
                    "source": id_to_path.get(str(edge.get("source")), str(edge.get("source", ""))),
                    "relation": relation,
                    "target": id_to_path.get(str(edge.get("target")), str(edge.get("target", ""))),
                }
            )

    relations = sorted(relations, key=lambda item: (item["source"], item["relation"], item["target"]))
    return {
        "source_kind": source_kind,
        "root": root,
        "generated_at": generated_at,
        "fingerprint": fingerprint,
        "entities": {key: entities[key] for key in sorted(entities)},
        "relations": relations,
        "boundary": "structural repository evidence only; no scientific, commercial, legal or IP validation inferred",
    }


def _entry_hash(snapshot: Mapping[str, Any], previous_hash: str) -> str:
    canonical = json.dumps(
        {"previous_hash": previous_hash, "snapshot": snapshot},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_index(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {
            "schema_version": "1.0.0",
            "runs": [],
            "boundary": "append-only structural observation index; not a scientific progress ledger",
        }
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("runs"), list):
        raise ValueError("invalid corpus index")
    return payload


def verify_index(index: Mapping[str, Any]) -> bool:
    previous_hash = ""
    for run in index.get("runs", []):
        snapshot = run.get("snapshot", {})
        if str(run.get("previous_hash", "")) != previous_hash:
            return False
        expected = _entry_hash(snapshot, previous_hash)
        if str(run.get("entry_hash", "")) != expected:
            return False
        previous_hash = expected
    return True


def append_snapshot(
    index_path: str | Path,
    summary: str | Path | Mapping[str, Any],
) -> dict[str, Any]:
    """Append a unique summary snapshot to a logical append-only hash chain."""

    payload = _load_payload(summary)
    snapshot = normalize_snapshot(payload)
    index = load_index(index_path)
    if not verify_index(index):
        raise ValueError("corpus index hash chain is invalid")

    fingerprint = snapshot.get("fingerprint", "")
    if fingerprint and any(
        run.get("snapshot", {}).get("fingerprint") == fingerprint for run in index.get("runs", [])
    ):
        return index

    previous_hash = str(index["runs"][-1]["entry_hash"]) if index["runs"] else ""
    entry_hash = _entry_hash(snapshot, previous_hash)
    index["runs"].append(
        {
            "ordinal": len(index["runs"]) + 1,
            "previous_hash": previous_hash,
            "entry_hash": entry_hash,
            "snapshot": snapshot,
        }
    )
    target = Path(index_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return index


def longitudinal_metrics(index: Mapping[str, Any]) -> dict[str, Any]:
    """Compute run-to-run structural crystallization and proof-debt trends."""

    if not verify_index(index):
        raise ValueError("corpus index hash chain is invalid")
    observations: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for run in index.get("runs", []):
        ordinal = int(run.get("ordinal", 0))
        for entity, profile in run.get("snapshot", {}).get("entities", {}).items():
            observations.setdefault(str(entity), []).append((ordinal, dict(profile)))

    systems = []
    for entity in sorted(observations):
        history = observations[entity]
        first_ordinal, first = history[0]
        last_ordinal, last = history[-1]
        transitions = []
        previous = None
        for ordinal, profile in history:
            status = str(profile.get("status", "observed"))
            if previous is not None and status != previous:
                transitions.append({"run": ordinal, "from": previous, "to": status})
            previous = status
        denominator = max(1, len(history) - 1)
        crystallization_delta = round(
            float(last.get("structural_crystallization", 0.0))
            - float(first.get("structural_crystallization", 0.0)),
            4,
        )
        debt_delta = int(last.get("structural_proof_debt", 0)) - int(first.get("structural_proof_debt", 0))
        systems.append(
            {
                "entity": entity,
                "first_observed_run": first_ordinal,
                "last_observed_run": last_ordinal,
                "observed_runs": len(history),
                "status_first": first.get("status"),
                "status_last": last.get("status"),
                "status_transitions": transitions,
                "crystallization_first": first.get("structural_crystallization", 0.0),
                "crystallization_last": last.get("structural_crystallization", 0.0),
                "crystallization_delta": crystallization_delta,
                "crystallization_velocity_per_observed_run": round(crystallization_delta / denominator, 4),
                "proof_debt_first": first.get("structural_proof_debt", 0),
                "proof_debt_last": last.get("structural_proof_debt", 0),
                "proof_debt_delta": debt_delta,
            }
        )
    return {
        "schema_version": "1.0.0",
        "run_count": len(index.get("runs", [])),
        "valid_hash_chain": True,
        "systems": systems,
        "boundary": "structural crystallization velocity is repository-state change per observed run; it is not scientific progress, novelty or product traction",
    }


def render_longitudinal_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# LONGITUDINAL CRYSTALLIZATION",
        "",
        f"- runs indexés : **{report.get('run_count', 0)}**",
        f"- chaîne d'intégrité valide : **{bool(report.get('valid_hash_chain'))}**",
        "",
        "| Système | Runs | Statut | Cristallisation Δ | Vitesse/run | Dette Δ |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for item in report.get("systems", []):
        lines.append(
            f"| `{item['entity']}` | {item['observed_runs']} | {item['status_first']}→{item['status_last']} | "
            f"{item['crystallization_delta']:+.3f} | {item['crystallization_velocity_per_observed_run']:+.3f} | "
            f"{item['proof_debt_delta']:+d} |"
        )
    lines += ["", "## OAK boundary", "", str(report.get("boundary", "")), ""]
    return "\n".join(lines)


def write_longitudinal_reports(index_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    index = load_index(index_path)
    report = longitudinal_metrics(index)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "LONGITUDINAL_CRYSTALLIZATION.json"
    markdown_path = out / "LONGITUDINAL_CRYSTALLIZATION.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_longitudinal_markdown(report), encoding="utf-8")
    return {"longitudinal_json": json_path, "longitudinal_markdown": markdown_path}
