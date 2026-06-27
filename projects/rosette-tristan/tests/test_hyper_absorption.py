import json
from pathlib import Path

from rosette_tristan.claim_graph import build_claim_graph
from rosette_tristan.code_forge import forge_equation_code
from rosette_tristan.consensus import ArtifactVote, build_consensus
from rosette_tristan.equation_oak import dimensional_oak
from rosette_tristan.hyper_pipeline import RosetteHyperAbsorptionPipeline
from rosette_tristan.ip_guardian import classify_ip_guardian


def test_consensus_prefers_weighted_equation():
    item = build_consensus([
        ArtifactVote("equation", "x = y", "a", confidence=0.9),
        ArtifactVote("equation", "x=y", "b", confidence=0.9),
        ArtifactVote("equation", "x = z", "c", confidence=0.2),
    ], artifact_id="E1")
    assert item.consensus_value.replace(" ", "") == "x=y"
    assert item.oak_status == "usable_not_certified"
    assert "dimensional_oak" in item.required_next_check


def test_dimensional_oak_decay_equation():
    check = dimensional_oak(r"\frac{dx}{dt} = -k x + u(t)")
    assert check.dimensional_status == "consistent_partial"
    assert check.inferred_units["k"] == "1/time"


def test_claim_graph_and_code_forge():
    claims = [type("Claim", (), {"claim": "We show the model improves stability under noisy input."})()]
    equations = [type("Eq", (), {"latex": r"\frac{dx}{dt} = -k x + u(t)"})()]
    graph = build_claim_graph(claims, equations)
    assert graph[0].counter_checks
    forged = forge_equation_code(equations[0].latex, level=3)
    assert "simulate_euler" in forged.python_code
    assert forged.oak_status == "translated_needs_validation"


def test_ip_guardian_confidential():
    report = classify_ip_guardian("Confidential proprietary claim text")
    assert report.copyright_status == "restricted_or_confidential"
    assert "external_sharing" in report.forbidden_outputs


def test_hyper_pipeline_outputs(tmp_path: Path):
    out = tmp_path / "hyper"
    payload = RosetteHyperAbsorptionPipeline().compile("examples/sample_paper.txt", out)
    assert payload["oak_status"] == "hyper_research_usable_not_certified"
    assert payload["equation_oak"]
    assert (out / "hyper_absorption.json").exists()
    data = json.loads((out / "hyper_absorption.json").read_text(encoding="utf-8"))
    assert "ip_guardian" in data
    assert "bench_metrics" in data
