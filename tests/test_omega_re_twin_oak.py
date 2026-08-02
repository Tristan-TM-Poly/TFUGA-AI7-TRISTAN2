from omega_re_t.cleanroom import build_cleanroom_spec, cleanroom_spec_json
from omega_re_t.evidence import EvidenceLedger
from omega_re_t.fsm import canonical_demo_machine, enumerate_mealy_machines
from omega_re_t.models import ClaimStatus, OAKMetricVector
from omega_re_t.oak import evaluate_oak
from omega_re_t.twin import CounterfactualTwin


def test_counterfactual_twin_exposes_uncertainty():
    candidates = tuple(
        enumerate_mealy_machines(
            state_count=1,
            input_alphabet=("A",),
            output_alphabet=("0", "1"),
            max_candidates=10,
        )
    )
    twin = CounterfactualTwin(candidates=candidates, posterior={candidate.candidate_id: 0.5 for candidate in candidates})
    prediction = twin.predict(("A",))
    assert prediction.confidence == 0.5
    assert set(prediction.distribution) == {("0",), ("1",)}


def test_oak_requires_independent_validation_for_verified_status():
    ledger = EvidenceLedger.empty()
    ledger.append(
        record_id="scope",
        kind="scope",
        payload={"authorized": True},
        claim_status=ClaimStatus.OBSERVED,
    )
    metrics = OAKMetricVector(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    conditional = evaluate_oak(metrics, ledger, independent_validation=False)
    verified = evaluate_oak(metrics, ledger, independent_validation=True)
    assert conditional.decision == "CONDITIONAL"
    assert conditional.promoted_status == ClaimStatus.RECONSTRUCTED
    assert verified.decision == "PROMOTE"
    assert verified.promoted_status == ClaimStatus.VERIFIED


def test_cleanroom_spec_contains_provenance_and_not_originality_claim():
    oracle = canonical_demo_machine()
    observation = oracle.observe(("A", "B"))
    spec = build_cleanroom_spec(
        system_id="demo",
        candidates=(oracle,),
        observations=(observation,),
        posterior={oracle.candidate_id: 1.0},
        authorization_reference="sandbox",
        evidence_root="abc",
    )
    text = cleanroom_spec_json(spec)
    assert '"authorization_reference": "sandbox"' in text
    assert "does not claim" in text
    assert oracle.candidate_id in text
