from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from omega_org_fam_t.evidence_benchmark import audit_benchmark, generate_benchmark, scenario
from omega_org_fam_t.evidence_engine import EvidenceEngine
from omega_org_fam_t.evidence_index import EvidenceIndex
from omega_org_fam_t.evidence_ledger import GENESIS, append_event, build_event, verify_events
from omega_org_fam_t.evidence_models import EvidenceBundle, Peak, SourceRef, SpectralObservation
from omega_org_fam_t.formula import Species, balance_reaction, is_balanced, parse_formula, reaction_residual
from omega_org_fam_t.mixture import fit_nonnegative_mixture
from omega_org_fam_t.pattern_registry import SEED_PATTERN_REGISTRY, PatternRegistry, validate_pattern_syntax
from omega_org_fam_t.seed_rules_r03 import SEED_RULES
from omega_org_fam_t.spectral_evidence import evaluate_numeric_rule, fuse_rule_evaluations


def source(source_id: str = "src") -> SourceRef:
    return SourceRef(source_id, "test", "local", "CC0", "2026-08-02", hashlib.sha256(b"test").hexdigest(), 0.9, "synthetic_test")


def test_formula_parser_nested_and_isotope() -> None:
    assert parse_formula("C6H12O6") == {"C": 6, "H": 12, "O": 6}
    assert parse_formula("C6H4(OH)2") == {"C": 6, "H": 6, "O": 2}
    assert parse_formula("[13C]2H4O") == {"13C": 2, "H": 4, "O": 1}
    with pytest.raises(ValueError):
        parse_formula("C6H5-OH")


def test_exact_reaction_balancing() -> None:
    reactants = (Species("C2H6"), Species("O2"))
    products = (Species("CO2"), Species("H2O"))
    left, right = balance_reaction(reactants, products)
    assert left == (2, 7)
    assert right == (4, 6)
    assert is_balanced(zip(left, reactants, strict=True), zip(right, products, strict=True))


def test_charge_balance() -> None:
    residual = reaction_residual(((1, Species("Fe", 2)),), ((1, Species("Fe", 3)), (1, Species("e", -1))))
    assert residual == {}


def test_spectral_multimodal_fusion() -> None:
    src = source()
    ftir = SpectralObservation("o1", "ftir", (Peak(3350, 1.0, 10), Peak(1100, 0.7, 8)), src.source_id)
    raman = SpectralObservation("o2", "raman", (Peak(1070, 1.0, 5),), src.source_id)
    bundle = EvidenceBundle("b1", ("alcohol_phenol", "aldehyde_ketone"), (ftir, raman), (src,), formula="C2H6O")
    engine = EvidenceEngine(SEED_RULES)
    ranking = engine.rank(bundle)
    assert ranking[0][0] == "alcohol_phenol"
    assert ranking[0][1] > 0.8
    assert engine.evaluate(bundle)["alcohol_phenol"]["modalities"] == 2


def test_counter_signature_reduces_score() -> None:
    rule = SEED_RULES[0]
    observation = SpectralObservation("o", "ftir", (Peak(3350, 1, 10), Peak(1100, 1, 10), Peak(5050, 1, 5)), "src")
    result = evaluate_numeric_rule(rule, observation, source_quality=1.0)
    assert result.matched_counters
    assert result.score < 0.65
    assert fuse_rule_evaluations((result,))["status"] == "conflicted_evidence"


def test_nonnegative_mixture_recovers_coefficients() -> None:
    fit = fit_nonnegative_mixture([2.0, 2.0, 3.0, 3.0], {"a": [1.0, 1.0, 0.0, 0.0], "b": [0.0, 0.0, 1.0, 1.0]})
    assert fit.converged
    assert fit.coefficients == {"a": 2.0, "b": 3.0}
    assert fit.rmse == 0.0


def test_ledger_hash_chain_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    first = append_event(path, "ingest", {"bundle": "b1"})
    second = append_event(path, "score", {"family": "alcohol"})
    assert first.previous_hash == GENESIS
    assert second.previous_hash == first.event_hash
    assert verify_events((first, second))["valid"]
    tampered = build_event(1, "score", {"family": "ketone"}, first.event_hash)
    bad = type(tampered)(tampered.sequence, tampered.event_type, {"changed": True}, tampered.previous_hash, tampered.event_hash)
    assert not verify_events((first, bad))["valid"]


def test_sqlite_index_round_trip(tmp_path: Path) -> None:
    src = source()
    observation = SpectralObservation("o1", "ftir", (Peak(3350, 1, 10), Peak(1100, 1, 10)), src.source_id)
    bundle = EvidenceBundle("b1", ("alcohol_phenol",), (observation,), (src,), formula="C2H6O")
    scores = EvidenceEngine(SEED_RULES).evaluate(bundle)
    with EvidenceIndex(tmp_path / "evidence.sqlite3") as index:
        index.ingest_bundle(bundle)
        index.upsert_family_scores(bundle.bundle_id, scores)
        assert index.stats() == {"bundles": 1, "sources": 1, "observations": 1, "family_scores": 1}
        assert index.query_family("alcohol_phenol", minimum_score=0.5)[0]["bundle_id"] == "b1"


def test_synthetic_scenario_deterministic() -> None:
    assert scenario(123456) == scenario(123456)
    assert len(scenario(0)) == 4


def test_benchmark_generation_and_audit(tmp_path: Path) -> None:
    manifest = generate_benchmark(tmp_path, cases=100_000, shard_cases=16_384, clean=True)
    output = tmp_path / "generated" / "omega_org_fam_t_r03_evidence_benchmark"
    audit = audit_benchmark(output)
    assert audit["valid"] and audit["cases"] == 100_000
    assert manifest["correct"] + manifest["wrong"] + manifest["abstained"] == 100_000
    assert manifest["generator"]["permanent_total_ceiling"] is None


def test_pattern_registry_fingerprint_and_roundtrip(tmp_path: Path) -> None:
    assert validate_pattern_syntax("[CX3]=[OX1]")[0]
    assert not validate_pattern_syntax("[CX3", transformation=False)[0]
    assert validate_pattern_syntax("[C:1][OH:2]>>[C:1]=[O:2]", transformation=True)[0]
    path = tmp_path / "patterns.json"
    SEED_PATTERN_REGISTRY.dump(path)
    loaded = PatternRegistry.load(path)
    assert loaded.fingerprint == SEED_PATTERN_REGISTRY.fingerprint
    assert len(loaded.patterns) >= 10
