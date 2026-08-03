from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def apply_runtime_contracts(
    *,
    opportunity_class: type[Any],
    event_store_class: type[Any],
    canonicalization_error: type[Exception],
) -> None:
    """Apply cross-module contracts after the foundation modules are loaded.

    Two contracts intentionally live at the package boundary:

    1. The strategic score is the calibrated signal score. Bayesian conversion
       probability remains separate in ``expected_pipeline_value_cad`` and must
       not be multiplied into the score a second time.
    2. ``append_new`` audits the persistent store before parsing aggregate
       history. Any malformed or tampered row therefore produces one stable
       invalid-store error instead of leaking a parser-specific exception.

    Keeping these policies at the boundary makes the separation explicit while
    the R1.0 package remains stacked above R0.2. A later refactor can move the
    bodies into their owning classes without changing the public contract.
    """

    if getattr(opportunity_class, "_omega_score_contract", False) is False:
        def strategic_score(self: Any) -> int:
            return int(self.signals.score_100)

        opportunity_class.strategic_score = property(strategic_score)
        opportunity_class._omega_score_contract = True

    if getattr(event_store_class, "_omega_preappend_contract", False) is False:
        original_append_new: Callable[..., Any] = event_store_class.append_new

        def audited_append_new(self: Any, *args: Any, **kwargs: Any) -> Any:
            audit = self.audit()
            if not audit.valid:
                raise canonicalization_error("cannot append to an invalid event store")
            return original_append_new(self, *args, **kwargs)

        event_store_class.append_new = audited_append_new
        event_store_class._omega_preappend_contract = True
