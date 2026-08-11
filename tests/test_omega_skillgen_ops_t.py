import tempfile
import unittest
from pathlib import Path

from omega_skillgen_t.genome import skill_genome, genome_similarity, dedup_report
from omega_skillgen_t.telemetry import behavioral_summary, split_memory, write_memory_ledgers


def spec(name, extra=""):
    return {
        "name":name,
        "use_when":["Audit a research skill " + extra],
        "do_not_use_when":["Translation"],
        "workflow":["Compare baseline.","Run OAK."],
        "invariants":["Static pass is not proof."],
        "outputs":["Audit report"],
        "eval_cases":[{"class":"positive"},{"class":"negative"},{"class":"incomplete"},{"class":"edge"}]
    }


class OpsTests(unittest.TestCase):
    def test_genome_similarity_and_dedup(self):
        a=spec("a"); b=spec("b"); c=spec("c","with unrelated astronomy expansion")
        self.assertEqual(len(skill_genome(a)["fingerprint"]),64)
        self.assertGreater(genome_similarity(a,b)["score"],0.9)
        self.assertEqual(len(dedup_report([a,b],0.8)["candidate_duplicate_pairs"]),1)
        self.assertLessEqual(genome_similarity(a,c)["score"],genome_similarity(a,b)["score"])

    def test_behavioral_telemetry_to_memory(self):
        payload={"skill":"x","version":"1","results":[
            {"eval_id":"p1","passed":True,"class":"positive","must_pass":True,"dimensions":{"quality":0.9},"evidence":"trace-1"},
            {"eval_id":"a1","passed":False,"class":"adversarial","must_pass":True,"failure_mode":"overclaim","repair":"strengthen guard","evidence":"trace-2"}
        ]}
        summary=behavioral_summary(payload)
        self.assertFalse(summary["behavioral_eval_pass"])
        self.assertEqual(summary["must_pass_failures"],["a1"])
        split=split_memory(payload)
        self.assertEqual(len(split["M_PLUS"]),1)
        self.assertEqual(len(split["M_MINUS"]),1)
        with tempfile.TemporaryDirectory() as td:
            write_memory_ledgers(payload,td)
            self.assertTrue((Path(td)/"M_PLUS.jsonl").exists())
            self.assertTrue((Path(td)/"M_MINUS.jsonl").exists())
            self.assertTrue((Path(td)/"BEHAVIORAL_SUMMARY.json").exists())


if __name__=="__main__":
    unittest.main()
