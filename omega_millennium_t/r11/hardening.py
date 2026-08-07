"""Semantic hardening for R0.11 serialization and opportunity policy."""
from __future__ import annotations

from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from . import audit as _audit_module
from . import compiler as _compiler_module
from .model import (
    CompetitionCycle,
    LedgerBundle,
    parse_datetime,
    stable_digest,
)

_BASE_CYCLE_TO_DICT = CompetitionCycle.to_dict
_BASE_EVALUATE = _compiler_module.evaluate_bundle


def _cycle_input_dict(self: CompetitionCycle) -> dict[str, Any]:
    """Keep derived rule digests out of immutable input serialization."""
    value = _BASE_CYCLE_TO_DICT(self)
    value.pop("rule_digest", None)
    return value


def _domain_matches(hostname: str | None, expected_domain: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    expected = expected_domain.lower().rstrip(".")
    return bool(host and expected and (host == expected or host.endswith("." + expected)))


def _url_blockers(url: str, expected_domain: str, label: str) -> list[str]:
    parsed = urlparse(url)
    blockers: list[str] = []
    if parsed.scheme.lower() != "https":
        blockers.append(f"https_required:{label}")
    if not _domain_matches(parsed.hostname, expected_domain):
        blockers.append(f"organizer_domain_mismatch:{label}")
    if parsed.username or parsed.password:
        blockers.append(f"userinfo_forbidden_in_official_url:{label}")
    return blockers


def _cycle_chain_blockers(bundle: LedgerBundle) -> dict[tuple[str, str], list[str]]:
    result: dict[tuple[str, str], list[str]] = defaultdict(list)
    grouped: dict[str, list[CompetitionCycle]] = defaultdict(list)
    for cycle in bundle.cycles:
        grouped[cycle.competition_id].append(cycle)

    for competition_id, cycles in grouped.items():
        ordered = sorted(
            cycles,
            key=lambda item: parse_datetime(
                str(item.deadlines["announced_at"]), "announced_at"
            ),
        )
        by_id = {item.cycle_id: item for item in cycles}
        for index, cycle in enumerate(ordered):
            key = (competition_id, cycle.cycle_id)
            if index == 0:
                if cycle.predecessor_cycle_id is not None:
                    result[key].append("earliest_cycle_must_not_have_predecessor")
            elif cycle.predecessor_cycle_id is None:
                result[key].append("predecessor_cycle_required")

            visited: set[str] = set()
            current = cycle
            while current.predecessor_cycle_id is not None:
                predecessor_id = current.predecessor_cycle_id
                if predecessor_id in visited or predecessor_id == cycle.cycle_id:
                    result[key].append("predecessor_cycle_loop")
                    break
                visited.add(predecessor_id)
                previous = by_id.get(predecessor_id)
                if previous is None:
                    break
                if parse_datetime(
                    str(previous.deadlines["announced_at"]), "announced_at"
                ) >= parse_datetime(
                    str(current.deadlines["announced_at"]), "announced_at"
                ):
                    result[key].append("predecessor_chronology_invalid")
                    break
                current = previous
    return result


def _source_policy_blockers(bundle: LedgerBundle) -> dict[str, list[str]]:
    as_of = parse_datetime(bundle.as_of, "as_of")
    result: dict[str, list[str]] = defaultdict(list)
    for source in bundle.sources:
        result[source.source_id].extend(
            _url_blockers(
                source.official_url,
                source.organizer_domain,
                f"source:{source.source_id}",
            )
        )
        if parse_datetime(source.observed_at, "observed_at") > as_of:
            result[source.source_id].append(
                f"source_observed_after_as_of:{source.source_id}"
            )
    return result


def _cycle_source_ids(cycle: CompetitionCycle) -> set[str]:
    source_ids = set(cycle.source_reference_ids)
    source_ids.update(cycle.eligibility.terms_reference_ids)
    source_ids.update(cycle.licenses.license_reference_ids)
    source_ids.update(cycle.prize.prize_reference_ids)
    source_ids.update(cycle.judging.judging_reference_ids)
    for task in cycle.tasks:
        source_ids.update(task.task_reference_ids)
    return source_ids


def _evaluate_with_policy_hardening(bundle: LedgerBundle) -> dict[str, Any]:
    evaluation = _BASE_EVALUATE(bundle)
    cycle_map = {(item.competition_id, item.cycle_id): item for item in bundle.cycles}
    source_map = {item.source_id: item for item in bundle.sources}
    source_blockers = _source_policy_blockers(bundle)
    chain_blockers = _cycle_chain_blockers(bundle)
    as_of = parse_datetime(bundle.as_of, "as_of")

    invalid_cycle_keys: set[tuple[str, str]] = set()
    for row in evaluation["cycle_rows"]:
        key = (row["competition_id"], row["cycle_id"])
        cycle = cycle_map[key]
        extra: list[str] = []
        extra.extend(
            _url_blockers(
                cycle.official_rule_url,
                cycle.organizer_domain,
                f"cycle:{cycle.cycle_id}",
            )
        )
        extra.extend(chain_blockers.get(key, []))
        for source_id in sorted(_cycle_source_ids(cycle)):
            extra.extend(source_blockers.get(source_id, []))

        row["rule_digest"] = cycle.rule_digest
        row["blockers"] = sorted(set(row.get("blockers", []) + extra))
        row["recommendation_blockers"] = sorted(
            set(row.get("recommendation_blockers", []) + extra)
        )
        if extra:
            row["recommendation_ready"] = False
            invalid_cycle_keys.add(key)
        row.pop("cycle_record_digest", None)
        row["cycle_record_digest"] = stable_digest(row)

    evaluation["recommendations"] = [
        row
        for row in evaluation["recommendations"]
        if (row["competition_id"], row["cycle_id"]) not in invalid_cycle_keys
    ]
    evaluation["archive_rows"] = [
        row
        for row in evaluation["archive_rows"]
        if (row["competition_id"], row["cycle_id"]) not in invalid_cycle_keys
    ]

    submission_map = {
        item.receipt_id: item for item in bundle.submission_receipts
    }
    for row in evaluation["submission_rows"]:
        receipt = submission_map[row["receipt_id"]]
        cycle = cycle_map.get((receipt.competition_id, receipt.cycle_id))
        extra: list[str] = []
        if parse_datetime(receipt.submitted_at, "submitted_at") > as_of:
            extra.append("submission_receipt_after_as_of")
        reference = urlparse(receipt.external_receipt_reference)
        if not reference.scheme or not reference.netloc:
            extra.append("external_submission_receipt_uri_invalid")
        if cycle is not None:
            for source_id in receipt.result_reference_ids:
                source = source_map.get(source_id)
                if source is None:
                    continue
                extra.extend(source_blockers.get(source_id, []))
                if not _domain_matches(
                    urlparse(source.official_url).hostname,
                    cycle.organizer_domain,
                ):
                    extra.append(
                        f"result_source_organizer_mismatch:{source_id}"
                    )
        row["blockers"] = sorted(set(row.get("blockers", []) + extra))
        row["valid"] = not row["blockers"]
        row.pop("assessment_digest", None)
        row["assessment_digest"] = stable_digest(row)

    global_extra = [
        blocker
        for blockers in source_blockers.values()
        for blocker in blockers
    ]
    evaluation["global_blockers"] = sorted(
        set(evaluation.get("global_blockers", []) + global_extra)
    )
    return evaluation


def install_hardening() -> None:
    if getattr(CompetitionCycle, "_r11_hardening_installed", False):
        return
    CompetitionCycle.to_dict = _cycle_input_dict
    CompetitionCycle._r11_hardening_installed = True
    _compiler_module.evaluate_bundle = _evaluate_with_policy_hardening
    _audit_module.evaluate_bundle = _evaluate_with_policy_hardening
