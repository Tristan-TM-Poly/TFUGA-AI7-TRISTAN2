"""Ω-DOC-COMPILER-T R0.3 — evidence-bound repository documentation compiler.

Conservative contracts:
- path presence is a structural fact, not proof of behavior;
- test/workflow presence is not equivalent to a green run;
- generated documentation never upgrades scientific truth status.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import hashlib
import json
import re
from typing import Iterable, Mapping, Sequence

SCHEMA_VERSION = "0.3.0"
SYSTEM_PREFIX = "omega_"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_walk(root: Path) -> Iterable[Path]:
    excluded = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for path in sorted(root.rglob("*")):
        if any(part in excluded for part in path.relative_to(root).parts):
            continue
        yield path


def discover_systems(root: str | Path) -> list[str]:
    root = Path(root).resolve()
    return sorted(p.name for p in root.iterdir() if p.is_dir() and p.name.startswith(SYSTEM_PREFIX))


def _family_id(system_id: str) -> str:
    """Lexical family candidate only; never semantic equivalence."""
    value = re.sub(r"_p\d+$", "", system_id)
    value = re.sub(r"_kernel$", "", value)
    value = re.sub(r"_n_t$", "_t", value)
    return value[:-2] if value.endswith("_t") else value


def _python_symbols(path: Path) -> list[dict]:
    text = _read_text(path)
    if not text:
        return []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            item = {"name": node.name, "kind": kind, "line": node.lineno}
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                item["args"] = [a.arg for a in node.args.args]
            doc = ast.get_docstring(node)
            if doc:
                item["doc"] = doc.splitlines()[0][:240]
            out.append(item)
    return out


@dataclass(frozen=True)
class Receipt:
    kind: str
    path: str
    sha256: str
    relation: str
    status: str = "present"
    boundary: str = ""

    def mapping(self) -> dict:
        return asdict(self)


def _path_mentions(path: Path, root: Path, system_id: str) -> bool:
    rel = _rel(path, root).lower()
    short = system_id.lower().removeprefix("omega_")
    alt = short.removesuffix("_t")
    variants = {system_id.lower(), short, short.replace("_", "-"), alt, alt.replace("_", "-")}
    return any(len(v) >= 4 and v in rel for v in variants)


def _candidate_files(root: Path, system_id: str, system_path: Path, inventory: Sequence[Path]) -> dict[str, list[Path]]:
    system_files = [p for p in _safe_walk(system_path) if p.is_file()]
    def select(part: str) -> list[Path]:
        return [p for p in inventory if part in p.parts and _path_mentions(p, root, system_id)]
    workflows = [p for p in inventory if ".github" in p.parts and "workflows" in p.parts and _path_mentions(p, root, system_id)]
    return {
        "system": system_files,
        "tests": select("tests"),
        "workflows": workflows,
        "schemas": select("schemas"),
        "docs": select("docs"),
        "examples": select("examples"),
        "benchmarks": select("benchmarks"),
    }


def scan_system(root: str | Path, system_id: str, declared_status: str | None = None, *, inventory: Sequence[Path] | None = None) -> dict:
    root = Path(root).resolve()
    system_path = (root / system_id).resolve()
    if not system_path.is_dir() or system_path.parent != root:
        raise ValueError(f"invalid root system directory: {system_id!r}")
    all_files = list(inventory) if inventory is not None else [p for p in _safe_walk(root) if p.is_file()]
    groups = _candidate_files(root, system_id, system_path, all_files)
    py_files = [p for p in groups["system"] if p.suffix == ".py"]
    modules = [{"path": _rel(path, root), "sha256": _sha256(path), "public_symbols": _python_symbols(path)} for path in py_files]

    receipts: list[Receipt] = []
    specs = {
        "tests": ("test", "tests", "TEST_PRESENT != TEST_GREEN"),
        "workflows": ("workflow", "ci-config", "WORKFLOW_PRESENT != CURRENT_CI_GREEN"),
        "schemas": ("schema", "schema", "SCHEMA_PRESENT != DATA_VALIDATED"),
        "docs": ("doc", "documents", "DOC_PRESENT != CLAIM_PROVEN"),
        "examples": ("example", "example", "EXAMPLE_PRESENT != GENERAL_VALIDITY"),
        "benchmarks": ("benchmark", "benchmarks", "BENCHMARK_PRESENT != SUPERIORITY_PROVEN"),
    }
    for group, (kind, relation, boundary) in specs.items():
        for path in groups[group]:
            receipts.append(Receipt(kind=kind, path=_rel(path, root), sha256=_sha256(path), relation=relation, boundary=boundary))

    evidence_count = sum(1 for r in receipts if r.kind in {"test", "workflow", "benchmark"})
    return {
        "id": system_id,
        "family_candidate": _family_id(system_id),
        "path": f"{system_id}/",
        "statuses": {
            "declared_system_status": declared_status or "unknown",
            "documentation_status": "resolved-structural" if modules else "path-only",
            "evidence_status": "structural-evidence-present" if evidence_count else "unresolved",
            "oak_review_status": "review",
        },
        "metrics": {
            "file_count": len(groups["system"]),
            "python_module_count": len(py_files),
            "public_symbol_count": sum(len(m["public_symbols"]) for m in modules),
            "test_candidate_count": len(groups["tests"]),
            "workflow_candidate_count": len(groups["workflows"]),
            "schema_candidate_count": len(groups["schemas"]),
            "doc_candidate_count": len(groups["docs"]),
            "example_candidate_count": len(groups["examples"]),
            "benchmark_candidate_count": len(groups["benchmarks"]),
        },
        "modules": modules,
        "receipts": [r.mapping() for r in receipts],
        "oak_boundaries": [
            "PATH_PRESENT != FUNCTIONAL_SYSTEM",
            "MODULE_PRESENT != VALIDATED_BEHAVIOR",
            "TEST_PRESENT != TEST_GREEN",
            "WORKFLOW_PRESENT != CURRENT_CI_GREEN",
            "DOC_GENERATED != SCIENTIFIC_TRUTH",
            "CLAIM_DOCUMENTED != CLAIM_PROVEN",
            "SIMULATION != MEASUREMENT",
        ],
    }


def scan_repository(root: str | Path, *, source_commit: str = "", declared_statuses: Mapping[str, str] | None = None) -> dict:
    root = Path(root).resolve()
    statuses = dict(declared_statuses or {})
    inventory = [p for p in _safe_walk(root) if p.is_file()]
    systems = [scan_system(root, sid, declared_status=statuses.get(sid), inventory=inventory) for sid in discover_systems(root)]
    families: dict[str, list[str]] = {}
    for system in systems:
        families.setdefault(system["family_candidate"], []).append(system["id"])
    families = {k: v for k, v in families.items() if len(v) > 1}
    return {
        "schema_version": SCHEMA_VERSION,
        "source_root": str(root),
        "source_commit": source_commit,
        "system_count": len(systems),
        "systems": systems,
        "family_candidates": families,
        "family_boundary": "FAMILY_CANDIDATE != SEMANTIC_EQUIVALENCE",
        "truth_boundary": "repository-derived documentation is evidence about repository structure, not scientific certification",
    }


def render_depth(system: Mapping, depth: int) -> str:
    if depth not in range(6):
        raise ValueError("depth must be 0..5")
    sid = str(system["id"])
    statuses, metrics = system["statuses"], system["metrics"]
    lines = [f"# D{depth} — {sid}", ""]
    if depth == 0:
        lines += [f"- path: `{system['path']}`", f"- declared status: `{statuses['declared_system_status']}`", f"- documentation: `{statuses['documentation_status']}`", f"- evidence: `{statuses['evidence_status']}`", f"- files: {metrics['file_count']}; Python modules: {metrics['python_module_count']}; public symbols: {metrics['public_symbol_count']}"]
    elif depth == 1:
        lines += ["## Structural identity", "", f"`{sid}` contains {metrics['file_count']} observed files and {metrics['python_module_count']} Python modules.", "", "## Candidate evidence surfaces", f"- tests: {metrics['test_candidate_count']}", f"- workflows: {metrics['workflow_candidate_count']}", f"- schemas: {metrics['schema_candidate_count']}", f"- docs: {metrics['doc_candidate_count']}"]
    elif depth == 2:
        lines += ["## Modules", ""] + ([f"- `{m['path']}` — {len(m['public_symbols'])} public symbols — sha256 `{m['sha256'][:16]}…`" for m in system["modules"]] or ["- no Python module resolved"])
    elif depth == 3:
        lines += ["## Public API extracted from AST", ""]
        found = False
        for module in system["modules"]:
            if not module["public_symbols"]:
                continue
            found = True
            lines.append(f"### `{module['path']}`")
            for symbol in module["public_symbols"]:
                args = ", ".join(symbol.get("args", []))
                suffix = f"({args})" if symbol["kind"] == "function" else ""
                lines.append(f"- `{symbol['name']}{suffix}` — {symbol['kind']} — line {symbol['line']}")
            lines.append("")
        if not found:
            lines.append("- no public symbol resolved")
    elif depth == 4:
        lines += ["## Structural evidence receipts", "", "| kind | path | relation | boundary |", "|---|---|---|---|"]
        for receipt in system["receipts"]:
            lines.append(f"| {receipt['kind']} | `{receipt['path']}` | {receipt['relation']} | `{receipt['boundary']}` |")
        if not system["receipts"]:
            lines.append("| unresolved | — | — | `NO_RECEIPT != NO_EVIDENCE` |")
    else:
        lines += ["## OAK", "", f"- review status: `{statuses['oak_review_status']}`", f"- family candidate: `{system['family_candidate']}`", "", "## Boundaries"] + [f"- `{b}`" for b in system["oak_boundaries"]] + ["", "No status is promoted by documentation generation."]
    return "\n".join(lines).rstrip() + "\n"


def write_bundle(report: Mapping, output_dir: str | Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    universe_path = out / "doc-universe.json"
    universe_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = [universe_path]
    for system in report["systems"]:
        sysdir = out / "systems" / str(system["id"])
        sysdir.mkdir(parents=True, exist_ok=True)
        for depth in range(6):
            path = sysdir / f"D{depth}.md"
            path.write_text(render_depth(system, depth), encoding="utf-8")
            files.append(path)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_commit": report.get("source_commit", ""),
        "system_count": report["system_count"],
        "files": [{"path": p.relative_to(out).as_posix(), "sha256": _sha256(p), "bytes": p.stat().st_size} for p in sorted(files)],
        "truth_boundary": report["truth_boundary"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
