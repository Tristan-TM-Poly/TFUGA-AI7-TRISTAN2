from __future__ import annotations

from typing import Any, Mapping

from .campaign import MutationCampaignEngine, mutation_specs_from_mapping, mutation_tests_from_mapping
from .counterexamples import CounterexampleForge
from .differential import DifferentialOracle
from .metamorphic import MetamorphicEngine, contracts_from_mapping
from .mminus import MMinusCompiler
from .models import EcologyAgentResult, MutationEcologyReport


class MutationEcologyEngine:
    def run(
        self,
        *,
        mutants: Mapping[str, Any],
        tests: Mapping[str, Any],
        seeds: Mapping[str, Any],
        contracts: Mapping[str, Any],
    ) -> tuple[MutationEcologyReport, dict[str, Any]]:
        specs = mutation_specs_from_mapping(mutants)
        test_cases = mutation_tests_from_mapping(tests)
        target = str(mutants.get("target", "path_normalizer"))
        baseline = str(mutants.get("baseline_behavior", "exact_prefix"))
        claim_id = str(mutants.get("claim_id", "CLAIM-PATH-NORMALIZATION-EXACT-PREFIX"))

        campaign = MutationCampaignEngine().run(specs, test_cases, target=target, baseline_behavior=baseline)
        counterexamples = CounterexampleForge().search(
            specs,
            campaign.surviving_mutant_ids,
            seeds,
            baseline_behavior=baseline,
            claim_id=claim_id,
            property_id="PROP-EXACT-ONE-PREFIX",
        )
        metamorphic = MetamorphicEngine().evaluate(
            contracts_from_mapping(contracts),
            [baseline, *[item.behavior for item in specs if item.behavior != "unknown_behavior"]],
        )
        corpus = tuple(sorted(set(
            [test.input_value for test in test_cases]
            + [str(value) for value in seeds.get("explicit", [])]
            + [item.minimized_input for item in counterexamples.counterexamples]
        )))
        differential = DifferentialOracle().compare(
            reference_behavior=baseline,
            candidate_behaviors=[item.behavior for item in specs if item.behavior != "unknown_behavior"],
            corpus=corpus,
            claim_id=claim_id,
        )
        mminus = MMinusCompiler().compile(counterexamples.counterexamples)
        resolved_survivors = {item.mutant_id for item in counterexamples.counterexamples}
        unresolved = tuple(sorted(set(campaign.surviving_mutant_ids) - resolved_survivors))
        proof_debt_delta = round(float(len(unresolved) * 3 + campaign.survived * 1.5 - len(counterexamples.counterexamples) * 1.0), 6)
        agents = (
            EcologyAgentResult("MutationPredator", "declarative mutants", len(specs), campaign.killed, (campaign.campaign_id,)),
            EcologyAgentResult("CounterexampleForge", "surviving mutants", max(1, counterexamples.candidates_evaluated), len(counterexamples.counterexamples), (counterexamples.report_id,)),
            EcologyAgentResult("MetamorphicHunter", "claim relations", metamorphic.passed_checks + metamorphic.failed_checks, metamorphic.failed_checks, (metamorphic.report_id,)),
            EcologyAgentResult("DifferentialHunter", "reference divergences", len(corpus), len(differential.divergences), (differential.report_id,)),
            EcologyAgentResult("MMinusCompiler", "permanent memory candidates", len(counterexamples.counterexamples), len(mminus.rules), (mminus.compilation_id,)),
        )
        report = MutationEcologyReport(
            campaign_id=campaign.campaign_id,
            counterexample_report_id=counterexamples.report_id,
            metamorphic_report_id=metamorphic.report_id,
            differential_report_id=differential.report_id,
            mminus_compilation_id=mminus.compilation_id,
            agents=agents,
            unresolved_survivors=unresolved,
            proof_debt_delta=proof_debt_delta,
        )
        artifacts = {
            "campaign": campaign.to_dict(),
            "counterexamples": counterexamples.to_dict(),
            "metamorphic": metamorphic.to_dict(),
            "differential": differential.to_dict(),
            "mminus": mminus.to_dict(),
            "ecology": report.to_dict(),
        }
        return report, artifacts
