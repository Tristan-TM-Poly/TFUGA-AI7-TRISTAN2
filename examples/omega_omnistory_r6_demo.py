"""End-to-end deterministic demonstration for Ω-OMNISTORY R6."""
from omega_omnistory_t import (
    GeneratorRegistry,
    derive_residuals,
    eighth_fire_story,
    projection_plan,
    propose_generator_from_residual,
    regeneration_receipt,
)


story = eighth_fire_story()
story.require_valid()

manga = projection_plan(story, "manga")
anime = projection_plan(story, "anime")
residuals = derive_residuals(story)
registry = GeneratorRegistry(tuple(propose_generator_from_residual(r) for r in residuals))
receipt = regeneration_receipt(
    story,
    ("story-ir", "continuity", "canon-ledger", "residual-field", "meta-generation", "crystallization", "regeneration"),
)

print({
    "story": story.story_id,
    "manga_events": manga["event_order"],
    "anime_events": anime["event_order"],
    "residuals": [r.residual_id for r in residuals],
    "generator_registry": registry.ids(),
    "regeneration_closure": receipt.closure,
})
