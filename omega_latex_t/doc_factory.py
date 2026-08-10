"""Ω-DOC-FACTORY-T∞ R1.0 — evidence-bound documentation campaign compiler.

R1.0 composes the already OAK-green R0.3 repository structural scan with
content-addressed AST/import facts, explicit execution observations, conservative
claim candidates, claim↔evidence review links, staleness/delta analysis, quality
metrics, graph projections and deterministic multi-format output.

Nothing in this module promotes scientific truth, semantic equivalence, product
maturity, IP status, merge authority or publication authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
from typing import Mapping, Sequence
from xml.sax.saxutils import escape as xml_escape

from .doc_universe import scan_repository, write_bundle

FACTORY_VERSION = "1.0.0"

OAK_BOUNDARIES = [
    "PATH_PRESENT != FUNCTIONAL_SYSTEM",
    "MODULE_PRESENT != VALIDATED_BEHAVIOR",
    "TEST_PRESENT != TEST_GREEN",
    "WORKFLOW_PRESENT != CURRENT_CI_GREEN",
    "DOC_GENERATED != SCIENTIFIC_TRUTH",
    "CLAIM_DOCUMENTED != CLAIM_PROVEN",
    "SIMULATION != MEASUREMENT",
    "BENCHMARK_WIN != UNIVERSAL_SUPERIORITY",
    "CI_GREEN != SCIENTIFIC_TRUTH",
    "FORMAL_PROOF != PHYSICAL_VALIDATION",
    "MERGED != INDEPENDENT_REPLICATION",
    "FAMILY_CANDIDATE != SEMANTIC_EQUIVALENCE",
    "EXECUTION_RECEIPT != INDEPENDENT_REPLICATION",
    "GRAPH_CONNECTIVITY != CAUSALITY_OR_PROOF",
    "CACHE_HIT != CURRENT_TRUTH",
]

EXECUTION_BOUNDARIES = {
    "test-run": "TEST_RUN_PASS != SCIENTIFIC_TRUTH",
    "workflow-run": "WORKFLOW_GREEN != SCIENTIFIC_TRUTH",
    "benchmark-run": "BENCHMARK_OBSERVATION != UNIVERSAL_SUPERIORITY",
    "schema-validation": "SCHEMA_VALID != DATA_TRUE",
    "build-run": "BUILD_PASS != BEHAVIOR_VALIDATED",
    "package-smoke": "SMOKE_PASS != COMPLETE_CORRECTNESS",
    "formal-proof": "FORMAL_PROOF != PHYSICAL_VALIDATION",
    "measurement": "MEASUREMENT != UNIVERSAL_LAW",
    "simulation": "SIMULATION != MEASUREMENT",
}

CLAIM_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:CLAIM|Claim|claim|AFFIRMATION|Affirmation|affirmation|"
    r"HYPOTHESIS|Hypothesis|hypothesis|CONJECTURE|Conjecture|conjecture)"
    r"\s*:\s*(?P<text>.+?)\s*$"
)
PLACEHOLDER_RE = re.compile(
    r"\b(?:unresolved|unknown|tbd|todo|à\s+résoudre|non\s+résolu)\b",
    re.IGNORECASE,
)


def _json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(x) for x in parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:20]}"


def _safe_rel(root: Path, rel: str) -> Path | None:
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _system_mentions(text: str, system_ids: Sequence[str]) -> list[str]:
    low = text.lower()
    found = []
    for sid in system_ids:
        short = sid.removeprefix("omega_")
        variants = {sid, sid.replace("_", "-"), short, short.replace("_", "-")}
        if any(len(v) >= 4 and v.lower() in low for v in variants):
            found.append(sid)
    return sorted(set(found))


def _module_name(path: str) -> str:
    value = path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")
    return value[:-9] if value.endswith(".__init__") else value


def _resolve_relative(module: str, imported: str) -> str:
    if not imported.startswith("."):
        return imported
    level = len(imported) - len(imported.lstrip("."))
    tail = imported[level:]
    parts = module.split(".")
    base = parts[:-1] if len(parts) > 1 else parts
    if level > 1:
        base = base[: max(0, len(base) - level + 1)]
    if tail:
        base.append(tail)
    return ".".join(x for x in base if x)


def _ast_imports(path: Path, digest: str, cache_dir: Path | None) -> dict:
    cache = cache_dir / "imports-v1" / f"{digest}.json" if cache_dir else None
    if cache and cache.is_file():
        try:
            payload = json.loads(cache.read_text(encoding="utf-8"))
            if payload.get("schema") == "imports-v1":
                return payload["facts"]
        except (OSError, json.JSONDecodeError):
            pass
    facts = {"status": "unreadable", "imports": [], "error": None}
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, UnicodeDecodeError) as exc:
        facts["error"] = type(exc).__name__
    except SyntaxError as exc:
        facts = {"status": "syntax-error", "imports": [], "error": f"line {exc.lineno}: {exc.msg}"}
    else:
        imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * int(node.level or 0) + (node.module or ""))
        facts = {"status": "parsed", "imports": sorted(x for x in imports if x), "error": None}
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(_json({"schema": "imports-v1", "facts": facts}) + "\n", encoding="utf-8")
    return facts


def enrich_imports(root: Path, systems: Sequence[dict], cache_dir: Path | None) -> list[dict]:
    residues = []
    for system in systems:
        for module in system.get("modules", []):
            path = _safe_rel(root, module["path"])
            if path is None or not path.is_file():
                module["imports"] = []
                module["import_parse_status"] = "missing"
                residues.append({"system_id": system["id"], "path": module["path"], "error": "missing"})
                continue
            facts = _ast_imports(path, module["sha256"], cache_dir)
            module["imports"] = facts["imports"]
            module["import_parse_status"] = facts["status"]
            if facts["error"]:
                residues.append({"system_id": system["id"], "path": module["path"], "error": facts["error"]})
    return residues


@dataclass(frozen=True)
class ExecutionReceipt:
    id: str
    kind: str
    system_id: str
    artifact_path: str
    source_sha256: str
    status: str
    observed_at: str
    environment: Mapping
    details: Mapping
    authority: str
    boundary: str
    stale: bool
    stale_reason: str

    def mapping(self) -> dict:
        return asdict(self)


def normalize_execution_receipts(root: Path, payload, system_ids: Sequence[str]) -> list[dict]:
    rows = payload.get("receipts", []) if isinstance(payload, Mapping) else payload
    rows = [] if rows is None else rows
    if not isinstance(rows, list):
        raise ValueError("execution receipts must be a list or {'receipts': [...]} object")
    out = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise ValueError(f"execution receipt {index} must be an object")
        kind = str(raw.get("kind", "")).strip()
        if kind not in EXECUTION_BOUNDARIES:
            raise ValueError(f"unsupported execution receipt kind: {kind!r}")
        sid = str(raw.get("system_id", "")).strip()
        if sid and sid not in system_ids:
            raise ValueError(f"unknown system_id in execution receipt: {sid!r}")
        rel = str(raw.get("artifact_path", "")).strip().replace("\\", "/")
        expected = str(raw.get("source_sha256", "")).strip().lower()
        stale = False
        reason = ""
        if rel and expected:
            path = _safe_rel(root, rel)
            if path is None:
                stale, reason = True, "artifact-path-escapes-root"
            elif not path.is_file():
                stale, reason = True, "artifact-missing"
            elif sha256_file(path) != expected:
                stale, reason = True, "source-hash-mismatch"
        environment = raw.get("environment", {})
        details = raw.get("details", {})
        if not isinstance(environment, Mapping) or not isinstance(details, Mapping):
            raise ValueError("receipt environment/details must be objects")
        status = str(raw.get("status", "unknown")).strip().lower().replace("_", "-") or "unknown"
        observed = str(raw.get("observed_at", "")).strip()
        rid = str(raw.get("id") or stable_id("exec", kind, sid, rel, expected, status, observed, _json(details)))
        out.append(ExecutionReceipt(
            id=rid, kind=kind, system_id=sid, artifact_path=rel, source_sha256=expected,
            status=status, observed_at=observed, environment=dict(environment), details=dict(details),
            authority="observation-only", boundary=EXECUTION_BOUNDARIES[kind], stale=stale, stale_reason=reason,
        ).mapping())
    return sorted(out, key=lambda x: x["id"])


def extract_claims(root: Path, system_ids: Sequence[str]) -> list[dict]:
    sources = set()
    for sid in system_ids:
        base = root / sid
        if base.is_dir():
            sources.update(p for p in base.rglob("*.md") if p.is_file())
    for shared in (root / "docs", root / "canon"):
        if shared.is_dir():
            sources.update(p for p in shared.rglob("*.md") if p.is_file())
    out = []
    for path in sorted(sources):
        try:
            rel = path.relative_to(root).as_posix()
            digest = sha256_file(path)
            direct = rel.split("/", 1)[0] if rel.split("/", 1)[0] in system_ids else ""
            with path.open("r", encoding="utf-8") as fh:
                for line_no, line in enumerate(fh, 1):
                    match = CLAIM_RE.match(line.rstrip("\n"))
                    if not match:
                        continue
                    text = match.group("text").strip()
                    sids = [direct] if direct else _system_mentions(text + " " + rel, system_ids)
                    out.append({
                        "id": stable_id("claim", rel, line_no, text), "text": text,
                        "source_path": rel, "source_line": line_no, "source_sha256": digest,
                        "system_ids": sids, "status": "candidate-unverified",
                        "authority": "documentation-observation", "boundary": "CLAIM_DOCUMENTED != CLAIM_PROVEN",
                    })
        except (OSError, UnicodeDecodeError, ValueError):
            continue
    return sorted(out, key=lambda x: x["id"])


def bind_claims(claims: Sequence[Mapping], systems: Sequence[Mapping], executions: Sequence[Mapping]) -> list[dict]:
    structural = {s["id"]: s.get("receipts", []) for s in systems}
    exec_by_system: dict[str, list[Mapping]] = {}
    for receipt in executions:
        if receipt.get("system_id"):
            exec_by_system.setdefault(receipt["system_id"], []).append(receipt)
    out = []
    for claim in claims:
        for sid in claim.get("system_ids", []):
            for receipt in structural.get(sid, []):
                if receipt.get("kind") not in {"test", "workflow", "benchmark", "schema", "doc"}:
                    continue
                out.append({
                    "id": stable_id("bind", claim["id"], receipt["kind"], receipt["path"]),
                    "claim_id": claim["id"], "system_id": sid,
                    "evidence_kind": f"structural-{receipt['kind']}", "evidence_ref": receipt["path"],
                    "relation": "candidate-support-surface", "support_strength": "unknown",
                    "authority": "review-only", "boundary": "LINKED_ARTIFACT != CLAIM_PROVEN",
                })
            for receipt in exec_by_system.get(sid, []):
                out.append({
                    "id": stable_id("bind", claim["id"], receipt["id"]), "claim_id": claim["id"],
                    "system_id": sid, "evidence_kind": receipt["kind"], "evidence_ref": receipt["id"],
                    "relation": "candidate-observation-link", "support_strength": "unknown",
                    "authority": "review-only", "boundary": receipt["boundary"],
                })
    return sorted(out, key=lambda x: x["id"])


def _placeholder_count(root: Path, receipts: Sequence[Mapping]) -> int:
    total, seen = 0, set()
    for receipt in receipts:
        if receipt.get("kind") != "doc" or receipt.get("path") in seen:
            continue
        seen.add(receipt.get("path"))
        path = _safe_rel(root, str(receipt.get("path", "")))
        if path is None or not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                total += sum(len(PLACEHOLDER_RE.findall(line)) for line in fh)
        except (OSError, UnicodeDecodeError):
            pass
    return total


def compute_quality(root: Path, systems: Sequence[Mapping], claims: Sequence[Mapping], bindings: Sequence[Mapping], executions: Sequence[Mapping]) -> dict:
    claim_count: dict[str, int] = {}
    bound: dict[str, set[str]] = {}
    execs: dict[str, list[Mapping]] = {}
    for c in claims:
        for sid in c.get("system_ids", []):
            claim_count[sid] = claim_count.get(sid, 0) + 1
    for b in bindings:
        bound.setdefault(b["system_id"], set()).add(b["claim_id"])
    for r in executions:
        if r.get("system_id"):
            execs.setdefault(r["system_id"], []).append(r)
    rows = []
    for system in systems:
        sid, m = system["id"], system["metrics"]
        symbols = sum(len(mod.get("public_symbols", [])) for mod in system.get("modules", []))
        documented = sum(1 for mod in system.get("modules", []) for s in mod.get("public_symbols", []) if s.get("doc"))
        categories = [m.get(k, 0) for k in (
            "test_candidate_count", "workflow_candidate_count", "schema_candidate_count",
            "doc_candidate_count", "example_candidate_count", "benchmark_candidate_count",
        )]
        erows = execs.get(sid, [])
        stale = sum(bool(x.get("stale")) for x in erows)
        cc, bc = claim_count.get(sid, 0), len(bound.get(sid, set()))
        rows.append({
            "system_id": sid, "api_doc_ratio": round(documented / symbols, 6) if symbols else None,
            "structural_evidence_category_ratio": round(sum(int(x) > 0 for x in categories) / len(categories), 6),
            "execution_receipt_count": len(erows), "fresh_execution_receipt_count": len(erows) - stale,
            "stale_execution_receipt_count": stale, "claim_candidate_count": cc,
            "claim_with_binding_count": bc, "claim_binding_ratio": round(bc / cc, 6) if cc else None,
            "placeholder_count": _placeholder_count(root, system.get("receipts", [])),
            "boundary": "QUALITY_SCORE != SCIENTIFIC_TRUTH",
        })
    return {
        "aggregate": {
            "system_count": len(rows), "claim_candidate_count": len(claims),
            "claim_binding_count": len(bindings), "execution_receipt_count": len(executions),
            "stale_execution_receipt_count": sum(r["stale_execution_receipt_count"] for r in rows),
            "placeholder_count": sum(r["placeholder_count"] for r in rows),
            "boundary": "DOCUMENTATION_COVERAGE != CLAIM_VALIDITY",
        },
        "systems": rows,
    }


def attach_fingerprints(report: dict) -> None:
    claims: dict[str, list[str]] = {}
    execs: dict[str, list[str]] = {}
    for c in report["claims"]:
        for sid in c.get("system_ids", []):
            claims.setdefault(sid, []).append(c["id"])
    for r in report["execution_receipts"]:
        if r.get("system_id"):
            execs.setdefault(r["system_id"], []).append(r["id"])
    for system in report["systems"]:
        sid = system["id"]
        payload = {
            "id": sid, "statuses": system["statuses"],
            "modules": [(m["path"], m["sha256"], m.get("imports", []), m.get("public_symbols", [])) for m in system.get("modules", [])],
            "receipts": [(r.get("kind"), r.get("path"), r.get("sha256")) for r in system.get("receipts", [])],
            "claims": sorted(claims.get(sid, [])), "executions": sorted(execs.get(sid, [])),
        }
        system["fingerprint"] = hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def compare_reports(before: Mapping | None, after: Mapping) -> dict:
    if not before:
        return {
            "baseline": "none", "added_systems": sorted(s["id"] for s in after["systems"]),
            "removed_systems": [], "changed_systems": [], "unchanged_systems": [],
            "invalidated_previous_documentation": [], "boundary": "DELTA != SEMANTIC_IMPACT_PROOF",
        }
    b = {s["id"]: s for s in before.get("systems", [])}
    a = {s["id"]: s for s in after.get("systems", [])}
    added, removed = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    changed, unchanged = [], []
    for sid in sorted(set(a) & set(b)):
        (changed if a[sid].get("fingerprint") != b[sid].get("fingerprint") else unchanged).append(sid)
    return {
        "baseline": str(before.get("source_commit", "")), "added_systems": added,
        "removed_systems": removed, "changed_systems": changed, "unchanged_systems": unchanged,
        "invalidated_previous_documentation": sorted(set(removed + changed)),
        "boundary": "DELTA != SEMANTIC_IMPACT_PROOF",
    }


def build_graph(report: Mapping) -> dict:
    nodes, edges, module_map = [], [], {}
    def node(i, kind, label, **attrs): nodes.append({"id": i, "kind": kind, "label": label, **attrs})
    def edge(a, b, relation, **attrs): edges.append({"source": a, "target": b, "relation": relation, **attrs})
    for system in report["systems"]:
        sid = f"system:{system['id']}"
        node(sid, "system", system["id"], fingerprint=system.get("fingerprint", ""))
        for module in system.get("modules", []):
            mid = f"module:{module['path']}"
            module_map[_module_name(module["path"])] = mid
            node(mid, "module", module["path"], sha256=module["sha256"]); edge(sid, mid, "contains")
            for symbol in module.get("public_symbols", []):
                yid = stable_id("symbol", module["path"], symbol["name"], symbol["line"])
                node(yid, "symbol", symbol["name"], symbol_kind=symbol["kind"]); edge(mid, yid, "declares")
    for system in report["systems"]:
        for module in system.get("modules", []):
            source, source_name = f"module:{module['path']}", _module_name(module["path"])
            for imported in module.get("imports", []):
                resolved = _resolve_relative(source_name, imported)
                target = module_map.get(resolved)
                parts = resolved.split(".")
                while target is None and len(parts) > 1:
                    parts.pop(); target = module_map.get(".".join(parts))
                if target and target != source:
                    edge(source, target, "imports", boundary="IMPORT_EDGE != RUNTIME_DEPENDENCY_PROOF")
    for receipt in report["execution_receipts"]:
        rid = f"execution:{receipt['id']}"; node(rid, "execution-receipt", receipt["kind"], status=receipt["status"], stale=receipt["stale"])
        if receipt.get("system_id"): edge(f"system:{receipt['system_id']}", rid, "has-execution-observation", boundary=receipt["boundary"])
    for claim in report["claims"]:
        cid = f"claim:{claim['id']}"; node(cid, "claim-candidate", claim["text"], status=claim["status"])
        for sid in claim.get("system_ids", []): edge(f"system:{sid}", cid, "mentions-claim", boundary=claim["boundary"])
    for binding in report["claim_evidence_bindings"]:
        target = f"execution:{binding['evidence_ref']}" if binding["evidence_kind"] in EXECUTION_BOUNDARIES else stable_id("evidence", binding["evidence_kind"], binding["evidence_ref"])
        edge(f"claim:{binding['claim_id']}", target, binding["relation"], support_strength="unknown", boundary=binding["boundary"])
    existing = {n["id"] for n in nodes}
    for missing in sorted({e["target"] for e in edges} - existing): node(missing, "evidence-reference", missing)
    return {"schema_version": FACTORY_VERSION, "nodes": sorted(nodes, key=lambda n: n["id"]), "edges": sorted(edges, key=lambda e: (e["source"], e["target"], e["relation"])), "boundary": "GRAPH_CONNECTIVITY != CAUSALITY_OR_PROOF"}


def render_dot(graph: Mapping) -> str:
    esc = lambda x: str(x).replace("\\", "\\\\").replace('"', '\\"')
    lines = ["digraph omega_doc_factory {", '  rankdir="LR";']
    for n in graph["nodes"]: lines.append(f'  "{esc(n["id"])}" [label="{esc(n["label"])}\\n[{esc(n["kind"])}]"];')
    for e in graph["edges"]: lines.append(f'  "{esc(e["source"])}" -> "{esc(e["target"])}" [label="{esc(e["relation"])}"];')
    return "\n".join(lines + ["}"]) + "\n"


def render_graphml(graph: Mapping) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">', '  <graph id="omega-doc-factory" edgedefault="directed">']
    for n in graph["nodes"]: lines += [f'    <node id="{xml_escape(str(n["id"]))}">', f'      <data key="kind">{xml_escape(str(n["kind"]))}</data>', f'      <data key="label">{xml_escape(str(n["label"]))}</data>', '    </node>']
    for i, e in enumerate(graph["edges"]): lines += [f'    <edge id="e{i}" source="{xml_escape(str(e["source"]))}" target="{xml_escape(str(e["target"]))}">', f'      <data key="relation">{xml_escape(str(e["relation"]))}</data>', '    </edge>']
    return "\n".join(lines + ['  </graph>', '</graphml>']) + "\n"


def render_atlas(report: Mapping) -> str:
    q = {r["system_id"]: r for r in report["quality"]["systems"]}
    lines = ["# Ω-DOC-FACTORY-T∞ R1.0 — Master Atlas", "", f"- source commit: `{report.get('source_commit','')}`", f"- systems: **{report['system_count']}**", f"- claim candidates: **{len(report['claims'])}**", f"- execution receipts: **{len(report['execution_receipts'])}**", f"- graph nodes/edges: **{len(report['graph']['nodes'])}/{len(report['graph']['edges'])}**", "", "| system | evidence | execution | claims | placeholders |", "|---|---:|---:|---:|---:|"]
    for s in report["systems"]:
        row = q[s["id"]]; lines.append(f"| `{s['id']}` | {row['structural_evidence_category_ratio']:.3f} | {row['execution_receipt_count']} | {row['claim_candidate_count']} | {row['placeholder_count']} |")
    lines += ["", "## Delta", "", f"- added: {len(report['delta']['added_systems'])}", f"- changed: {len(report['delta']['changed_systems'])}", f"- removed: {len(report['delta']['removed_systems'])}", f"- unchanged: {len(report['delta']['unchanged_systems'])}", "", "## OAK boundaries", ""] + [f"- `{b}`" for b in report["oak_boundaries"]]
    return "\n".join(lines) + "\n"


def render_latex(report: Mapping) -> str:
    esc = lambda x: str(x).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    lines = [r"\documentclass{article}", r"\usepackage[T1]{fontenc}", r"\usepackage{longtable}", r"\begin{document}", r"\section*{$\Omega$-DOC-FACTORY-T R1.0 Master Atlas}", f"Source commit: \\texttt{{{esc(report.get('source_commit',''))}}}\\\\", f"Systems: {report['system_count']}\\\\", r"\begin{longtable}{p{0.5\linewidth}rrr}", r"System & Modules & Symbols & Tests\\\hline"]
    for s in report["systems"]:
        m=s["metrics"]; lines.append(f"\\texttt{{{esc(s['id'])}}} & {m['python_module_count']} & {m['public_symbol_count']} & {m['test_candidate_count']}\\\\")
    return "\n".join(lines + [r"\end{longtable}", r"\paragraph{Boundary.} Generated documentation and CI observations do not certify scientific truth.", r"\end{document}"]) + "\n"


def build_factory_report(root: str | Path, *, source_commit: str = "", declared_statuses: Mapping[str,str] | None = None, execution_receipts_payload=None, previous_report: Mapping | None = None, cache_dir: str | Path | None = ".omega-doc-cache") -> dict:
    root = Path(root).resolve(); cache = Path(cache_dir).resolve() if cache_dir else None
    structural = scan_repository(root, source_commit=source_commit, declared_statuses=declared_statuses)
    systems = structural["systems"]; system_ids = [s["id"] for s in systems]
    import_residues = enrich_imports(root, systems, cache)
    executions = normalize_execution_receipts(root, execution_receipts_payload or [], system_ids)
    claims = extract_claims(root, system_ids); bindings = bind_claims(claims, systems, executions)
    for system in systems:
        erows = [r for r in executions if r.get("system_id") == system["id"]]
        system["statuses"]["implementation_status"] = "code-present" if system.get("modules") else "path-only-or-non-python"
        system["statuses"]["reproducibility_status"] = "fresh-execution-observations" if any(not r["stale"] for r in erows) else ("stale-execution-observations" if erows else "execution-unresolved")
        system["statuses"]["product_status"] = "unknown"; system["statuses"]["ip_status"] = "unknown"
    report = {**structural, "factory_version": FACTORY_VERSION, "import_residues": import_residues, "execution_receipts": executions, "claims": claims, "claim_evidence_bindings": bindings, "oak_boundaries": list(OAK_BOUNDARIES)}
    report["quality"] = compute_quality(root, systems, claims, bindings, executions); attach_fingerprints(report)
    report["delta"] = compare_reports(previous_report, report); report["graph"] = build_graph(report)
    report["campaign_fingerprint"] = hashlib.sha256(_json({"factory_version": FACTORY_VERSION, "source_commit": source_commit, "systems": [(s["id"], s["fingerprint"]) for s in systems], "claims": [c["id"] for c in claims], "executions": [r["id"] for r in executions]}).encode("utf-8")).hexdigest()
    return report


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")


def write_factory_bundle(report: Mapping, output_dir: str | Path) -> dict:
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    structural = {k: report[k] for k in ("schema_version","source_root","source_commit","system_count","systems","family_candidates","family_boundary","truth_boundary") if k in report}
    write_bundle(structural, out / "depths")
    files=[]
    for rel,payload in (("factory-report.json",report),("quality.json",report["quality"]),("delta.json",report["delta"]),("graph/evidence-graph.json",report["graph"])):
        path=out/rel; _write_json(path,payload); files.append(path)
    for rel,rows in (("claims.jsonl",report["claims"]),("claim-evidence-bindings.jsonl",report["claim_evidence_bindings"]),("execution-receipts.jsonl",report["execution_receipts"])):
        path=out/rel; path.write_text("".join(_json(r)+"\n" for r in rows),encoding="utf-8"); files.append(path)
    atlas=out/"MASTER_DOC_ATLAS.md"; atlas.write_text(render_atlas(report),encoding="utf-8"); files.append(atlas)
    dot=out/"graph/evidence-graph.dot"; dot.parent.mkdir(parents=True,exist_ok=True); dot.write_text(render_dot(report["graph"]),encoding="utf-8"); files.append(dot)
    graphml=out/"graph/evidence-graph.graphml"; graphml.write_text(render_graphml(report["graph"]),encoding="utf-8"); files.append(graphml)
    tex=out/"latex/MASTER_DOC_ATLAS.tex"; tex.parent.mkdir(parents=True,exist_ok=True); tex.write_text(render_latex(report),encoding="utf-8"); files.append(tex)
    qcsv=out/"quality.csv"; rows=report["quality"]["systems"]; fields=list(rows[0]) if rows else ["system_id"]
    with qcsv.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    files.append(qcsv); files.extend(p for p in (out/"depths").rglob("*") if p.is_file()); files=sorted(set(files))
    manifest={"factory_version":FACTORY_VERSION,"source_commit":report.get("source_commit",""),"campaign_fingerprint":report["campaign_fingerprint"],"system_count":report["system_count"],"files":[{"path":p.relative_to(out).as_posix(),"sha256":sha256_file(p),"bytes":p.stat().st_size} for p in files],"boundaries":report["oak_boundaries"]}
    _write_json(out/"MANIFEST.json",manifest); return manifest
