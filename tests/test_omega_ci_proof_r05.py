from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_ci_proof_t.r05.behaviors import normalize_exact_prefix, resolve_behavior
from omega_ci_proof_t.r05.campaign import MutationCampaignEngine, mutation_specs_from_mapping, mutation_tests_from_mapping
from omega_ci_proof_t.r05.counterexamples import CounterexampleForge
from omega_ci_proof_t.r05.differential import DifferentialOracle
from omega_ci_proof_t.r05.ecology import MutationEcologyEngine
from omega_ci_proof_t.r05.metamorphic import MetamorphicEngine, contracts_from_mapping
from omega_ci_proof_t.r05.mminus import MMinusCompiler
from omega_ci_proof_t.r05.models import MutationSpec, MutationTest
from omega_ci_proof_t.r05.oak import run_oakbench

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "omega_ci_proof_t"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def specs():
    return mutation_specs_from_mapping(load("r05-mutants.json"))


def mutation_test_cases():
    return mutation_tests_from_mapping(load("r05-tests.json"))


def campaign():
    raw = load("r05-mutants.json")
    return MutationCampaignEngine().run(specs(), mutation_test_cases(), target=raw["target"], baseline_behavior=raw["baseline_behavior"])


def test_exact_prefix_preserves_dot_github():
    assert normalize_exact_prefix(".github/workflows/ci.yml") == ".github/workflows/ci.yml"


def test_exact_prefix_removes_only_one_prefix():
    assert normalize_exact_prefix("././a") == "./a"


def test_unknown_behavior_is_rejected():
    with pytest.raises(KeyError):
        resolve_behavior("missing")


def test_mutation_spec_requires_positive_weight():
    with pytest.raises(ValueError):
        MutationSpec("M", "O", "T", "identity", "x", weight=0)


def test_campaign_requires_specs():
    with pytest.raises(ValueError):
        MutationCampaignEngine().run((), mutation_test_cases(), target="path_normalizer", baseline_behavior="exact_prefix")


def test_campaign_requires_mutation_test_cases():
    with pytest.raises(ValueError):
        MutationCampaignEngine().run(specs(), (), target="path_normalizer", baseline_behavior="exact_prefix")


def test_campaign_rejects_duplicate_mutants():
    duplicate = (specs()[0], specs()[0])
    with pytest.raises(ValueError, match="duplicate"):
        MutationCampaignEngine().run(duplicate, mutation_test_cases(), target="path_normalizer", baseline_behavior="exact_prefix")


def test_campaign_rejects_invalid_baseline_contract():
    bad = (MutationTest("T", ("C",), "./a", "wrong"),)
    with pytest.raises(ValueError, match="baseline fails"):
        MutationCampaignEngine().run((specs()[0],), bad, target="path_normalizer", baseline_behavior="exact_prefix")


def test_campaign_counts_are_explicit():
    report = campaign()
    assert (report.killed, report.survived, report.equivalent, report.invalid) == (3, 1, 1, 1)


def test_campaign_mutation_score_is_finite():
    report = campaign()
    assert report.mutation_score == 0.75
    assert report.weighted_mutation_score == 0.846154


def test_campaign_survivor_is_repeated_prefix_mutant():
    assert campaign().surviving_mutant_ids == ("M-ALL-PREFIX",)


def test_campaign_is_deterministic_under_reversed_inputs():
    raw = load("r05-mutants.json")
    a = MutationCampaignEngine().run(specs(), mutation_test_cases(), target=raw["target"], baseline_behavior=raw["baseline_behavior"])
    b = MutationCampaignEngine().run(tuple(reversed(specs())), tuple(reversed(mutation_test_cases())), target=raw["target"], baseline_behavior=raw["baseline_behavior"])
    assert a.campaign_id == b.campaign_id


def test_campaign_never_applies_code_changes():
    payload = campaign().to_dict()
    assert payload["code_changes_applied"] is False
    assert payload["automatic_patch_allowed"] is False
    assert payload["remote_mutations"] == 0


def test_counterexample_forge_finds_survivor_witness():
    report = CounterexampleForge().search(
        specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"),
        baseline_behavior="exact_prefix", claim_id="CLAIM-PATH-NORMALIZATION-EXACT-PREFIX",
        property_id="PROP-EXACT-ONE-PREFIX",
    )
    assert len(report.counterexamples) == 1
    assert report.counterexamples[0].mutant_id == "M-ALL-PREFIX"


def test_counterexample_is_minimized_and_still_distinguishes():
    report = CounterexampleForge().search(
        specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"),
        baseline_behavior="exact_prefix", claim_id="C", property_id="P",
    )
    item = report.counterexamples[0]
    assert item.minimized_input
    assert item.expected_output != item.observed_output


def test_counterexample_provenance_is_recorded():
    report = CounterexampleForge().search(
        specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"),
        baseline_behavior="exact_prefix", claim_id="C", property_id="P",
    )
    assert any(value.startswith("seed-space:") for value in report.counterexamples[0].provenance)


