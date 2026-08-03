"""Executable demonstration of Ω-VLA-T∞² R0.2-MAX."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import numpy as np

from omega_vla_t.r02 import (
    CampaignConfig,
    FrontierCodec,
    TheoremFactory,
    analyze_residual,
    audit_max_system,
    run_campaign,
    spectral_dna,
)


def main() -> None:
    codec = FrontierCodec()
    factory = TheoremFactory()
    sampled = [
        factory.generate(address).to_dict()
        for address in codec.iter_sample(3, seed=2026)
    ]

    matrix = np.array(
        [
            [2.0, -1.0, 0.0],
            [1.0, 2.0, -0.5],
            [0.0, 0.5, 1.0],
        ]
    )
    dna = spectral_dna(matrix, pseudospectral_points=6)

    axis = np.linspace(0.0, 10.0 * np.pi, 512)
    residual = np.sin(axis) + 0.15 * np.sin(7.0 * axis)
    residual_profile = analyze_residual(residual)

    with tempfile.TemporaryDirectory(prefix="omega-vla-r02-") as temporary:
        output_dir = Path(temporary) / "campaign"
        campaign = run_campaign(
            CampaignConfig(
                work_items=129,
                seed=2026,
                initial_batch=16,
                min_batch=8,
                max_batch=64,
                records_per_shard=32,
                output_dir=str(output_dir),
            )
        )
        oak = audit_max_system(seed=2026, campaign_items=129)
        payload = {
            "logical_frontier_cells": codec.size,
            "sample_cells": sampled,
            "spectral_dna": dna.to_dict(),
            "residual_profile": residual_profile.to_dict(),
            "campaign": campaign.to_dict(),
            "oak": oak.to_dict(),
            "claim_boundary": (
                "generated cells are research candidates; no theorem, formal proof "
                "or scientific validation is claimed"
            ),
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
