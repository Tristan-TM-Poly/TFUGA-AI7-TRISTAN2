"""Clean-room specification generation from observed behavior."""

from __future__ import annotations

from json import dumps
from typing import Mapping, Sequence

from .fsm import MealyMachine
from .models import Observation


def build_cleanroom_spec(
    *,
    system_id: str,
    candidates: Sequence[MealyMachine],
    observations: Sequence[Observation],
    posterior: Mapping[str, float],
    authorization_reference: str,
    evidence_root: str,
) -> dict[str, object]:
    ranked = sorted(candidates, key=lambda candidate: posterior.get(candidate.candidate_id, 0.0), reverse=True)
    return {
        "schema_version": "0.1.0",
        "system_id": system_id,
        "purpose": "authorized behavioral reconstruction and interoperability",
        "authorization_reference": authorization_reference,
        "evidence_root": evidence_root,
        "epistemic_notice": (
            "This specification describes observed and inferred behavior. It does not claim "
            "recovery of an inaccessible original implementation."
        ),
        "observations": [
            {
                "inputs": list(observation.inputs),
                "outputs": list(observation.outputs),
                "source": observation.source,
                "uncertainty": observation.uncertainty,
            }
            for observation in observations
        ],
        "candidate_models": [
            {
                "candidate_id": candidate.candidate_id,
                "posterior": posterior.get(candidate.candidate_id, 0.0),
                "behavioral_spec": candidate.to_spec(),
            }
            for candidate in ranked
        ],
        "implementation_constraints": [
            "Implement from this behavioral specification, not from inaccessible source code.",
            "Preserve provenance and authorization records.",
            "Treat untested inputs as uncertain rather than silently specified.",
            "Add every discovered counterexample to the regression suite and evidence ledger.",
        ],
    }


def cleanroom_spec_json(spec: Mapping[str, object]) -> str:
    return dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
