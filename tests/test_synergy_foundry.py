from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from omega_synergy_t.discovery import closure_bridges, discover_n_order, select_portfolio
from omega_synergy_t.experiments import compile_experiment, counterfactual_twin
from omega_synergy_t.graph import CreationGraph
from omega_synergy_t.ledger import ProofLedger, revalidation_status
from omega_synergy_t.meta import compose_meta_synergies
from omega_synergy_t.models import CreationDNA, EvidenceRecord, SynergyStage
from omega_synergy_t.pr_orchestra import compile_pr_gene, orchestra_manifest
from omega_synergy_t.reporting import write_foundry_bundle
from omega_synergy_t.scanner import ScannerPolicy, scan_repositories
from omega_synergy_t.scoring import approximate_shapley, build_candidate, decayed_confidence


def seed_repo(root: Path) -> None:
    (root / "docs" / "canon").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "docs" / "canon" / "systems.md").write_text(
        """# Canon

Ω-AUTO²-T orchestrates workflow automation with OAKGate.
Ω-ROSETTE-T transforms PDF -> claim graph and preserves provenance.
Ω-DOC-T needs claim graph -> tested documentation before promotion.
Ω-STARTUP-T transforms validated report -> product offer.
TODO Ω-AUTO²-T needs source code -> test suite.
""",
        encoding="utf-8",
    )
    (root / "src" / "bridge.py").write_text(
        "# Ω-OAK-T transforms source code -> test suite and test suite -> evidence report\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_rosette.py").write_text(
        "# Ω-ROSETTE-T + Ω-DOC-T baseline test passed\n",
        encoding="utf-8",
    )


def test_scanner_compiles_creation_dna_and_transforms(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path], ScannerPolicy(max_nodes=50))
    names = {item.name for item in result.creations}
    assert {"Ω-AUTO²-T", "Ω-ROSETTE-T", "Ω-DOC-T", "Ω-STARTUP-T", "Ω-OAK-T", "OAKGate"} <= names
    rosette = next(item for item in result.creations if item.name == "Ω-ROSETTE-T")
    assert rosette.capabilities
    assert rosette.evidence_score > 0
    auto = next(item for item in result.creations if item.name == "Ω-AUTO²-T")
    assert auto.needs


def test_capability_need_matching_without_exact_system_name(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    bridges = closure_bridges(result.creations, threshold=0.3)
    assert any(bridge.provider == "Ω-OAK-T" and bridge.target == "Ω-AUTO²-T" for bridge in bridges)
    assert all("provenance_preservation" in bridge.contract.preserved_invariants for bridge in bridges)


def test_semantic_similarity_without_closure_is_flagged() -> None:
    evidence = [EvidenceRecord(kind="doc", source="x", strength=0.5)]
    left = CreationDNA(
        id="A", name="A", repository="r", paths=["a.md"], mentions=2,
        domains=["software"], tokens=["graph", "engine", "code"], evidence=evidence,
    )
    right = CreationDNA(
        id="B", name="B", repository="r", paths=["b.md"], mentions=2,
        domains=["software"], tokens=["graph", "engine", "code"], evidence=evidence,
    )
    candidate = build_candidate([left, right])
    assert "semantic_similarity_without_capability_need_match" in candidate.anti_synergy_flags
    assert candidate.stage == SynergyStage.S1_RESONANCE


def test_discovery_is_bounded_and_deterministic(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    first = discover_n_order(result.creations, result.file_systems, max_order=4, beam_width=16, top_k=6)
    second = discover_n_order(result.creations, result.file_systems, max_order=4, beam_width=16, top_k=6)
    assert [item.id for item in first[2]] == [item.id for item in second[2]]
    assert all(len(items) <= 6 for items in first.values())
    assert all(item.order == order for order, items in first.items() for item in items)


def test_experiment_has_baseline_ablation_oak_and_rollback(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    candidate = discover_n_order(result.creations, result.file_systems, max_order=2, beam_width=12, top_k=4)[2][0]
    experiment = compile_experiment(candidate)
    assert len(experiment.baselines) >= 3
    assert experiment.ablations
    assert "baseline_required" in experiment.oak_gates
    assert experiment.rollback
    twin = counterfactual_twin(candidate)
    assert twin["counterfactual_worlds"]


def test_creation_graph_and_meta_synergy(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    graph = CreationGraph(result.creations)
    graph.infer_edges()
    assert graph.nodes
    assert graph.to_dot().startswith("digraph")
    candidates = discover_n_order(result.creations, result.file_systems, max_order=2, beam_width=20, top_k=10)[2]
    metas = compose_meta_synergies(candidates, max_chain=2, top_k=10)
    assert isinstance(metas, list)


def test_pr_orchestra_never_authorizes_merge(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    candidates = discover_n_order(result.creations, result.file_systems, max_order=2, beam_width=12, top_k=3)[2]
    genes = [compile_pr_gene(candidate, compile_experiment(candidate)) for candidate in candidates]
    manifest = orchestra_manifest(genes)
    assert manifest["authority"] == "review_only_plan"
    assert "No merge is authorized by this manifest." in manifest["rules"]
    assert manifest["waves"]


def test_proof_ledger_hash_chain_and_tamper_detection(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = ProofLedger(path)
    ledger.append("SYN-1", "hypothesis", "Candidate created")
    ledger.append("SYN-1", "benchmark", "Baseline measured", metrics={"gain": 0.12})
    ok, errors = ledger.verify()
    assert ok and not errors
    lines = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["claim"] = "tampered"
    lines[0] = json.dumps(payload)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, errors = ledger.verify()
    assert not ok and errors


def test_half_life_and_revalidation() -> None:
    assert decayed_confidence(1.0, 30, 30) == pytest.approx(0.5)
    stamp = (datetime.now(UTC) - timedelta(days=40)).replace(microsecond=0).isoformat()
    status = revalidation_status(stamp, 0.8, 30)
    assert status["revalidation_required"]


def test_shapley_credit_sums_to_total_value() -> None:
    weights = {"A": 1.0, "B": 2.0, "C": 3.0}
    values = approximate_shapley(list(weights), lambda coalition: sum(weights[item] for item in coalition))
    assert sum(values.values()) == pytest.approx(6.0)
    assert values["C"] == pytest.approx(3.0)


def test_portfolio_respects_budget(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = scan_repositories([tmp_path])
    candidates = discover_n_order(result.creations, result.file_systems, max_order=3, beam_width=20, top_k=10)
    all_candidates = [item for order in candidates.values() for item in order]
    selected = select_portfolio(all_candidates, budget=1.2, max_items=5)
    assert len(selected) <= 5


def test_foundry_bundle_is_review_only_and_complete(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    seed_repo(repo)
    result = scan_repositories([repo])
    candidates = discover_n_order(result.creations, result.file_systems, max_order=3, beam_width=20, top_k=6)
    out = repo / "reports" / "foundry"
    report = write_foundry_bundle(out, [repo], result.creations, candidates, {"max_order": 3})
    assert report["authority"] == "review_only_heuristic"
    for name in (
        "creation_dna.json", "creation_graph.json", "creation_graph.dot", "synergy_report.json",
        "experiment_queue.json", "counterfactual_twins.json", "pr_orchestra.json",
        "meta_synergies.json", "product_hypotheses.json", "SYNERGY_FOUNDRY_REPORT.md",
    ):
        assert (out / name).exists(), name
