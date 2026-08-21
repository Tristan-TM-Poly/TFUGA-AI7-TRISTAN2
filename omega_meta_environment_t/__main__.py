from __future__ import annotations

import json

from .core import (
    EnvironmentalState,
    EnvironmentalTransformationGenome,
    EvidenceContract,
    EvidenceStatus,
    ResidualKind,
    ResidualPassport,
)
from .oak import audit


def fixture() -> EnvironmentalTransformationGenome:
    state = EnvironmentalState(
        state_id="urban-watershed-001",
        scale="municipal-watershed",
        observed_at="2026-08-21",
        indicators={"runoff_index": 1.0, "canopy_fraction": 0.22},
        provenance=("demo:synthetic-fixture",),
    )
    residual = ResidualPassport(
        residual_id="R-WATER-001",
        kind=ResidualKind.WATER,
        magnitude=1.0,
        unit="normalized_index",
        origin="impervious_surface",
        transformation="stormwater routing",
        destination="downstream receiving waters",
        spatial_boundary="municipal watershed + downstream receiver",
        temporal_boundary="storm event to seasonal recovery",
        uncertainty=0.25,
        affected_entities=("residents", "aquatic habitat"),
    )
    evidence = EvidenceContract(
        claim_id="C-001",
        claim="Pilot should reduce peak runoff relative to declared baseline.",
        status=EvidenceStatus.MEASURED,
        sources=("demo:synthetic-measurement-plan",),
        boundary="pilot catchment + downstream receiver",
        baseline="pre-pilot runoff index",
        falsifier="no reduction or adverse downstream residual beyond threshold",
    )
    return EnvironmentalTransformationGenome(
        transformation_id="T-ENV-R01-DEMO",
        state_before=state,
        goal="reduce peak runoff without exporting hidden residuals",
        mechanism="bounded pilot of permeable surface and retention",
        place="synthetic municipality",
        time_horizon="one hydrologic season",
        affected_entities=("residents", "aquatic habitat"),
        residuals=(residual,),
        evidence=(evidence,),
        reversibility=0.7,
        authority_confirmed=True,
        monitoring_required=True,
        local_scope="pilot catchment",
        global_scope="watershed + upstream/downstream supply chain boundary",
    )


def main() -> None:
    report = audit(fixture())
    print(json.dumps({
        "transformation_id": report.transformation_id,
        "passed": report.passed,
        "genome_digest": report.genome_digest,
        "report_digest": report.report_digest,
        "findings": [f.__dict__ for f in report.findings],
        "oak_boundary": {
            "simulation_is_reality": False,
            "software_pass_is_scientific_validation": False,
            "compensation_is_restoration": False,
            "local_pass_is_global_pass": False,
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
