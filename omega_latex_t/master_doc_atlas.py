from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Mapping

ATLAS_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

OAK_BOUNDARIES = [
    "REPOSITORY_PRESENT != FUNCTIONAL_SYSTEM",
    "MODULE_HASH_EQUALITY != SEMANTIC_EQUIVALENCE",
    "COMPONENT_NAME_MATCH != SHARED_IMPLEMENTATION",
    "REPOSITORY_OVERLAP != SUPERSESSION",
    "CLAIM_DUPLICATE != CLAIM_TRUE",
    "REVIEW_BINDING_VOLUME != EVIDENCE_STRENGTH",
    "ARTIFACT_ARCHIVED != INDEPENDENT_REPLICATION",
    "GRAPH_CONNECTIVITY != CAUSALITY_OR_PROOF",
    "DOCUMENTATION_COVERAGE != CLAIM_VALIDITY",
]


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


def _safe_id(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "unnamed"


def _repo_short(repo: str) -> str:
    return repo.split("/", 1)[-1]


def load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("registry_schema") != "omega-master-doc-source-registry-v1":
        raise ValueError(f"unsupported registry schema in {path}")
    repositories = list(payload.get("repositories", []))
    if not repositories:
        raise ValueError("at least one repository source receipt is required")
    names = [x.get("repository") for x in repositories]
    if any(not x for x in names) or len(names) != len(set(names)):
        raise ValueError("repository names must be present and unique")
    return payload


def _validate_registry(registry: Mapping[str, Any]) -> None:
    repositories = registry["repositories"]
    totals = registry["totals"]
    checks = {
        "module_observations": sum(int(x.get("module_count", 0)) for x in repositories),
        "public_symbol_observations": sum(int(x.get("public_symbol_count", 0)) for x in repositories),
        "structural_receipt_observations": sum(int(x.get("structural_receipt_count", 0)) for x in repositories),
        "claim_candidates": sum(int(x.get("claim_count", 0)) for x in repositories),
        "review_only_claim_evidence_bindings": sum(int(x.get("review_binding_count", 0)) for x in repositories),
        "placeholder_observations": sum(int(x.get("placeholder_count", 0)) for x in repositories),
        "execution_receipts": sum(int(x.get("execution_receipt_count", 0)) for x in repositories),
    }
    for key, expected in checks.items():
        if int(totals.get(key, -1)) != expected:
            raise ValueError(f"registry total mismatch for {key}: {totals.get(key)} != {expected}")
    if int(totals.get("cross_repository_identical_module_hash_groups", -1)) != len(registry.get("cross_repository_identical_modules", [])):
        raise ValueError("module-hash group count mismatch")
    for source in repositories:
        artifact = source.get("artifact", {})
        if len(str(artifact.get("artifact_sha256", ""))) != 64:
            raise ValueError(f"invalid artifact digest for {source.get('repository')}")


def build_atlas(registry: Mapping[str, Any]) -> dict[str, Any]:
    _validate_registry(registry)
    repositories = sorted((dict(x) for x in registry["repositories"]), key=lambda x: x["repository"])
    atlas = {
        "atlas_version": ATLAS_VERSION,
        "schema_version": SCHEMA_VERSION,
        "repository_count": len(repositories),
        "repositories": repositories,
        "totals": dict(registry["totals"]),
        "repository_similarity": list(registry.get("repository_similarity", [])),
        "shared_component_candidates": list(registry.get("shared_component_candidates", [])),
        "cross_repository_identical_modules": list(registry.get("cross_repository_identical_modules", [])),
        "cross_repository_duplicate_claims": list(registry.get("cross_repository_duplicate_claims", [])),
        "source_snapshots": [
            {
                "repository": x["repository"],
                "source_commit": x["source_commit"],
                "artifact_id": x["artifact"]["artifact_id"],
                "artifact_sha256": x["artifact"]["artifact_sha256"],
                "campaign_fingerprint": x["campaign_fingerprint"],
            }
            for x in repositories
        ],
        "derivation": registry.get("derivation"),
        "oak_boundaries": OAK_BOUNDARIES,
        "truth_boundary": "cross-repository atlas is provenance and structural evidence; it does not certify semantic equivalence, scientific truth, product maturity, or canonical supersession",
    }
    atlas["atlas_fingerprint"] = _sha({k: v for k, v in atlas.items() if k != "atlas_fingerprint"})
    return atlas


def render_markdown(atlas: Mapping[str, Any]) -> str:
    t = atlas["totals"]
    lines = [
        "# Ω-MASTER-DOC-ATLAS-T∞ — Multi-repository atlas",
        "",
        f"Atlas version: `{atlas['atlas_version']}`  ",
        f"Fingerprint: `{atlas['atlas_fingerprint']}`",
        "",
        "## Global receipt",
        "",
        f"- repositories: **{atlas['repository_count']}**",
        f"- module observations: **{t['module_observations']}**",
        f"- unique module hashes: **{t['unique_module_hashes']}**",
        f"- identical cross-repository module-hash groups: **{t['cross_repository_identical_module_hash_groups']}**",
        f"- public symbol observations: **{t['public_symbol_observations']}**",
        f"- structural evidence receipts: **{t['structural_receipt_observations']}**",
        f"- explicit claim candidates: **{t['claim_candidates']}**",
        f"- review-only claim↔evidence links: **{t['review_only_claim_evidence_bindings']}**",
        f"- placeholders observed: **{t['placeholder_observations']}**",
        f"- execution receipts: **{t['execution_receipts']}**",
        "",
        "## Repository roots",
        "",
        "| Repository | Visibility | Source commit | Modules | Symbols | Claims | Review links | Placeholders | Artifact |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for repo in atlas["repositories"]:
        lines.append(
            f"| `{repo['repository']}` | {repo['visibility']} | `{repo['source_commit'][:12]}` | {repo['module_count']} | {repo['public_symbol_count']} | {repo['claim_count']} | {repo['review_binding_count']} | {repo['placeholder_count']} | `{repo['artifact']['artifact_id']}` |"
        )
    lines += ["", "## Highest module-hash overlaps", "", "| Left | Right | Shared hashes | Jaccard |", "|---|---|---:|---:|"]
    for row in sorted(atlas["repository_similarity"], key=lambda x: (-x["shared_module_hashes"], -x["jaccard"], x["left"], x["right"]))[:15]:
        lines.append(f"| `{_repo_short(row['left'])}` | `{_repo_short(row['right'])}` | {row['shared_module_hashes']} | {row['jaccard']:.6f} |")
    lines += ["", "## Shared component-name candidates", ""]
    if atlas["shared_component_candidates"]:
        for item in atlas["shared_component_candidates"]:
            repos = ", ".join(f"`{_repo_short(m['repository'])}`" for m in item["members"])
            lines.append(f"- **{item['normalized_name']}** — {item['repository_count']} repositories: {repos}")
    else:
        lines.append("No repeated component-name candidate was observed.")
    lines += ["", "## Cross-repository duplicate claim candidates", ""]
    if atlas["cross_repository_duplicate_claims"]:
        for item in atlas["cross_repository_duplicate_claims"]:
            lines.append(f"- `{item['claim_text_sha256'][:16]}` observed in {item['repository_count']} repositories — `CLAIM_DUPLICATE != CLAIM_TRUE`")
    else:
        lines.append("No exact normalized claim text was observed in more than one repository.")
    lines += ["", "## OAK boundaries", ""]
    lines.extend(f"- `{b}`" for b in atlas["oak_boundaries"])
    lines += ["", f"> {atlas['truth_boundary']}", ""]
    return "\n".join(lines)


def _csv(rows: list[Mapping[str, Any]], fields: list[str]) -> str:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({f: row.get(f, "") for f in fields})
    return out.getvalue()


def render_repository_csv(atlas: Mapping[str, Any]) -> str:
    fields = ["repository", "visibility", "source_commit", "module_count", "unique_module_hash_count", "public_symbol_count", "structural_receipt_count", "claim_count", "review_binding_count", "execution_receipt_count", "placeholder_count", "component_candidate_count"]
    return _csv(list(atlas["repositories"]), fields)


def render_similarity_csv(atlas: Mapping[str, Any]) -> str:
    return _csv(list(atlas["repository_similarity"]), ["left", "right", "shared_module_hashes", "union_module_hashes", "jaccard", "boundary"])


def render_graphml(atlas: Mapping[str, Any]) -> str:
    nodes = []
    edges = []
    for repo in atlas["repositories"]:
        rid = "repo:" + repo["repository"]
        nodes.append((rid, repo["repository"], "repository"))
    for i, component in enumerate(atlas["shared_component_candidates"]):
        cid = f"component:{i}:{component['normalized_name']}"
        nodes.append((cid, component["normalized_name"], "component-candidate"))
        for member in component["members"]:
            edges.append(("component-member", "repo:" + member["repository"], cid))
    for i, group in enumerate(atlas["cross_repository_identical_modules"]):
        mid = f"hash:{i}:{group['sha256']}"
        nodes.append((mid, group["sha256"], "identical-module-hash"))
        for repo in group["repositories"]:
            edges.append(("identical-module-observation", "repo:" + repo, mid))
    def esc(x: str) -> str:
        return x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">', '<key id="label" for="node" attr.name="label" attr.type="string"/>', '<key id="kind" for="node" attr.name="kind" attr.type="string"/>', '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>', '<graph id="omega-master-doc-atlas" edgedefault="undirected">']
    for nid, label, kind in nodes:
        lines.append(f'<node id="{esc(nid)}"><data key="label">{esc(label)}</data><data key="kind">{esc(kind)}</data></node>')
    for idx, (rel, source, target) in enumerate(edges):
        lines.append(f'<edge id="e{idx}" source="{esc(source)}" target="{esc(target)}"><data key="relation">{esc(rel)}</data></edge>')
    lines += ["</graph>", "</graphml>", ""]
    return "\n".join(lines)


def render_dot(atlas: Mapping[str, Any]) -> str:
    lines = ["graph omega_master_doc_atlas {"]
    for repo in atlas["repositories"]:
        rid = _safe_id(repo["repository"])
        lines.append(f'  "{rid}" [label="{repo["repository"]}"];')
    for idx, component in enumerate(atlas["shared_component_candidates"]):
        cid = f"component_{idx}_{_safe_id(component['normalized_name'])}"
        lines.append(f'  "{cid}" [label="component:{component["normalized_name"]}"];')
        for member in component["members"]:
            lines.append(f'  "{_safe_id(member["repository"])}" -- "{cid}";')
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_bundle(registry_path: Path, output_dir: Path) -> dict[str, Any]:
    atlas = build_atlas(load_registry(registry_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "MASTER_REPOSITORY_ATLAS.md": render_markdown(atlas),
        "master-atlas.json": json.dumps(atlas, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "repositories.csv": render_repository_csv(atlas),
        "repository-similarity.csv": render_similarity_csv(atlas),
        "graph/master-atlas.graphml": render_graphml(atlas),
        "graph/master-atlas.dot": render_dot(atlas),
    }
    for rel, text in files.items():
        path = output_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = []
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(output_dir).as_posix()
        data = path.read_bytes()
        manifest.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    receipt = {
        "atlas_version": ATLAS_VERSION,
        "atlas_fingerprint": atlas["atlas_fingerprint"],
        "repository_count": atlas["repository_count"],
        "files": manifest,
        "truth_boundary": atlas["truth_boundary"],
    }
    (output_dir / "MANIFEST.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return atlas
