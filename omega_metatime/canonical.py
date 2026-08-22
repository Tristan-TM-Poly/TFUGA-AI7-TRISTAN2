from __future__ import annotations

from typing import Iterable

from omega_morphogenesis import MorphogenesisKernel

from .core import MetaTimeEngine as _LegacyMetaTimeEngine


class MetaTimeEngine(_LegacyMetaTimeEngine):
    """Public MetaTime engine with generic governance delegated to morphogenesis.

    Temporal metrics/regime logic remains MetaTime-specific. Meta-level admission and
    regeneration closure are canonical kernel responsibilities. The inherited
    implementations remain only as a temporary compatibility surface pending ablation.
    """

    def should_create_meta_level(
        self,
        *,
        verified_out_of_sample_gain: float,
        complexity_cost: float,
        risk_cost: float,
        debt_cost: float,
        expressible_by_current_kernel: bool,
    ) -> bool:
        return MorphogenesisKernel.should_create_meta_level(
            verified_out_of_sample_gain=verified_out_of_sample_gain,
            meta_complexity_cost=(
                max(0.0, complexity_cost)
                + max(0.0, risk_cost)
                + max(0.0, debt_cost)
            ),
            expressible_by_current_kernel=expressible_by_current_kernel,
        )

    @staticmethod
    def regeneration_closure(
        required_components: Iterable[str],
        rebuilt_components: Iterable[str],
    ) -> float:
        return MorphogenesisKernel.regeneration_closure(
            required_components,
            rebuilt_components,
        )
