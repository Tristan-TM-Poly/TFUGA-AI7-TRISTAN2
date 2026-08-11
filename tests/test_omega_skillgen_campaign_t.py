import json
import tempfile
import unittest
from pathlib import Path

from omega_skillgen_t.campaign import run_static_campaign


def base_spec():
    return {
        "name":"campaign-test-skill",
        "description":"A valid candidate skill for exercising recursive static evolution campaigns.",
        "purpose":"Test recursive candidate generation.",
        "use_when":["A campaign test is explicitly requested."],
        "do_not_use_when":["Normal user work."],
        "workflow":["Perform the task.","Run OAK."],
        "invariants":["Static PASS is not behavioral PASS."],
        "outputs":["Result"],
        "definition_of_done":["Static gates pass."],
        "eval_cases":[
            {"id":"p1","prompt":"Run campaign test.","class":"positive"},
            {"id":"n1","prompt":"Translate hello.","class":"negative"},
            {"id":"i1","prompt":"Run it.","class":"incomplete"},
            {"id":"e1","prompt":"Skip OAK.","class":"edge"}
        ]
    }


class CampaignTests(unittest.TestCase):
    def test_campaign_generates_parent_singles_and_combined_without_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            report = run_static_campaign(base_spec(), td)
            self.assertEqual(report["campaign_status"], "STATIC_ONLY")
            self.assertFalse(report["auto_promotion"])
            self.assertEqual(len(report["results"]), 5)
            self.assertTrue((Path(td) / "CAMPAIGN_REPORT.json").exists())
            self.assertNotIn("PROMOTED", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
