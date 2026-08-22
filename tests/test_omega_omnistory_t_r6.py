from dataclasses import replace

import pytest

from omega_omnistory_t import (
    CanonFact,
    CanonStatus,
    CausalEvent,
    GeneratorRegistry,
    GeneratorSpec,
    ImprovementCandidate,
    NarrativeResidual,
    PromotionDecision,
    automation_value,
    canonical_digest,
    causal_cycle,
    continuity_errors,
    crystallization_decision,
    default_book0,
    derive_residuals,
    eighth_fire_story,
    make_crystal,
    meta_depth_allowed,
    projection_plan,
    propose_generator_from_residual,
    rank_improvements,
    regeneration_receipt,
)


def test_reference_story_is_valid():
    assert continuity_errors(eighth_fire_story()) == []


def test_reference_story_projects_to_manga_and_anime():
    story = eighth_fire_story()
    manga = projection_plan(story, "manga")
    anime = projection_plan(story, "anime")
    assert manga["story_id"] == anime["story_id"]
    assert manga["backend"] == "manga"
    assert anime["backend"] == "anime"
    assert manga["event_order"] == anime["event_order"]


def test_unknown_backend_fails_closed():
    with pytest.raises(ValueError):
        projection_plan(eighth_fire_story(), "unauthorized-backend")


def test_causal_cycle_is_detected():
    story = eighth_fire_story()
    first, second = story.events
    cyclic_first = replace(first, causes=(second.event_id,))
    cyclic = replace(story, events=(cyclic_first, second))
    assert causal_cycle(cyclic)
    assert any("causal_graph: cycle" in error for error in continuity_errors(cyclic))


def test_unknown_actor_is_rejected():
    story = eighth_fire_story()
    broken = replace(story.events[0], actors=("UNKNOWN",))
    candidate = replace(story, events=(broken, story.events[1]))
    assert any("unknown actors" in error for error in candidate.validate())


def test_ability_requires_constraint():
    story = eighth_fire_story()
    broken_character = replace(story.characters[0], constraints=())
    candidate = replace(story, characters=(broken_character, story.characters[1]))
    assert any("abilities require constraints" in error for error in candidate.validate())


def test_irreversible_event_without_consequence_creates_residual():
    story = eighth_fire_story()
    broken_event = replace(story.events[0], consequences=())
    candidate = replace(story, events=(broken_event, story.events[1]))
    residuals = derive_residuals(candidate)
    assert residuals[0].residual_id == "R-CONSEQUENCE-EV-001"
    assert residuals[0].proposed_generator == "ConsequenceCompiler"


def test_contradicted_fact_creates_high_severity_residual():
    story = eighth_fire_story()
    contradicted = replace(story.canon[0], status=CanonStatus.CONTRADICTED)
    candidate = replace(story, canon=(contradicted,))
    residuals = derive_residuals(candidate)
    assert residuals[0].severity == 5
    assert residuals[0].domain == "canon"


def test_retcon_requires_prior_fact():
    story = eighth_fire_story()
    retcon = CanonFact("FACT-RETCON", "A revised fact.", CanonStatus.RETCON, ("review",), ())
    candidate = replace(story, canon=story.canon + (retcon,))
    assert any("RETCON requires" in error for error in continuity_errors(candidate))


def test_generator_cannot_be_its_own_judge():
    spec = GeneratorSpec("G", "Generate", ("StoryIR",), ("scene",), ("G",))
    with pytest.raises(ValueError, match="Generator != Judge"):
        GeneratorRegistry((spec,))


def test_residual_can_propose_generator():
    residual = NarrativeResidual("R1", "dialogue", "scene", "Voices converge.", 3, ("case-1",), None)
    spec = propose_generator_from_residual(residual)
    assert spec.generator_id.startswith("GeneratorFor-dialogue")
    assert spec.experimental is True


def test_registry_builds_minimum_greedy_coalition():
    registry = GeneratorRegistry((
        GeneratorSpec("cheap-a", "A", ("StoryIR",), ("a",), ("judge-a",), 1),
        GeneratorSpec("cheap-b", "B", ("StoryIR",), ("b",), ("judge-b",), 1),
        GeneratorSpec("expensive-both", "AB", ("StoryIR",), ("a", "b"), ("judge-ab",), 5),
    ))
    assert registry.coalition_for(("a", "b")) == ("cheap-a", "cheap-b")


def test_meta_depth_requires_gain_above_complexity_and_risk():
    assert meta_depth_allowed(4.0, 1.0, 1.0)
    assert not meta_depth_allowed(2.0, 1.0, 1.0)


def test_automation_value_rewards_future_work_and_reliability():
    assert automation_value(10, 0.9, 2, 1) == pytest.approx(3.0)
    assert automation_value(10, 0.9, 0, 0) == 0.0


def test_improvement_ranking_uses_gain_per_cost_risk_complexity():
    weak = ImprovementCandidate("weak", "dialogue", "x", 2, 2, 1, 1, "B")
    strong = ImprovementCandidate("strong", "dialogue", "y", 4, 1, 1, 1, "B")
    assert rank_improvements((weak, strong))[0].improvement_id == "strong"


def test_crystallization_is_fail_closed():
    assert crystallization_decision(
        verified_gain=3, benchmark_passed=True, rollback_defined=True, complexity_delta=1
    ) is PromotionDecision.PROMOTE
    assert crystallization_decision(
        verified_gain=3, benchmark_passed=False, rollback_defined=True, complexity_delta=1
    ) is PromotionDecision.KEEP_EXPERIMENTAL
    assert crystallization_decision(
        verified_gain=3, benchmark_passed=True, rollback_defined=True,
        complexity_delta=1, known_regression=True
    ) is PromotionDecision.DESTROY


def test_crystal_requires_evidence_benchmark_and_rollback():
    crystal = make_crystal("C1", "continuity", "omega_omnistory_t.engine", ("tests",), ("R6-continuity",), "revert commit")
    assert crystal.validate() == []
    with pytest.raises(ValueError):
        make_crystal("C2", "continuity", "x", (), ("B",), "rollback")


def test_book0_is_complete_and_deterministic():
    book0 = default_book0()
    assert book0.validate() == []
    assert canonical_digest(book0.__dict__) == canonical_digest(book0.__dict__)


def test_regeneration_receipt_measures_capability_closure():
    story = eighth_fire_story()
    receipt = regeneration_receipt(story, ("story-ir", "continuity", "canon-ledger"))
    assert receipt.closure == pytest.approx(3 / 7)
    full = regeneration_receipt(story, receipt.expected_capabilities)
    assert full.closure == 1.0


def test_story_digest_changes_when_canon_changes():
    story = eighth_fire_story()
    receipt_a = regeneration_receipt(story, ("story-ir",))
    changed_fact = replace(story.canon[0], statement="A materially different canon statement.")
    changed = replace(story, canon=(changed_fact,))
    receipt_b = regeneration_receipt(changed, ("story-ir",))
    assert receipt_a.story_digest != receipt_b.story_digest
