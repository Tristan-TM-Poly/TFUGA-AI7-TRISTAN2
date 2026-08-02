"""Closed-loop reconstruction campaign for the finite-state-machine MVP."""

from __future__ import annotations

from itertools import product
from typing import Iterable, Sequence

from .active import select_experiment
from .bayes import posterior_entropy_bits, posterior_map, score_candidates
from .evidence import EvidenceLedger
from .fsm import MealyMachine
from .identifiability import identifiability_debt_bits
from .models import (
    AuthorizationScope,
    CampaignResult,
    ClaimStatus,
    OAKMetricVector,
    Observation,
)
from .oak import evaluate_oak


def all_sequences(alphabet: Sequence[str], max_length: int) -> tuple[tuple[str, ...], ...]:
    return tuple(
        sequence
        for length in range(1, max_length + 1)
        for sequence in product(alphabet, repeat=length)
    )


def behaviorally_equal(
    left: MealyMachine,
    right: MealyMachine,
    *,
    max_length: int,
) -> bool:
    if left.input_alphabet != right.input_alphabet:
        return False
    return all(
        left.run(sequence)[0] == right.run(sequence)[0]
        for sequence in all_sequences(left.input_alphabet, max_length)
    )


def reconstruct_fsm(
    *,
    oracle: MealyMachine,
    candidates: Iterable[MealyMachine],
    authorization: AuthorizationScope,
    max_rounds: int = 12,
    max_experiment_length: int = 5,
    validation_max_length: int = 8,
    error_probability: float = 1.0e-6,
) -> CampaignResult:
    authorization.require("query_oracle")
    population = tuple(candidates)
    if not population:
        raise ValueError("Candidate population cannot be empty")
    observations: list[Observation] = []
    ledger = EvidenceLedger.empty()
    ledger.append(
        record_id="scope-0001",
        kind="authorization_scope",
        payload={
            "mode": authorization.mode.value,
            "purpose": authorization.purpose,
            "permitted_actions": list(authorization.permitted_actions),
            "prohibited_actions": list(authorization.prohibited_actions),
            "reference": authorization.reference,
        },
        claim_status=ClaimStatus.OBSERVED,
    )
    scores = score_candidates(population, observations, error_probability=error_probability)
    surviving = list(population)
    completed_rounds = 0
    for round_index in range(1, max_rounds + 1):
        posterior = posterior_map(scores)
        experiment = select_experiment(
            surviving,
            alphabet=oracle.input_alphabet,
            max_length=max_experiment_length,
            posterior=posterior,
        )
        if experiment is None or experiment.expected_information_gain_bits <= 1.0e-12:
            break
        observation = oracle.observe(experiment.inputs, source="authorized-oracle")
        observations.append(observation)
        ledger.append(
            record_id=f"observation-{round_index:04d}",
            kind="behavioral_observation",
            payload={
                "inputs": list(observation.inputs),
                "outputs": list(observation.outputs),
                "expected_information_gain_bits": experiment.expected_information_gain_bits,
                "utility": experiment.utility,
            },
            claim_status=ClaimStatus.OBSERVED,
            provenance=("scope-0001",),
        )
        scores = score_candidates(population, observations, error_probability=error_probability)
        score_by_id = {score.candidate_id: score for score in scores}
        surviving = [
            candidate for candidate in population if score_by_id[candidate.candidate_id].mismatches == 0
        ]
        completed_rounds = round_index
        if len(surviving) <= 1:
            break
    scores = score_candidates(surviving or population, observations, error_probability=error_probability)
    posterior = posterior_map(scores)
    entropy = posterior_entropy_bits(scores)
    validation_tests = all_sequences(oracle.input_alphabet, validation_max_length)
    debt = identifiability_debt_bits(surviving, validation_tests, posterior=posterior) if surviving else entropy
    top_id = scores[0].candidate_id if scores else None
    by_id = {candidate.candidate_id: candidate for candidate in population}
    top = by_id.get(top_id) if top_id is not None else None
    exact = top is not None and behaviorally_equal(top, oracle, max_length=validation_max_length)
    total_symbols = sum(len(observation.inputs) for observation in observations)
    fidelity = 1.0 if exact else 0.0
    generalization = fidelity
    causal_quality = 1.0 if exact and completed_rounds > 0 else min(1.0, completed_rounds / max(1, min(3, max_rounds)))
    parsimony = 1.0 if top is not None and top.complexity <= oracle.complexity else 0.5
    uncertainty_calibration = 1.0 if (len(surviving) == 1 and entropy < 1.0e-9) or len(surviving) > 1 else 0.75
    reproducibility = 1.0
    legal_provenance = 1.0
    ledger.append(
        record_id="reconstruction-0001",
        kind="reconstruction_summary",
        payload={
            "rounds": completed_rounds,
            "total_symbols": total_symbols,
            "surviving_candidate_ids": [candidate.candidate_id for candidate in surviving],
            "posterior_entropy_bits": entropy,
            "identifiability_debt_bits": debt,
            "top_candidate_id": top_id,
            "exact_behavior_recovered": exact,
        },
        claim_status=ClaimStatus.RECONSTRUCTED,
        provenance=tuple(f"observation-{index:04d}" for index in range(1, completed_rounds + 1)),
    )
    oak_report = evaluate_oak(
        OAKMetricVector(
            fidelity=fidelity,
            generalization=generalization,
            causal_quality=causal_quality,
            parsimony=parsimony,
            uncertainty_calibration=uncertainty_calibration,
            reproducibility=reproducibility,
            legal_provenance=legal_provenance,
        ),
        ledger,
        independent_validation=False,
    )
    return CampaignResult(
        rounds=completed_rounds,
        observations=tuple(observations),
        surviving_candidate_ids=tuple(candidate.candidate_id for candidate in surviving),
        posterior_entropy_bits=entropy,
        identifiability_debt_bits=debt,
        top_candidate_id=top_id,
        exact_behavior_recovered=exact,
        oak_report=oak_report,
    )
