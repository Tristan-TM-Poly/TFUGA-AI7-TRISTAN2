import pytest
from omega_synergy_n_t.search import exhaustive_search,beam_search,branch_and_bound,heuristic_candidate
from omega_synergy_n_t.experiment import compile_design,next_adaptive_run,stopping_decision
from omega_synergy_n_t.oak import hard_gate,promotion_flags,classify
from omega_synergy_n_t.fixtures import synergy_os_order4
from omega_synergy_n_t.mobius import decompose_measurements
from omega_synergy_n_t.models import Certification

SIG={"A":{"outputs":["claim"],"domains":["doc"],"evidence":.5},"B":{"inputs":["claim"],"outputs":["test"],"domains":["test"],"evidence":.6},"C":{"inputs":["test"],"outputs":["proof"],"domains":["proof"],"evidence":.7},"D":{"inputs":["proof"],"domains":["portfolio"],"evidence":.4}}
def test_heuristic_closure(): assert heuristic_candidate(("A","B"),SIG).closure_gain>0
def test_exhaustive_orders(): assert {x.order for x in exhaustive_search(SIG,SIG,min_order=2,max_order=3)}=={2,3}
def test_beam_orders(): assert set(beam_search(SIG,SIG,max_order=4,beam_width=5))=={2,3,4}
def test_beam_deterministic(): assert beam_search(SIG,SIG,max_order=4,beam_width=5)==beam_search(SIG,SIG,max_order=4,beam_width=5)
def test_exploration_validation():
    with pytest.raises(ValueError): beam_search(SIG,SIG,exploration_rate=2)
def test_branch_bound_limit(): assert len(branch_and_bound(SIG,SIG,max_results=2))<=2
def test_auto_design_full_small(): assert compile_design(("A","B","C"),design_type="auto").design_type=="full_factorial"
def test_auto_design_fractional_large(): assert compile_design(tuple(map(str,range(9))),design_type="auto").design_type=="fractional_half"
def test_next_adaptive_prefers_uncertainty():
    d=compile_design(("A","B")); obs={frozenset():0}; u={frozenset({"A","B"}):2}; assert next_adaptive_run(d,obs,u)==("A","B")
def test_stopping_critical(): assert stopping_decision(critical_failure=True)=="STOP_CRITICAL_FAILURE"
def test_stopping_positive(): assert stopping_decision(interval_low=.2,interval_high=.5)=="STOP_POSITIVE_DECISION_STABLE"
def test_stopping_continue(): assert stopping_decision(interval_low=-.2,interval_high=.5)=="CONTINUE"
def complete_candidate(**overrides):
    d={x:True for x in ("typed_interfaces","declared_losses","provenance","baseline","simplest_baseline","metric","falsifier","uncertainty","rollback","budget","owner","logging")}; d.update(overrides); return d
def test_gate_pass(): assert hard_gate(complete_candidate()).status=="ELIGIBLE_FOR_EXPERIMENT"
def test_gate_noncompensatory(): assert hard_gate(complete_candidate(metric=False,score=999)).status=="BLOCKED"
def test_recursive_gate(): assert "finite_budget" in hard_gate(complete_candidate(recursive=True)).failed
def test_sensitive_gate(): assert "sensitive_human_gate" in hard_gate(complete_candidate(sensitive=True)).failed
def test_classify_proper():
    x=next(x for x in decompose_measurements(synergy_os_order4()) if x.order==4); assert classify(x)==Certification.N5_PROPER
def test_promotion_flags_safe():
    f=promotion_flags(Certification.N5_PROPER); assert not f["automatic_merge_allowed"] and f["human_review_required"]
