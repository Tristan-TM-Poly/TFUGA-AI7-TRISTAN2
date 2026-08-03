from __future__ import annotations

from typing import Any, Callable


def apply_runtime_contracts(
    *,
    opportunity_class: type[Any],
    event_store_class: type[Any],
    canonicalization_error: type[Exception],
    migration_module: Any | None = None,
    company_unit_class: type[Any] | None = None,
) -> None:
    """Apply cross-module contracts after the foundation modules are loaded.

    Contracts:

    1. The strategic score is the calibrated signal score. Bayesian conversion
       probability remains separate in ``expected_pipeline_value_cad`` and must
       not be multiplied into the score a second time.
    2. ``append_new`` audits the persistent store before parsing aggregate
       history. Any malformed or tampered row therefore produces one stable
       invalid-store error instead of leaking a parser-specific exception.
    3. R0.2 company identifiers are mapped explicitly to R1.0 enum members.
       The migration path never relies on whichever same-named enum happens to
       be imported first in a stacked package graph.

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

    if migration_module is not None and company_unit_class is not None:
        members_by_value = {
            str(member.value).strip().casefold(): member for member in company_unit_class
        }
        aliases = {
            "parent": "tristan_parent_opco",
            "parent_opco": "tristan_parent_opco",
            "oak": "tristan_oak_systems",
            "software": "tristan_software_labs",
            "research": "tristan_research_foundry",
        }

        def resolve_legacy_company_unit(value: Any) -> Any:
            normalized = " ".join(str(value).strip().split()).casefold()
            normalized = aliases.get(normalized, normalized)
            member = members_by_value.get(normalized)
            if member is None:
                raise canonicalization_error(
                    f"unknown legacy company_unit: {value!r}; "
                    f"expected one of {sorted(members_by_value)}"
                )
            return member

        migration_module.CompanyUnit = resolve_legacy_company_unit
