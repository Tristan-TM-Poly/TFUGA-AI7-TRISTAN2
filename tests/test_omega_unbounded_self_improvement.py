from __future__ import annotations

import json

from omega_unbounded_t import (
    ControllerVariant,
    SelfImprovementLab,
    SelfImprovementScenario,
    iter_variants_jsonl,
)


def _scenarios():
    return (
        SelfImprovementScenario("small", 1_200, 32, 16),
        SelfImprovementScenario("medium", 3_600, 64, 32),
        SelfImprovementScenario("large", 7_200, 128, 64),
    )


def test_self_improvement_proposes_a_resource_aware_candidate(tmp_path):
    report = SelfImprovementLab(
        tmp_path,
        scenarios=_scenarios(),
        minimum_improvement_ratio=0.01,
    ).run()

    assert report.baseline.completed is True
    assert report.decision.status == "promotion_proposed"
    assert report.decision.selected == "mminus-capacity-redesign"
    assert report.decision.improvement_ratio > 0.01
    assert report.decision.requires_human_approval is True
    assert report.decision.remote_mutations == 0
    assert report.no_source_mutation is True
    assert report.no_auto_merge is True

    promotion = json.loads((tmp_path / "promotion-plan.json").read_text(encoding="utf-8"))
    judge = promotion["evidence"]["judge"]
    assert judge["type"] == "resource_aware_oak_judge"
    assert judge["overshoot_penalty_weight"] > 0
    assert judge["selected_capacity_overshoot_ratio"] <= (
        judge["baseline_capacity_overshoot_ratio"]
        * judge["maximum_overshoot_multiplier"]
    )
    assert promotion["apply"]["automatic"] is False
    assert promotion["apply"]["source_mutations"] == 0
    assert promotion["apply"]["remote_mutations"] == 0
    assert promotion["apply"]["merge"] is False
    assert (tmp_path / "m_plus.jsonl").exists()
    assert (tmp_path / "candidate-results.jsonl").exists()

    negative_memory = (tmp_path / "self_improvement_m_minus.jsonl").read_text(
        encoding="utf-8"
    )
    assert "capacity overshoot exceeded the permitted multiplier" in negative_memory


def test_duplicate_and_regressing_candidates_become_negative_memory(tmp_path):
    candidates = (
        ControllerVariant(name="same-policy-different-name"),
        ControllerVariant(name="slow-redesign", redesign_factor=1.1),
    )
    report = SelfImprovementLab(
        tmp_path,
        scenarios=_scenarios(),
        minimum_improvement_ratio=0.01,
    ).run(candidates)

    assert report.decision.status == "no_promotion"
    assert report.decision.selected is None
    records = [
        json.loads(line)
        for line in (tmp_path / "self_improvement_m_minus.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(item["event"] == "candidate_duplicate" for item in records)
    assert any(item["event"] == "candidate_not_promoted" for item in records)


def test_external_candidate_stream_is_consumed_until_exhaustion(tmp_path):
    candidate_file = tmp_path / "candidates.jsonl"
    candidate_file.write_text(
        "\n".join(
            (
                json.dumps({"name": "redesign-3x", "redesign_factor": 3.0}),
                json.dumps({"name": "redesign-4x", "redesign_factor": 4.0}),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    candidates = tuple(iter_variants_jsonl(candidate_file))
    report = SelfImprovementLab(
        tmp_path / "run",
        scenarios=_scenarios(),
        minimum_improvement_ratio=0.01,
    ).run(iter(candidates))

    assert len(candidates) == 2
    assert len(report.candidates) == 2
    assert report.candidate_stream_exhausted is True
    assert report.no_permanent_candidate_cap is True
