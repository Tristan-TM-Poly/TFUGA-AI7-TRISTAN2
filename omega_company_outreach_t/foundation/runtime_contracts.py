from __future__ import annotations

from typing import Any, Callable, Mapping


class _LegacyCompanyUnitResolver:
    """Callable compatibility adapter without function-descriptor binding.

    Assigning a plain function into a class-like namespace can turn that
    function into a bound method. A callable instance has no descriptor
    behavior, so the legacy string is always received as the sole argument.
    """

    def __init__(
        self,
        *,
        members_by_value: Mapping[str, Any],
        aliases: Mapping[str, str],
        canonicalization_error: type[Exception],
    ) -> None:
        self._members_by_value = dict(members_by_value)
        self._aliases = dict(aliases)
        self._canonicalization_error = canonicalization_error

    def __call__(self, value: Any) -> Any:
        normalized = " ".join(str(value).strip().split()).casefold()
        normalized = self._aliases.get(normalized, normalized)
        member = self._members_by_value.get(normalized)
        if member is None:
            raise self._canonicalization_error(
                f"unknown legacy company_unit: {value!r}; "
                f"expected one of {sorted(self._members_by_value)}"
            )
        return member


def apply_runtime_contracts(
    *,
    opportunity_class: type[Any],
    event_store_class: type[Any],
    canonicalization_error: type[Exception],
    migration_module: Any | None = None,
    company_unit_class: type[Any] | None = None,
) -> None:
    """Apply cross-module contracts after foundation modules are loaded.

    Contracts:

    1. The strategic score is the calibrated signal score. Bayesian conversion
       probability remains separate in ``expected_pipeline_value_cad`` and must
       not be multiplied into the score a second time.
    2. ``append_new`` audits the persistent store before parsing aggregate
       history. Any malformed or tampered row therefore produces one stable
       invalid-store error instead of leaking a parser-specific exception.
    3. R0.2 company identifiers are mapped explicitly to R1.0 enum members by
       a callable object that cannot be converted into a bound method.
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
        migration_module.CompanyUnit = _LegacyCompanyUnitResolver(
            members_by_value=members_by_value,
            aliases=aliases,
            canonicalization_error=canonicalization_error,
        )
