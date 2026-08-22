from omega_morphogenesis import EpistemicStatus, Residual
from omega_research_civilization import ClaimRecord, ResearchCivilizationKernel


kernel = ResearchCivilizationKernel()
plan = kernel.compile(
    "Which experiment best distinguishes two competing models?",
    [Residual("model-disagreement", 1.0, 1.0, 0.8, 1.0, downstream_leverage=1.2)],
    complexity_signal=0.8,
)

claim = ClaimRecord(
    claim_id="example-observation",
    statement="The discriminating measurement was observed.",
    producer_id="vt-generator",
    falsifier_id="vt-falsifier",
    verifier_id="independent-verifier",
    output_status=EpistemicStatus.OBSERVED,
    evidence_status=EpistemicStatus.OBSERVED,
    provenance=("example://dataset/hash",),
    tests=("example-replication-protocol",),
)

seed = kernel.distill(plan, [claim])
rebuilt = kernel.regenerate(seed)

print("plan:", plan.digest())
print("materialized:", [u.unit_id for u in plan.materialized_units()])
print("lazy:", [u.unit_id for u in plan.potential_units()])
print("seed:", seed.digest())
print("closure:", kernel.regeneration_closure(plan, rebuilt))
