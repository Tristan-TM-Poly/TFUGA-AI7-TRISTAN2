"""Omega-MGHFM-TGNT prototype engine.

Dependency-free executable sketch of:

    X_next = EXP(OAK(TGNT(J(CVCD(LOG(HGFM(X)))))))
    J = JKD o YY3 o Tristan^2

The engine treats inputs as trace strings, builds a tiny HGFM-like structure,
extracts LOG layers, performs compressed/virtual CVCD scoring, applies JKD/YY3,
classifies with OAK, and decompresses into candidate outputs.

It is a research tooling prototype, not a theorem prover.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


OAK_STATUSES: Sequence[str] = ("observed", "anchored", "known", "speculative", "refuted", "noise")


@dataclass(frozen=True)
class OmegaNode:
    id: str
    value: str
    kind: str
    fertility: float
    oak_status: str


@dataclass(frozen=True)
class OmegaHyperedge:
    id: str
    nodes: List[str]
    relation: str
    fertility: float
    oak_status: str


@dataclass(frozen=True)
class OmegaCycle:
    input_count: int
    nodes: List[OmegaNode]
    hyperedges: List[OmegaHyperedge]
    log_layers: Dict[str, object]
    cvcd: Dict[str, object]
    jkd: Dict[str, object]
    yy3: Dict[str, object]
    tristan2: Dict[str, object]
    tgnt: Dict[str, object]
    oak: Dict[str, object]
    exp: Dict[str, object]
    negative_memory: List[Dict[str, object]]


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _unit(text: str, field: str) -> float:
    return (_hash_int(f"{text}|{field}") % 1000) / 999


def _oak_status(score: float, risk: float) -> str:
    if risk > 0.85:
        return "noise"
    if score > 0.82:
        return "known"
    if score > 0.65:
        return "observed"
    if score > 0.48:
        return "speculative"
    if score > 0.30:
        return "anchored"
    return "refuted"


def hgfm(inputs: Iterable[str]) -> Dict[str, object]:
    nodes: List[OmegaNode] = []
    for index, value in enumerate(inputs):
        normalized = value.strip()
        if not normalized:
            continue
        fertility = round(10 * (0.45 * _unit(normalized, "utility") + 0.35 * _unit(normalized, "generativity") + 0.20 * _unit(normalized, "compression")), 3)
        risk = _unit(normalized, "risk")
        oak = _oak_status(fertility / 10, risk)
        nodes.append(
            OmegaNode(
                id=f"v{index:03d}-{_hash_int(normalized) % 10000:04d}",
                value=normalized,
                kind="trace",
                fertility=fertility,
                oak_status=oak,
            )
        )

    hyperedges: List[OmegaHyperedge] = []
    for i, left in enumerate(nodes):
        for right in nodes[i + 1 :]:
            shared = set(left.value.lower().split()) & set(right.value.lower().split())
            if shared or left.kind == right.kind:
                relation = "shared_terms" if shared else "same_kind"
                seed = f"{left.id}|{right.id}|{relation}"
                fertility = round((left.fertility + right.fertility) / 2 + 2 * _unit(seed, "bridge"), 3)
                oak = _oak_status(min(1.0, fertility / 12), _unit(seed, "risk"))
                hyperedges.append(
                    OmegaHyperedge(
                        id=f"e{i:03d}-{_hash_int(seed) % 10000:04d}",
                        nodes=[left.id, right.id],
                        relation=relation,
                        fertility=fertility,
                        oak_status=oak,
                    )
                )
    return {"nodes": nodes, "hyperedges": hyperedges}


def log_tower(nodes: Sequence[OmegaNode], hyperedges: Sequence[OmegaHyperedge]) -> Dict[str, object]:
    raw_data = [node.value for node in nodes]
    local_patterns = sorted({word for node in nodes for word in node.value.lower().split() if len(word) > 3})[:32]
    invariants = {
        "node_count": len(nodes),
        "hyperedge_count": len(hyperedges),
        "oak_statuses": sorted({node.oak_status for node in nodes} | {edge.oak_status for edge in hyperedges}),
    }
    generative_rules = [
        "same signature terms create candidate hyperedges",
        "high fertility and non-refuted OAK status promote expansion",
        "low fertility or high risk enters negative memory",
    ]
    meta_rules = [
        "LOG must preserve reconstructive/generative power",
        "EXP must be filtered by OAK",
        "JKD chooses minimum high-impact actions",
    ]
    signature = {
        "top_terms": local_patterns[:8],
        "mean_node_fertility": round(sum(node.fertility for node in nodes) / max(1, len(nodes)), 3),
        "mean_edge_fertility": round(sum(edge.fertility for edge in hyperedges) / max(1, len(hyperedges)), 3),
    }
    return {
        "L0_raw_data": raw_data,
        "L1_local_patterns": local_patterns,
        "L2_invariants": invariants,
        "L3_generative_rules": generative_rules,
        "L4_meta_rules": meta_rules,
        "Lomega_minimal_fertile_signature": signature,
    }


def cvcd(log_layers: Dict[str, object]) -> Dict[str, object]:
    signature = log_layers["Lomega_minimal_fertile_signature"]
    virtual_prediction = {
        "expected_generators": max(1, int(signature["mean_node_fertility"] // 2)),
        "expected_hyperedges": max(1, int(signature["mean_edge_fertility"] // 2)),
        "decompress_windows": signature["top_terms"][:4],
    }
    return {
        "compressed_signature": signature,
        "virtual_prediction": virtual_prediction,
        "controlled_decompression": virtual_prediction["decompress_windows"],
        "principle": "do not compute fully what a signature can decide locally",
    }


def apply_jkd(cvcd_packet: Dict[str, object]) -> Dict[str, object]:
    windows = cvcd_packet["controlled_decompression"]
    actions = [
        {"action": f"decompress:{window}", "impact": round(5 + 5 * _unit(window, "impact"), 3), "cost": round(1 + 4 * _unit(window, "cost"), 3)}
        for window in windows
    ]
    for action in actions:
        action["jkd_score"] = round(action["impact"] / (action["cost"] + 1), 3)
    best = sorted(actions, key=lambda item: item["jkd_score"], reverse=True)[:3]
    return {"candidate_actions": actions, "top_jkd_actions": best}


def apply_yy3(jkd_packet: Dict[str, object]) -> Dict[str, object]:
    top_actions = jkd_packet["top_jkd_actions"]
    return {
        "Y_minus": [f"remove_or_compress_low_yield_around:{action['action']}" for action in top_actions],
        "Y_plus": [f"generate_variants_from:{action['action']}" for action in top_actions],
        "Y_cross": [f"prototype_or_codex:{action['action']}" for action in top_actions],
    }


def apply_tristan2(yy3_packet: Dict[str, object]) -> Dict[str, object]:
    generators = [
        f"generator_from::{item}" for stream in ("Y_plus", "Y_cross") for item in yy3_packet[stream]
    ]
    return {
        "derived_generators": generators,
        "self_improvement_rule": "Improve generator using outputs plus negative memory under OAK",
    }


def apply_tgnt(tristan2_packet: Dict[str, object]) -> Dict[str, object]:
    generators = tristan2_packet["derived_generators"]
    return {
        "turing": [f"algorithmize:{generator}" for generator in generators],
        "godel": ["detect_missing_axioms", "mark_speculative_boundaries", "require_meta_level_when_self_reference_detected"],
        "von_neumann": ["store_program_memory", "emit_runner", "emit_codex", "emit_state"],
        "tristan": ["fertile_compression", "HGFM_expansion", "OAK_filter", "negative_memory_update"],
    }


def apply_oak(nodes: Sequence[OmegaNode], hyperedges: Sequence[OmegaHyperedge], tgnt_packet: Dict[str, object]) -> Dict[str, object]:
    statuses = {status: 0 for status in OAK_STATUSES}
    for node in nodes:
        statuses[node.oak_status] += 1
    for edge in hyperedges:
        statuses[edge.oak_status] += 1
    promoted = statuses["known"] + statuses["observed"] + statuses["anchored"]
    quarantined = statuses["speculative"] + statuses["refuted"] + statuses["noise"]
    return {
        "statuses": statuses,
        "promoted_count": promoted,
        "quarantined_count": quarantined,
        "tgnt_checks": tgnt_packet,
        "rule": "no motif becomes truth automatically",
    }


def exp_tower(oak_packet: Dict[str, object], tristan2_packet: Dict[str, object]) -> Dict[str, object]:
    generators = tristan2_packet["derived_generators"]
    return {
        "E0_instances": generators[:4],
        "E1_families": [f"family::{generator}" for generator in generators[:4]],
        "E2_hypergraphs": ["HGFM_expansion_candidate"],
        "E3_theories": ["Omega-MGHFM-TGNT candidate theory"],
        "E4_meta_theories": ["Generator of verified generators"],
        "oak_gate": oak_packet["statuses"],
    }


def run_cycle(inputs: Sequence[str]) -> Dict[str, object]:
    graph = hgfm(inputs)
    nodes: List[OmegaNode] = graph["nodes"]  # type: ignore[assignment]
    hyperedges: List[OmegaHyperedge] = graph["hyperedges"]  # type: ignore[assignment]
    logs = log_tower(nodes, hyperedges)
    cvcd_packet = cvcd(logs)
    jkd_packet = apply_jkd(cvcd_packet)
    yy3_packet = apply_yy3(jkd_packet)
    tristan2_packet = apply_tristan2(yy3_packet)
    tgnt_packet = apply_tgnt(tristan2_packet)
    oak_packet = apply_oak(nodes, hyperedges, tgnt_packet)
    exp_packet = exp_tower(oak_packet, tristan2_packet)
    negative_memory = [
        {"type": "node", "id": node.id, "value": node.value, "reason": node.oak_status}
        for node in nodes
        if node.oak_status in {"refuted", "noise"}
    ]
    cycle = OmegaCycle(
        input_count=len(inputs),
        nodes=nodes,
        hyperedges=hyperedges,
        log_layers=logs,
        cvcd=cvcd_packet,
        jkd=jkd_packet,
        yy3=yy3_packet,
        tristan2=tristan2_packet,
        tgnt=tgnt_packet,
        oak=oak_packet,
        exp=exp_packet,
        negative_memory=negative_memory,
    )
    return {
        "engine": "Omega-MGHFM-TGNT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mother_equation": "X_next = EXP(OAK(TGNT(J(CVCD(LOG(HGFM(X)))))))",
        "cycle": asdict(cycle),
        "oak_note": "Research architecture prototype; OAK status is local and heuristic, not external truth.",
    }


def write_outputs(result: Dict[str, object], reports_dir: Path, examples_dir: Path) -> None:
    reports_dir.mkdir(exist_ok=True)
    examples_dir.mkdir(exist_ok=True)
    (reports_dir / "omega_mghfm_tgnt_latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (reports_dir / "omega_mghfm_tgnt_latest.md").write_text(render_markdown(result), encoding="utf-8")
    summary = {
        "engine": result["engine"],
        "generated_at_utc": result["generated_at_utc"],
        "mother_equation": result["mother_equation"],
        "oak_statuses": result["cycle"]["oak"]["statuses"],
        "top_jkd_actions": result["cycle"]["jkd"]["top_jkd_actions"],
        "oak_note": result["oak_note"],
    }
    (examples_dir / "omega_mghfm_tgnt_latest.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def render_markdown(result: Dict[str, object]) -> str:
    cycle = result["cycle"]
    lines = [
        "# Omega-MGHFM-TGNT Latest Cycle",
        "",
        f"**Generated UTC:** `{result['generated_at_utc']}`",
        f"**Equation:** `{result['mother_equation']}`",
        "",
        "## LOG signature",
        "",
        "```json",
        json.dumps(cycle["log_layers"]["Lomega_minimal_fertile_signature"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## OAK statuses",
        "",
        "```json",
        json.dumps(cycle["oak"]["statuses"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Top JKD actions",
        "",
    ]
    for action in cycle["jkd"]["top_jkd_actions"]:
        lines.append(f"- `{action['action']}` — JKD `{action['jkd_score']}`")
    lines.extend(
        [
            "",
            "## EXP outputs",
            "",
            "```json",
            json.dumps(cycle["exp"], indent=2, ensure_ascii=False),
            "```",
            "",
            "## OAK note",
            "",
            result["oak_note"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Omega-MGHFM-TGNT prototype cycle.")
    parser.add_argument("inputs", nargs="*", default=["prime tensor gaps", "LOG EXP codex", "OAK memory negative", "JKD YY3 Tristan2"])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run_cycle(args.inputs)
    if args.write:
        write_outputs(result, Path("reports"), Path("examples"))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
