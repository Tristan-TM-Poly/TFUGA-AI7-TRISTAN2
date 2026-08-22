import unittest

from omega_value_os import (
    EconomicState,
    RevenueMode,
    RevenueStreamMetrics,
    Shock,
    apply_shock,
    platform_concentration,
    prune_candidates,
    revenue_mode_mix,
)


class PortfolioTests(unittest.TestCase):
    def test_platform_concentration_detects_single_platform_dependency(self):
        streams = [
            RevenueStreamMetrics("a", RevenueMode.PASSIVE, 100, 10, 1, "youtube", 0.8),
            RevenueStreamMetrics("b", RevenueMode.MIXED, 100, 10, 2, "youtube", 0.5),
        ]
        self.assertAlmostEqual(platform_concentration(streams), 1.0)

    def test_diversification_reduces_concentration(self):
        one = [RevenueStreamMetrics("a", RevenueMode.PASSIVE, 100, 0, 1, "youtube")]
        two = [
            RevenueStreamMetrics("a", RevenueMode.PASSIVE, 100, 0, 1, "youtube"),
            RevenueStreamMetrics("b", RevenueMode.MIXED, 100, 0, 1, "owned_site"),
        ]
        self.assertLess(platform_concentration(two), platform_concentration(one))

    def test_mode_mix_uses_positive_contribution_margin(self):
        streams = [
            RevenueStreamMetrics("active", RevenueMode.ACTIVE, 100, 0, 5, "direct"),
            RevenueStreamMetrics("passive", RevenueMode.PASSIVE, 100, 0, 1, "owned"),
        ]
        active, passive, mixed = revenue_mode_mix(streams)
        self.assertAlmostEqual(active, 0.5)
        self.assertAlmostEqual(passive, 0.5)
        self.assertEqual(mixed, 0.0)

    def test_prune_candidates_returns_review_flags_not_deletion(self):
        streams = [
            RevenueStreamMetrics("loss", RevenueMode.ACTIVE, 10, 20, 10, "direct"),
            RevenueStreamMetrics("healthy", RevenueMode.MIXED, 100, 20, 2, "owned"),
        ]
        self.assertEqual(prune_candidates(streams), ("loss",))


class EconomicShockTests(unittest.TestCase):
    def test_platform_collapse_is_scenario_not_negative_state(self):
        state = EconomicState(1000, 600, 0.05, 1.0, 0.9)
        result = apply_shock(state, Shock("platform-collapse", revenue_factor=0.2, reach_factor=0.1))
        self.assertEqual(result.after.revenue, 200)
        self.assertEqual(result.after.platform_reach, 0.1)
        self.assertLess(result.surplus_delta, 0)

    def test_trust_is_bounded(self):
        state = EconomicState(100, 50, 0.1, 1.0, 0.95)
        result = apply_shock(state, Shock("trust-up", trust_delta=0.5))
        self.assertEqual(result.after.trust, 1.0)


if __name__ == "__main__":
    unittest.main()
