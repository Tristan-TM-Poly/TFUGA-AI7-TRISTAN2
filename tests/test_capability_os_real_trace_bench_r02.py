import json
import unittest
from pathlib import Path

from omega_capability_os_t.real_trace_bench import (
    TraceCase,
    governed_policy,
    naive_local_policy,
    replay_policy_benchmark,
)


FIXTURE = Path(__file__).parent / "fixtures" / "capability_os_pr501_508_trace.json"


class CapabilityOSRealTraceBenchR02Tests(unittest.TestCase):
    def load_cases(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return tuple(TraceCase.from_dict(item) for item in payload["cases"])

    def test_frozen_trace_is_exact_pr501_to_pr508(self):
        cases = self.load_cases()
        self.assertEqual([case.source_pr for case in cases], list(range(501, 509)))
        self.assertTrue(all(case.evidence_class == "repository_history" for case in cases))

    def test_governed_policy_beats_naive_local_pass_on_observed_history(self):
        report = replay_policy_benchmark(self.load_cases())
        self.assertEqual(report.decision, "PASS")
        self.assertGreater(report.governed_accuracy, report.naive_accuracy)
        self.assertGreater(report.match_delta, 0.0)
        self.assertEqual(report.regressions, ())
        self.assertGreaterEqual(report.avoided_premature_promotions, 1)

    def test_local_pass_alone_collapses_all_cases_to_promote(self):
        cases = self.load_cases()
        self.assertTrue(all(naive_local_policy(case) == "PROMOTE" for case in cases))
        self.assertTrue(any(governed_policy(case) == "CONTINUE" for case in cases))
        self.assertTrue(any(governed_policy(case) == "CRYSTALLIZE" for case in cases))

    def test_authority_widening_fails_closed(self):
        case = TraceCase("authority-case", 0, True, False, True, "HOLD")
        self.assertEqual(governed_policy(case), "HOLD")

    def test_empty_trace_holds(self):
        report = replay_policy_benchmark(())
        self.assertEqual(report.decision, "HOLD")
        self.assertEqual(report.regressions, ("missing_trace_cases",))


if __name__ == "__main__":
    unittest.main()
