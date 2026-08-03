from __future__ import annotations

from .campaign import MutationCampaignEngine, mutation_specs_from_mapping, mutation_tests_from_mapping
from .counterexamples import CounterexampleForge
from .ecology import MutationEcologyEngine
from .metamorphic import MetamorphicEngine, contracts_from_mapping
from .mminus import MMinusCompiler


def _fixtures():
    mutants = {
        "target": "path_normalizer",
        "baseline_behavior": "exact_prefix",
        "claim_id": "CLAIM-PATH-NORMALIZATION-EXACT-PREFIX",
        "mutants": [
            {"mutant_id": "M-LSTRIP", "operator_id": "OP-CHARSET-TRIM", "target": "path_normalizer", "behavior": "lstrip_charset", "description": "Use lstrip('./').", "weight": 2.0},
            {"mutant_id": "M-STRIP", "operator_id": "OP-BIDIRECTIONAL-TRIM", "target": "path_normalizer", "behavior": "strip_charset", "description": "Trim both ends.", "weight": 1.5},
            {"mutant_id": "M-DOT", "operator_id": "OP-DROP-DOT", "target": "path_normalizer", "behavior": "remove_leading_dot", "description": "Remove a leading dot.", "weight": 2.0},
            {"mutant_id": "M-ALL-PREFIX", "operator_id": "OP-LOOP-PREFIX", "target": "path_normalizer", "behavior": "all_relative_prefixes", "description": "Remove all repeated ./ prefixes.", "weight": 1.0},
            {"mutant_id": "M-EQUIV", "operator_id": "OP-REFORMULATE", "target": "path_normalizer", "behavior": "exact_prefix_clone", "description": "Equivalent reformulation.", "expected_equivalent": True},
            {"mutant_id": "M-INVALID", "operator_id": "OP-UNKNOWN", "target": "path_normalizer", "behavior": "unknown_behavior", "description": "Invalid operator."},
        ],
    }
    tests = {"tests": [
        {"test_id": "T-DOT-GITHUB", "claim_ids": ["CLAIM-PATH-NORMALIZATION-EXACT-PREFIX"], "input": ".github/workflows/ci.yml", "expected": ".github/workflows/ci.yml"},
        {"test_id": "T-ONE-PREFIX", "claim_ids": ["CLAIM-PATH-NORMALIZATION-EXACT-PREFIX"], "input": "./omega/file.py", "expected": "omega/file.py"},
        {"test_id": "T-PARENT", "claim_ids": ["CLAIM-PATH-NORMALIZATION-EXACT-PREFIX"], "input": "../omega/file.py", "expected": "../omega/file.py"},
        {"test_id": "T-PLAIN", "claim_ids": ["CLAIM-PATH-NORMALIZATION-EXACT-PREFIX"], "input": "omega/file.py", "expected": "omega/file.py"},
    ]}
    seeds = {"explicit": ["././a", "././.github", ".github"], "prefixes": ["", "./", "././"], "atoms": ["a", ".github"], "suffixes": ["", "/b"]}
    contracts = {"contracts": [
        {"property_id": "PROP-EXACT-ONE-PREFIX", "claim_id": "CLAIM-PATH-NORMALIZATION-EXACT-PREFIX", "kind": "exact_one_prefix_removal", "description": "Remove exactly one ./ prefix.", "seed_inputs": ["./a", "././a", ".github", "../a"]},
        {"property_id": "PROP-DOT-PRESERVE", "claim_id": "CLAIM-PATH-NORMALIZATION-EXACT-PREFIX", "kind": "leading_dot_preservation", "description": "Preserve non-relative leading dots.", "seed_inputs": [".github", ".config", "../a"]},
    ]}
    return mutants, tests, seeds, contracts


def run_oakbench() -> dict[str, object]:
    mutants, tests, seeds, contracts = _fixtures()
    specs = mutation_specs_from_mapping(mutants)
    campaign = MutationCampaignEngine().run(specs, mutation_tests_from_mapping(tests), target="path_normalizer", baseline_behavior="exact_prefix")
    counter = CounterexampleForge().search(specs, campaign.surviving_mutant_ids, seeds, baseline_behavior="exact_prefix", claim_id="CLAIM-PATH-NORMALIZATION-EXACT-PREFIX", property_id="PROP-EXACT-ONE-PREFIX")
    metamorphic = MetamorphicEngine().evaluate(contracts_from_mapping(contracts), ["exact_prefix", "all_relative_prefixes", "lstrip_charset"])
    mminus = MMinusCompiler().compile(counter.counterexamples)
    ecology, artifacts = MutationEcologyEngine().run(mutants=mutants, tests=tests, seeds=seeds, contracts=contracts)
    checks = {
        "campaign_has_kills": campaign.killed >= 3,
        "campaign_has_survivor": campaign.survived == 1,
        "equivalent_explicit": campaign.equivalent == 1,
        "invalid_explicit": campaign.invalid == 1,
        "counterexample_found": len(counter.counterexamples) == 1,
        "counterexample_minimized": counter.counterexamples[0].minimized_input != "" if counter.counterexamples else False,
        "metamorphic_detects_faults": metamorphic.failed_checks > 0,
        "mminus_generated": len(mminus.rules) == 1,
        "no_tests_applied": artifacts["mminus"]["tests_applied"] is False,
        "a3_preserved": ecology.to_dict()["maximum_authority"] == "A3",
        "no_remote_mutations": ecology.to_dict()["remote_mutations"] == 0,
        "no_patch": ecology.to_dict()["automatic_patch_allowed"] is False,
    }
    return {
        "schema": "omega-ci-r05-oakbench/v5",
        "passed": all(checks.values()),
        "checks": checks,
        "mutation_score": campaign.mutation_score,
        "weighted_mutation_score": campaign.weighted_mutation_score,
        "counterexamples": len(counter.counterexamples),
        "maximum_authority": "A3",
        "automatic_patch_allowed": False,
        "automatic_merge_allowed": False,
        "remote_mutations": 0,
    }
