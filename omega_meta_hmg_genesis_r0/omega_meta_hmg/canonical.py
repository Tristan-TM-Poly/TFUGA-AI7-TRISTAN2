from __future__ import annotations

from omega_morphogenesis import MorphogenesisKernel

from .engine import MetaHMGEngine as _LegacyMetaHMGEngine


class MetaHMGEngine(_LegacyMetaHMGEngine):
    """Public HMG engine with generic meta-admission delegated to morphogenesis.

    HMG-specific representation generation/tournaments, MHT provenance, and bounded
    regeneration remain local. The inherited generic MetaStop implementation is a
    temporary compatibility surface and is not the public governance authority.
    """

    def meta_stop(
        self,
        verified_gain: float,
        regenerability_gain: float,
        transfer_gain: float,
        optionality_gain: float,
        complexity: float,
        risk: float,
        debt: float,
        compute: float,
    ) -> bool:
        benefit = sum(
            max(0.0, value)
            for value in (
                verified_gain,
                regenerability_gain,
                transfer_gain,
                optionality_gain,
            )
        )
        burden = sum(
            max(0.0, value)
            for value in (complexity, risk, debt, compute)
        )
        return MorphogenesisKernel.should_create_meta_level(
            verified_out_of_sample_gain=benefit,
            meta_complexity_cost=burden,
            expressible_by_current_kernel=False,
        )
