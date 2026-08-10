from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .models import NetworkFingerprint


@dataclass(frozen=True)
class SpecializedNetworkAtlas:
    """Small registry of network fingerprints without anatomical overclaiming."""

    entries: Dict[str, NetworkFingerprint]

    def nearest(self, query: NetworkFingerprint) -> str:
        if not self.entries:
            raise ValueError("atlas is empty")

        def distance(fp: NetworkFingerprint) -> float:
            return sum(
                (a - b) ** 2
                for a, b in (
                    (query.excitation_inhibition_ratio, fp.excitation_inhibition_ratio),
                    (query.recurrence, fp.recurrence),
                    (query.modularity, fp.modularity),
                    (query.delay_dispersion, fp.delay_dispersion),
                    (query.plasticity, fp.plasticity),
                    (query.hierarchy, fp.hierarchy),
                    (query.multiscale_coherence, fp.multiscale_coherence),
                )
            )

        return min(self.entries, key=lambda name: (distance(self.entries[name]), name))


def reference_archetypes() -> SpecializedNetworkAtlas:
    """Synthetic archetypes for software tests, not claims about named brain regions."""

    return SpecializedNetworkAtlas(
        entries={
            "feed_forward": NetworkFingerprint(1.0, 0.10, 0.40, 0.20, 0.30, 0.60, 0.30),
            "recurrent": NetworkFingerprint(1.0, 0.85, 0.55, 0.35, 0.65, 0.50, 0.70),
            "competitive": NetworkFingerprint(0.70, 0.55, 0.75, 0.25, 0.50, 0.45, 0.50),
            "sequence": NetworkFingerprint(1.10, 0.45, 0.60, 0.65, 0.55, 0.70, 0.60),
        }
    )
