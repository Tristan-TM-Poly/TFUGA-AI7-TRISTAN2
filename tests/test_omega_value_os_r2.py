from __future__ import annotations

import unittest

from omega_value_os.book0 import (
    EconomicBOOK0,
    ablate_book0,
    future_work_annihilation,
    regeneration_passes,
    regeneration_receipt,
)
from omega_value_os.experiments import (
    ExperimentCandidate,
    minimum_sufficient_experiment,
    pricing_tournament,
    standard_price_mutations,
)
from omega_value_os.meta_economy import (
    EconomicGenome,
    RepresentationCandidate,
    compile_economic_genomes,
    meta_generation_allowed,
    mutate_economic_genome,
    representation_tournament,
)


class MetaEconomyTests(unittest.TestCase):
    def seed(self) -> EconomicGenome:
        return EconomicGenome(
            name="subscription_seed",
            actors=("member", "provider"),
            value_objects=("verified_capability",),
            capabilities=("analysis",),
            evidence=("retention",),
            exchange_mechanisms=("checkout",),
            pricing_mechanisms=("flat",),
            revenue_mechanisms=("subscription",),
        )

    def test_population_is_finite_and_keeps_no_action(self) -> None:
        population = compile_economic_genomes(
            self.seed(),
            ({"name": f"candidate_{index}"} for index in range(100)),
            max_candidates=5,
        )
        self.assertEqual(len(population), 5)
        self.assertTrue(population[0].is_no_action)
        self.assertEqual(population[0].name, "NO_ACTION")

    def test_meta_candidate_cannot_execute_or_self_approve(self) -> None:
        candidate = mutate_economic_genome(
            self.seed(),
            mutation="try_usage_pricing",
            changes={"pricing_mechanisms": ("usage",)},
        )
        self.assertFalse(candidate.executable)
        self.assertTrue(candidate.requires_independent_evaluation)

    def test_meta_stop_rule_and_depth_cap(self) -> None:
        self.assertFalse(
            meta_generation_allowed(
                verified_gain=0.2,
                complexity_debt=0.15,
                risk_debt=0.1,
                meta_depth=1,
            )
        )
        self.assertFalse(
            meta_generation_allowed(
                verified_gain=10.0,
                complexity_debt=0.1,
                risk_debt=0.1,
                meta_depth=4,
                max_meta_depth=4,
            )
        )
        self.assertTrue(
            meta_generation_allowed(
                verified_gain=1.0,
                complexity_debt=0.1,
                risk_debt=0.1,
                meta_depth=1,
            )
        )

    def test_representation_tournament_penalizes_complexity(self) -> None:
        ranked = representation_tournament(
            (
                RepresentationCandidate("simple", 0.8, 0.4, 0.1),
                RepresentationCandidate("bloated", 1.0, 0.4, 10.0),
            )
        )
        self.assertEqual(ranked[0].name, "simple")


class ExperimentTests(unittest.TestCase):
    def test_minimum_sufficient_experiment_chooses_cheapest_qualified(self) -> None:
        chosen = minimum_sufficient_experiment(
            (
                ExperimentCandidate("cheap_weak", 1, 1.0, 0.3, 0.8),
                ExperimentCandidate("expensive", 20, 0.9, 0.9, 0.9),
                ExperimentCandidate("minimal", 5, 0.9, 0.8, 0.7),
            ),
            minimum_discrimination=0.7,
        )
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.name, "minimal")

    def test_price_mutations_are_simulation_only(self) -> None:
        mutations = standard_price_mutations()
        self.assertTrue(mutations)
        self.assertTrue(all(not mutation.executable for mutation in mutations))

    def test_tournament_uses_multiple_dimensions(self) -> None:
        mutations = standard_price_mutations()[:2]
        ranked = pricing_tournament(
            {
                "half_price": {"conversion": 1.0, "margin": 0.1, "trust": 0.9},
                "lower_price": {"conversion": 0.8, "margin": 0.8, "trust": 0.9},
            },
            mutations,
        )
        self.assertEqual(ranked[0].mutation.name, "lower_price")


class Book0Tests(unittest.TestCase):
    def book(self) -> EconomicBOOK0:
        return EconomicBOOK0(
            capabilities=frozenset({"checkout", "entitlement", "analytics"}),
            user_problems=frozenset({"access"}),
            offer_grammar=frozenset({"subscription"}),
            pricing_rules=frozenset({"evidence_bounded"}),
            revenue_mechanisms=frozenset({"subscription"}),
            evidence_rules=frozenset({"claim_scope_lte_evidence_scope"}),
            authority_rules=frozenset({"automation_ne_authority"}),
            dependencies=frozenset({"payment_adapter"}),
            recovery_probes=frozenset({"can_restore_entitlement"}),
        )

    def test_regeneration_is_functional_not_identity_claim(self) -> None:
        receipt = regeneration_receipt(
            required_capabilities=("checkout", "entitlement"),
            recovered_capabilities=("checkout", "entitlement", "analytics"),
            probe_residual=0.0,
        )
        self.assertTrue(regeneration_passes(receipt))
        self.assertFalse(receipt.identity_claimed)

    def test_missing_capability_fails_full_regeneration(self) -> None:
        receipt = regeneration_receipt(
            required_capabilities=("checkout", "entitlement"),
            recovered_capabilities=("checkout",),
            probe_residual=0.0,
        )
        self.assertFalse(regeneration_passes(receipt))
        self.assertEqual(receipt.missing_capabilities, frozenset({"entitlement"}))

    def test_ablation_preserves_required_capabilities(self) -> None:
        book, removed = ablate_book0(
            self.book(),
            removable_capabilities=("analytics", "entitlement"),
            required_capabilities=("checkout", "entitlement"),
        )
        self.assertEqual(removed, ("analytics",))
        self.assertIn("entitlement", book.capabilities)

    def test_future_work_annihilation_pays_verification_cost(self) -> None:
        self.assertEqual(
            future_work_annihilation(
                baseline_future_work=100,
                residual_future_work=20,
                verification_cost=10,
            ),
            70,
        )


if __name__ == "__main__":
    unittest.main()
