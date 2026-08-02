from dataclasses import replace

import pytest

from omega_re_t.active_causal import (
    CausalHypothesis,
    Intervention,
    score_intervention,
    select_intervention,
    update_posterior,
)
from omega_re_t.authenticated_receipts import ReceiptChain


def test_active_causal_selects_discriminating_intervention():
    hypotheses = [
        CausalHypothesis("h1", {"a": 0.9, "b": 0.5}),
        CausalHypothesis("h2", {"a": 0.1, "b": 0.5}),
    ]
    selected = select_intervention(hypotheses, [Intervention("a"), Intervention("b")])
    assert selected.intervention == "a"
    assert selected.information_gain_bits > 0.5


def test_blocked_intervention_has_no_utility():
    hypotheses = [CausalHypothesis("h", {"a": 0.5})]
    score = score_intervention(hypotheses, Intervention("a", authorized=False))
    assert score.blocked
    assert score.utility == float("-inf")


def test_posterior_update_moves_toward_likely_hypothesis():
    hypotheses = [
        CausalHypothesis("h1", {"a": 0.9}),
        CausalHypothesis("h2", {"a": 0.1}),
    ]
    posterior = update_posterior(hypotheses, "a", True)
    assert posterior[0] == pytest.approx(0.9)
    assert posterior[1] == pytest.approx(0.1)


def test_receipt_chain_detects_tampering():
    chain = ReceiptChain(b"secret")
    first = chain.append("materialized", {"count": 2})
    second = chain.append("executed", {"count": 1})
    valid, errors = chain.verify()
    assert valid and not errors

    tampered = replace(second, event="rewritten")
    valid, errors = chain.verify((first, tampered))
    assert not valid
    assert any("mismatch" in error for error in errors)
