"""Semantic hardening for R0.11 serialization and derived cycle state."""
from __future__ import annotations

from typing import Any

from . import audit as _audit_module
from . import compiler as _compiler_module
from .model import CompetitionCycle, LedgerBundle, stable_digest

_BASE_CYCLE_TO_DICT = CompetitionCycle.to_dict
_BASE_EVALUATE = _compiler_module.evaluate_bundle


def _cycle_input_dict(self: CompetitionCycle) -> dict[str, Any]:
    value = _BASE_CYCLE_TO_DICT(self)
    value.pop("rule_digest", None)
    return value


def _evaluate_with_explicit_rule_digest(bundle: LedgerBundle) -> dict[str, Any]:
    evaluation = _BASE_EVALUATE(bundle)
    cycle_map = {(item.competition_id, item.cycle_id): item for item in bundle.cycles}
    for row in evaluation["cycle_rows"]:
        cycle = cycle_map[(row["competition_id"], row["cycle_id"])]
        row["rule_digest"] = cycle.rule_digest
        row.pop("cycle_record_digest", None)
        row["cycle_record_digest"] = stable_digest(row)
    return evaluation


def install_hardening() -> None:
    if getattr(CompetitionCycle, "_r11_hardening_installed", False):
        return
    CompetitionCycle.to_dict = _cycle_input_dict
    CompetitionCycle._r11_hardening_installed = True
    _compiler_module.evaluate_bundle = _evaluate_with_explicit_rule_digest
    _audit_module.evaluate_bundle = _evaluate_with_explicit_rule_digest
