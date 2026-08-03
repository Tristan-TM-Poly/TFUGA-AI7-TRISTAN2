"""OAK audits for Ω-VLA-T∞² R0.2-MAX."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .address import FrontierCodec
from .catalogs import CATALOG, Catalog
from .frontier import CampaignConfig, run_campaign
from .residual_intelligence import analyze_residual
from .spectral_dna import spectral_dna
from .theorem_factory import TheoremFactory


@dataclass(frozen=True)
class MaxOAKCheck:
    name: str
    passed: bool
    measured: float | int | str | bool
    expected: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MaxOAKReport:
    system: str
    version: str
    status: str
    checks: tuple[MaxOAKCheck, ...]
    logical_frontier_cells: int
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "version": self.version,
            "status": self.status,
            "passed": self.passed,
            "logical_frontier_cells": self.logical_frontier_cells,
            "checks": [check.to_dict() for check in self.checks],
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_max_system(
    *,
    catalog: Catalog = CATALOG,
    seed: int = 17,
    campaign_items: int = 257,
) -> MaxOAKReport:
    """Run deterministic software-fixture checks; this is not mathematical proof."""

    codec = FrontierCodec(catalog)
    factory = TheoremFactory()
    checks: list[MaxOAKCheck] = []

    summary = catalog.summary()
    checks.append(
        MaxOAKCheck(
            name="catalog_shape",
            passed=(summary["layers"] == 32 and summary["programs"] == 64),
            measured=f"{summary['layers']}x{summary['programs']}",
            expected="32 layers and 64 programs",
        )
    )

    probe_indices = codec.sample_indices(128, seed=seed)
    round_trip_errors = sum(
        codec.encode(codec.decode(index)) != index for index in probe_indices
    )
    checks.append(
        MaxOAKCheck(
            name="address_round_trip",
            passed=round_trip_errors == 0,
            measured=round_trip_errors,
            expected="0 reversible-address errors",
        )
    )

    first = [factory.generate(codec.decode(index)).to_dict() for index in probe_indices]
    second = [factory.generate(codec.decode(index)).to_dict() for index in probe_indices]
    checks.append(
        MaxOAKCheck(
            name="factory_determinism",
            passed=first == second,
            measured=len(first),
            expected="identical repeated generation",
        )
    )

    unsafe_claims = sum(
        bool(cell["theorem_claimed"])
        or cell["status"] in {"FORMALLY_VERIFIED", "CANONICAL"}
        for cell in first
    )
    checks.append(
        MaxOAKCheck(
            name="generated_claim_safety",
            passed=unsafe_claims == 0,
            measured=unsafe_claims,
            expected="0 generated theorem/canon claims",
        )
    )

    config = CampaignConfig(
        work_items=campaign_items,
        seed=seed,
        initial_batch=32,
        min_batch=8,
        max_batch=256,
        min_utility=0.0,
        max_risk=1.0,
    )
    campaign_a = run_campaign(config, catalog=catalog).to_dict()
    campaign_b = run_campaign(config, catalog=catalog).to_dict()
    checks.append(
        MaxOAKCheck(
            name="campaign_determinism",
            passed=campaign_a == campaign_b,
            measured=campaign_a["accepted_cells"],
            expected="byte-equivalent logical payloads after JSON serialization",
        )
    )
    checks.append(
        MaxOAKCheck(
            name="finite_campaign_no_permanent_cap",
            passed=(
                campaign_a["proposed_cells"] == campaign_items
                and campaign_a["permanent_total_cap"] is None
            ),
            measured=campaign_a["proposed_cells"],
            expected=f"{campaign_items} finite work items and permanent_total_cap=null",
        )
    )

    matrix = np.array([[2.0, -1.0], [1.0, 2.0]])
    dna = spectral_dna(matrix, pseudospectral_points=4)
    checks.append(
        MaxOAKCheck(
            name="spectral_dna_fixture",
            passed=(
                dna.numerical_rank == 2
                and np.isfinite(dna.condition_number)
                and dna.spectral_radius > 0.0
                and len(dna.pseudospectral_probe) == 4
            ),
            measured=dna.spectral_radius,
            expected="finite full-rank spectral fixture with four probes",
        )
    )

    residual = np.sin(np.linspace(0.0, 8.0 * np.pi, 256))
    profile = analyze_residual(residual)
    checks.append(
        MaxOAKCheck(
            name="residual_structure_fixture",
            passed=profile.structured,
            measured=profile.classification,
            expected="structured oscillatory or correlated residual",
        )
    )

    passed = all(check.passed for check in checks)
    return MaxOAKReport(
        system="Ω-VLA-T∞²",
        version="R0.2-MAX",
        status=(
            "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_2_MAX"
            if passed
            else "OAK_FAIL_SOFTWARE_RESEARCH_FIXTURES_R0_2_MAX"
        ),
        checks=tuple(checks),
        logical_frontier_cells=codec.size,
    )
