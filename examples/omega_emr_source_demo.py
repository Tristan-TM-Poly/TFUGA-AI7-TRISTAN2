"""Reproducible low-power visible-source planning example."""

from __future__ import annotations

import json

from omega_emr_source_t import SpectrumTarget, audit_plan, compile_source


def main() -> None:
    target = SpectrumTarget(
        center_frequency_hz=5e14,
        bandwidth_hz=2e13,
        power_w=1e-3,
        coherence="low",
        polarization="unpolarized",
        environment="shielded_lab",
        max_prototype_tier="low_power_benchtop",
    )
    plan = compile_source(target)
    oak = audit_plan(plan)
    print(
        json.dumps(
            {
                "spectral_region": plan.spectral_region,
                "safety_status": plan.safety_status,
                "oak_status": oak.status,
                "recommended": [
                    candidate.to_dict() for candidate in plan.recommended[:3]
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
