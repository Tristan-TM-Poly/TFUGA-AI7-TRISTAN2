"""Artifact bundle generation for the Synergy Foundry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .experiments import compile_experiment, counterfactual_twin
from .graph import CreationGraph
from .meta import compose_meta_synergies
from .models import CreationDNA, SynergyCandidate
from .pr_orchestra import compile_pr_gene, orchestra_manifest
from .product import compile_product_hypothesis


M_MINUS = [
    "Similarity is not complementarity.",
    "Co-mention is not causality.",
    "A large composition must beat the simplest baseline.",
    "Two agents using the same evidence are not independent confirmation.",
    "Interface losses must be explicit.",
    "Confidence decays and requires revalidation.",
    "No irreversible remote action is authorized by a heuristic score.",
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_foundry_bundle(
    out: Path,
    roots: list[Path],
    creations: list[CreationDNA],
    candidates_by_order: dict[int, list[SynergyCandidate]],
    parameters: dict,
    diagnostics: Iterable[str] = (),
) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    graph = CreationGraph(creations)
    graph.infer_edges()
    all_candidates = [candidate for order in sorted(candidates_by_order) for candidate in candidates_by_order[order]]
    experiments = [compile_experiment(candidate) for candidate in all_candidates]
    counterfactuals = [counterfactual_twin(candidate) for candidate in all_candidates]
    genes = [compile_pr_gene(candidate, experiment) for candidate, experiment in zip(all_candidates, experiments)]
    metas = compose_meta_synergies(all_candidates[: min(12, len(all_candidates))])
    domains_by_name = {item.name: item.domains for item in creations}
    products = [
        compile_product_hypothesis(candidate, sorted({domain for system in candidate.systems for domain in domains_by_name.get(system, [])}))
        for candidate in all_candidates
    ]

    report = {
        "schema_version": "1.0",
        "engine": "OMEGA-SYNERGY-T-FOUNDRY",
        "authority": "review_only_heuristic",
        "repo_roots": [str(path) for path in roots],
        "parameters": parameters,
        "counts": {
            "creations": len(creations),
            "graph_edges": len(graph.edges),
            "synergy_candidates": len(all_candidates),
            "experiments": len(experiments),
            "pr_genes": len(genes),
            "meta_synergies": len(metas),
            "product_hypotheses": len(products),
        },
        "synergies_by_order": {
            str(order): [candidate.to_dict() for candidate in candidates]
            for order, candidates in candidates_by_order.items()
        },
        "m_minus": M_MINUS,
        "diagnostics": list(diagnostics),
    }

    inventory_payload = [item.to_dict() for item in creations]
    _write_json(out / "creation_dna.json", inventory_payload)
    _write_json(out / "system_inventory.json", inventory_payload)
    _write_json(out / "creation_graph.json", graph.to_dict())
    (out / "creation_graph.dot").write_text(graph.to_dot(), encoding="utf-8")
    _write_json(out / "synergy_report.json", report)
    _write_json(out / "synergy_n.json", report)
    experiment_payload = [item.to_dict() for item in experiments]
    _write_json(out / "experiment_queue.json", experiment_payload)
    _write_json(out / "research_queue.json", experiment_payload)
    _write_json(out / "counterfactual_twins.json", counterfactuals)
    _write_json(out / "pr_orchestra.json", orchestra_manifest(genes))
    _write_json(out / "meta_synergies.json", [item.to_dict() for item in metas])
    _write_json(out / "product_hypotheses.json", [item.to_dict() for item in products])

    dashboard = [
        "# Ω-SYNERGY-T∞ Foundry Report",
        "",
        "Authority: **review-only heuristic**. Scores schedule experiments; they do not certify truth, safety, IP, product-market fit or revenue.",
        "",
        f"- CreationDNA records: **{len(creations)}**",
        f"- Graph edges: **{len(graph.edges)}**",
        f"- Synergy candidates: **{len(all_candidates)}**",
        f"- Meta-synergies: **{len(metas)}**",
        "",
    ]
    for order in sorted(candidates_by_order):
        dashboard.extend([f"## Order {order}", ""])
        for index, candidate in enumerate(candidates_by_order[order], start=1):
            flags = ", ".join(candidate.anti_synergy_flags) or "none"
            dashboard.append(f"{index}. **{candidate.score:.3f}** — {' × '.join(candidate.systems)} — flags: `{flags}`")
        dashboard.append("")
    dashboard.extend(["## M⁻", "", *[f"- {item}" for item in M_MINUS], ""])
    markdown = "\n".join(dashboard)
    (out / "SYNERGY_FOUNDRY_REPORT.md").write_text(markdown, encoding="utf-8")
    (out / "SYNERGY_N_REPORT.md").write_text(markdown, encoding="utf-8")
    return report
