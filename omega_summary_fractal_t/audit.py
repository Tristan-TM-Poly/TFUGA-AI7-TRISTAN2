from __future__ import annotations

import re
from collections import Counter
from .models import SummaryNode
TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)


def health_dashboard(nodes: list[SummaryNode]) -> dict[str, object]:
    systems = [n for n in nodes if n.kind == "system"]; metrics = Counter()
    for node in systems:
        metrics["systems"] += 1
        for key in ("implemented", "tested", "documented", "schema_backed"):
            if node.metrics.get(key): metrics[key] += 1
    total = max(1, metrics["systems"])
    return {"systems": metrics["systems"], "implemented_ratio": round(metrics["implemented"] / total, 4), "tested_ratio": round(metrics["tested"] / total, 4), "documented_ratio": round(metrics["documented"] / total, 4), "schema_backed_ratio": round(metrics["schema_backed"] / total, 4), "oak": {"truth": "evidence-bound structural inventory; not scientific validation", "code": metrics["implemented"], "test": metrics["tested"], "product": "not inferred from repository structure alone", "ip": "not inferred; requires explicit IPGate review", "github": metrics["systems"], "revenue": "not inferred from code presence", "risk": "summary claims are bounded to observable repository evidence", "next_action": "prioritize implemented but untested systems, then documented but unimplemented systems"}}


def gap_analysis(nodes: list[SummaryNode]) -> list[dict[str, object]]:
    gaps = []
    for node in nodes:
        if node.kind != "system": continue
        m = node.metrics
        if m.get("implemented") and not m.get("tested"): gaps.append({"system": node.path, "kind": "implemented_without_tests", "priority": 1, "action": f"Add focused tests for {node.path}"})
        elif m.get("documented") and not m.get("implemented"): gaps.append({"system": node.path, "kind": "documented_without_code", "priority": 2, "action": f"Implement or explicitly mark {node.path} as concept-only"})
        if m.get("implemented") and not m.get("schema_backed"): gaps.append({"system": node.path, "kind": "implemented_without_schema", "priority": 3, "action": f"Add machine-readable contracts for {node.path} where appropriate"})
    return sorted(gaps, key=lambda x: (int(x["priority"]), str(x["system"]), str(x["kind"])))


def _tokens(node: SummaryNode) -> set[str]: return set(TOKEN_RE.findall((node.title + " " + node.one_line + " " + node.path).casefold()))


def duplicate_candidates(nodes: list[SummaryNode], threshold: float = 0.72) -> list[dict[str, object]]:
    systems = sorted((n for n in nodes if n.kind == "system"), key=lambda n: n.path); out = []
    for i, left in enumerate(systems):
        lt = _tokens(left)
        for right in systems[i + 1:]:
            rt = _tokens(right); union = lt | rt
            if not union: continue
            score = len(lt & rt) / len(union)
            if score >= threshold: out.append({"left": left.path, "right": right.path, "similarity": round(score, 4), "classification": "near-duplicate-candidate", "status": "review_required"})
    return sorted(out, key=lambda x: (-float(x["similarity"]), str(x["left"]), str(x["right"])))
