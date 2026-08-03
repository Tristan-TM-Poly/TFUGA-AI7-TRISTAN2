import pytest
from omega_synergy_n_t.information import entropy,mutual_information,conditional_mutual_information,interaction_information,xor_fixture,information_report
from omega_synergy_n_t.tensor import SparseInteractionTensor
from omega_synergy_n_t.bayes import NormalBelief,update,probability_greater_than,hypothesis_packet
from omega_synergy_n_t.uncertainty import rss_standard_error,decayed_confidence,compare_contexts
from omega_synergy_n_t.fixtures import synergy_os_order4
from omega_synergy_n_t.mobius import decompose_measurements
from omega_synergy_n_t.pr_hypergraph import PRMutation,compile_constellation,topological_waves,hyper_epistasis


def test_entropy_binary(): assert entropy([0,0,1,1])==pytest.approx(1)
def test_mutual_information_identity(): assert mutual_information([0,0,1,1],[0,0,1,1])==pytest.approx(1)
def test_xor_inputs_individually_uninformative():
    x,y,t=xor_fixture(); assert mutual_information(x,t)==pytest.approx(0) and mutual_information(y,t)==pytest.approx(0)
def test_xor_joint_informative():
    x,y,t=xor_fixture(); assert information_report(x,y,t)["i_xy_target"]==pytest.approx(1)
def test_xor_interaction_negative_under_convention():
    x,y,t=xor_fixture(); assert interaction_information(x,y,t)<0
def test_information_length_validation():
    with pytest.raises(ValueError): mutual_information([1],[1,2])
def test_tensor_symmetry():
    t=SparseInteractionTensor(); t.set(("B","A"),.5); assert t.get(("A","B"))==.5
def test_tensor_slices():
    t=SparseInteractionTensor(); t.set(("A",),1); t.set(("A","B"),2); assert list(t.order_slice(2).values())==[2]
def test_tensor_positive_negative():
    t=SparseInteractionTensor(); t.set(("A",),1); t.set(("B",),-1); assert len(t.positive())==1 and len(t.negative())==1
def test_tensor_top_absolute():
    t=SparseInteractionTensor(); t.set(("A",),1); t.set(("B",),-3); assert t.top(1,absolute=True)[0][0]==("B",)
def test_tensor_sparsity():
    t=SparseInteractionTensor(); t.set(("A",),1); assert 0<t.sparsity(3,2)<1
def test_bayes_update_reduces_sd():
    prior=NormalBelief(0,1); post=update(prior,1,.5); assert post.standard_deviation<prior.standard_deviation
def test_bayes_probability_positive(): assert probability_greater_than(NormalBelief(2,.1))>.99
def test_bayes_packet_safe(): assert hypothesis_packet(NormalBelief())["decision_authority"]=="review_only"
def test_bayes_error_validation():
    with pytest.raises(ValueError): update(NormalBelief(),1,0)
def test_rss(): assert rss_standard_error([3,4])==5
def test_decay_half_life(): assert decayed_confidence(1,10,10)==pytest.approx(.5)
def test_decay_validation():
    with pytest.raises(ValueError): decayed_confidence(2,1,1)
def test_compare_contexts_inconclusive_for_same():
    x=next(e for e in decompose_measurements(synergy_os_order4()) if e.order==4); assert compare_contexts(x,x)["status"]=="INCONCLUSIVE"
def test_pr_constellation_waves():
    a=PRMutation("A",("a",)); b=PRMutation("B",("b",),dependencies=("A",)); c=compile_constellation([a,b]); assert topological_waves(c)==[("A",),("B",)]
def test_pr_constellation_conflict():
    a=PRMutation("A",("a",),conflicts=("B",)); b=PRMutation("B",("b",)); assert compile_constellation([a,b]).conflict_pairs==(("A","B"),)
def test_pr_cycle_detected():
    a=PRMutation("A",("a",),dependencies=("B",)); b=PRMutation("B",("b",),dependencies=("A",));
    with pytest.raises(ValueError): topological_waves(compile_constellation([a,b]))
def test_hyper_epistasis():
    v={frozenset():0,frozenset({"A"}):0,frozenset({"B"}):0,frozenset({"A","B"}):1}; assert hyper_epistasis(v,("A","B"))==1
