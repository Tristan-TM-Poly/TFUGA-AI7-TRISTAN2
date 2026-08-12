"""Leak-resistant contestant/evaluator split for GreatSages blind tournaments."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Sequence

from sage_tristan.greatsages import SageProfile, discovery_by_id, get_profile
from sage_tristan.greatsages_time_machine import causal_leakage_firewall, default_context, time_machine_snapshot


@dataclass(frozen=True, slots=True)
class ContestantPack:
    tournament_id: str
    sage_id: str
    gate_year: int
    visible_atom_ids: tuple[str, ...]
    visible_discovery_ids: tuple[str, ...]
    task_contract: tuple[str, ...]
    scoring_axes: tuple[str, ...]
    target_content_withheld: bool = True
    descendant_content_withheld: bool = True
    historical_truth_certified: bool = False


@dataclass(frozen=True, slots=True)
class EvaluatorSecret:
    tournament_id: str
    target_discovery_id: str
    target_year: int
    target_title: str
    masked_discovery_ids: tuple[str, ...]
    descendants_masked: tuple[str, ...]
    target_digest: str


def _opaque_id(profile: SageProfile, discovery_id: str, gate_year: int) -> str:
    digest = sha256(f"greatsages-blind-v1|{profile.sage_id}|{discovery_id}|{gate_year}".encode("utf-8")).hexdigest()
    return f"blind::{profile.sage_id}::{digest[:16]}"


def compile_blind_packs(profile: SageProfile, discovery_id: str) -> tuple[ContestantPack, EvaluatorSecret]:
    target = discovery_by_id(profile, discovery_id)
    gate_year = max(profile.birth_year, target.year - 1)
    context = default_context(profile, gate_year)
    snapshot = time_machine_snapshot(profile, context)
    firewall = causal_leakage_firewall(profile, discovery_id, year=gate_year)
    tournament_id = _opaque_id(profile, discovery_id, gate_year)

    contestant = ContestantPack(
        tournament_id=tournament_id,
        sage_id=profile.sage_id,
        gate_year=gate_year,
        visible_atom_ids=snapshot.allowed_atom_ids,
        visible_discovery_ids=firewall.visible_discovery_ids,
        task_contract=(
            "Generate candidate next discoveries using only the supplied visible state.",
            "Do not use later terminology, notation, instruments or descendants unless supplied.",
            "Separate historical evidence, reconstruction and speculative alternatives.",
            "Return failure paths and counterexamples, not only a preferred answer.",
        ),
        scoring_axes=(
            "chronological_admissibility",
            "causal_leakage_control",
            "problem_transformation_quality",
            "invariant_or_representation_gain",
            "counterexample_strength",
            "epistemic_calibration",
        ),
    )

    evaluator = EvaluatorSecret(
        tournament_id=tournament_id,
        target_discovery_id=target.discovery_id,
        target_year=target.year,
        target_title=target.title,
        masked_discovery_ids=firewall.masked_discovery_ids,
        descendants_masked=firewall.descendants_masked,
        target_digest=sha256(target.discovery_id.encode("utf-8")).hexdigest(),
    )
    return contestant, evaluator


def contestant_payload(profile: SageProfile, discovery_id: str) -> dict[str, object]:
    contestant, _ = compile_blind_packs(profile, discovery_id)
    payload = asdict(contestant)
    serialized = json.dumps(payload, sort_keys=True)
    target = discovery_by_id(profile, discovery_id)
    forbidden = (
        discovery_id,
        target.title,
        target.problem,
        target.compressed_invariant,
    )
    leakage = tuple(value for value in forbidden if value and value in serialized)
    payload["metadata_leakage_detected"] = bool(leakage)
    payload["leakage_tokens"] = leakage
    return payload


def evaluator_payload(profile: SageProfile, discovery_id: str) -> dict[str, object]:
    _, evaluator = compile_blind_packs(profile, discovery_id)
    return asdict(evaluator)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="GreatSages blind tournament pack compiler")
    parser.add_argument("--sage", default="gauss")
    parser.add_argument("--discovery", default="gauss_1801_ceres")
    parser.add_argument("--evaluator", action="store_true", help="emit secret evaluator metadata instead of contestant pack")
    args = parser.parse_args(argv)
    profile = get_profile(args.sage)
    payload = evaluator_payload(profile, args.discovery) if args.evaluator else contestant_payload(profile, args.discovery)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