def test_counterexample_report_is_deterministic():
    kwargs = dict(
        baseline_behavior="exact_prefix", claim_id="C", property_id="P"
    )
    a = CounterexampleForge().search(specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"), **kwargs)
    b = CounterexampleForge().search(tuple(reversed(specs())), tuple(reversed(campaign().surviving_mutant_ids)), load("r05-seeds.json"), **kwargs)
    assert a.report_id == b.report_id


def test_counterexample_unknown_survivor_is_rejected():
    with pytest.raises(KeyError):
        CounterexampleForge().search(specs(), ["UNKNOWN"], load("r05-seeds.json"), baseline_behavior="exact_prefix", claim_id="C", property_id="P")


def test_counterexample_budget_must_be_positive():
    with pytest.raises(ValueError):
        CounterexampleForge().search(specs(), [], load("r05-seeds.json"), baseline_behavior="exact_prefix", claim_id="C", property_id="P", max_candidates=0)


def test_counterexample_report_never_executes_remote_mutation():
    report = CounterexampleForge().search(
        specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"), baseline_behavior="exact_prefix", claim_id="C", property_id="P"
    )
    assert report.to_dict()["execution_authorized"] is False
    assert report.to_dict()["remote_mutations"] == 0


def test_metamorphic_baseline_has_no_failures():
    report = MetamorphicEngine().evaluate(contracts_from_mapping(load("r05-contracts.json")), ["exact_prefix"])
    assert report.failed_checks == 0


def test_metamorphic_detects_lstrip_damage():
    report = MetamorphicEngine().evaluate(contracts_from_mapping(load("r05-contracts.json")), ["lstrip_charset"])
    assert report.failed_checks > 0
    assert any(item.property_id == "PROP-DOT-PRESERVE" for item in report.findings)


def test_metamorphic_detects_repeated_prefix_survivor():
    report = MetamorphicEngine().evaluate(contracts_from_mapping(load("r05-contracts.json")), ["all_relative_prefixes"])
    assert any(item.property_id == "PROP-EXACT-ONE-PREFIX" for item in report.findings)


def test_metamorphic_rejects_unknown_kind():
    raw = {"contracts": [{"property_id":"P","claim_id":"C","kind":"unknown","description":"x","seed_inputs":["a"]}]}
    with pytest.raises(ValueError):
        MetamorphicEngine().evaluate(contracts_from_mapping(raw), ["exact_prefix"])


def test_differential_reports_divergences():
    report = DifferentialOracle().compare(
        reference_behavior="exact_prefix",
        candidate_behaviors=["lstrip_charset", "all_relative_prefixes"],
        corpus=[".github", "./a", "././a"],
        claim_id="C",
    )
    assert len(report.divergences) >= 2


def test_differential_equivalent_clone_agrees():
    report = DifferentialOracle().compare(reference_behavior="exact_prefix", candidate_behaviors=["exact_prefix_clone"], corpus=[".github", "./a", "././a"], claim_id="C")
    assert report.divergences == ()
    assert report.agreements == 3


def test_mminus_compiler_emits_candidate_not_applied():
    counter = CounterexampleForge().search(specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"), baseline_behavior="exact_prefix", claim_id="C", property_id="P")
    compilation = MMinusCompiler().compile(counter.counterexamples)
    assert len(compilation.rules) == 1
    payload = compilation.to_dict()
    assert payload["tests_applied"] is False
    assert payload["code_changes_applied"] is False
    assert payload["human_review_required"] is True


def test_mminus_generated_test_is_traceable():
    counter = CounterexampleForge().search(specs(), campaign().surviving_mutant_ids, load("r05-seeds.json"), baseline_behavior="exact_prefix", claim_id="C", property_id="P")
    compilation = MMinusCompiler().compile(counter.counterexamples)
    assert counter.counterexamples[0].counterexample_id in compilation.generated_tests[0]


def test_ecology_links_all_artifacts():
    report, artifacts = MutationEcologyEngine().run(
        mutants=load("r05-mutants.json"), tests=load("r05-tests.json"), seeds=load("r05-seeds.json"), contracts=load("r05-contracts.json")
    )
    assert set(artifacts) == {"campaign", "counterexamples", "metamorphic", "differential", "mminus", "ecology"}
    assert report.campaign_id == artifacts["campaign"]["campaign_id"]


def test_ecology_has_five_specialized_agents():
    report, _ = MutationEcologyEngine().run(mutants=load("r05-mutants.json"), tests=load("r05-tests.json"), seeds=load("r05-seeds.json"), contracts=load("r05-contracts.json"))
    assert [item.agent for item in report.agents] == ["MutationPredator", "CounterexampleForge", "MetamorphicHunter", "DifferentialHunter", "MMinusCompiler"]


def test_ecology_resolves_known_survivor():
    report, _ = MutationEcologyEngine().run(mutants=load("r05-mutants.json"), tests=load("r05-tests.json"), seeds=load("r05-seeds.json"), contracts=load("r05-contracts.json"))
    assert report.unresolved_survivors == ()


def test_ecology_preserves_a3_and_human_review():
    report, _ = MutationEcologyEngine().run(mutants=load("r05-mutants.json"), tests=load("r05-tests.json"), seeds=load("r05-seeds.json"), contracts=load("r05-contracts.json"))
    payload = report.to_dict()
    assert payload["maximum_authority"] == "A3"
    assert payload["human_review_required"] is True
    assert payload["automatic_patch_allowed"] is False
    assert payload["automatic_merge_allowed"] is False
    assert payload["remote_mutations"] == 0


def test_oakbench_passes():
    result = run_oakbench()
    assert result["passed"]
    assert result["mutation_score"] == 0.75
    assert result["maximum_authority"] == "A3"
    assert result["automatic_patch_allowed"] is False
    assert result["remote_mutations"] == 0
