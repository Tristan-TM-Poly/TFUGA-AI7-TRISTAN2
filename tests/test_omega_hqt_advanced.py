from omega_hqt_t.economics import evaluate_case
from omega_hqt_t.gridbench import benchmark_manifest,score_submission
from omega_hqt_t.maturity import assess_maturity
from omega_hqt_t.mission import compile_mission
from omega_hqt_t.noether import energy_balance
from omega_hqt_t.source_registry import fixture_registry
from omega_hqt_t.topology import audit_topology,corridor_criticality
from omega_hqt_t.synthetic_quebec import build_corridors
from omega_hqt_t.trust import score_source,claim_confidence
from omega_hqt_t.uncertainty import Interval,ratio,uncertainty_budget

def test_noether_balance_and_residue():
    assert energy_balance(inputs_mwh=100,outputs_mwh=97,modeled_losses_mwh=3).status=='BALANCED_WITHIN_TOLERANCE'
    assert energy_balance(inputs_mwh=100,outputs_mwh=90).status.startswith('OAK_')

def test_topology_audit_is_deterministic():
    a=audit_topology(build_corridors()); b=audit_topology(build_corridors()); assert a.evidence_hash==b.evidence_hash; assert len(corridor_criticality(build_corridors()))==20

def test_uncertainty_operations():
    x=Interval(8,12,0.95,('x',)); y=Interval(2,4,0.9,('y',)); z=ratio(x,y); assert z.low==2 and z.high==6
    assert uncertainty_budget({'data':3,'model':4})['rss_combined']==5

def test_mission_compiler_and_maturity():
    assert compile_mission('improve synthetic regional resilience').status.startswith('READY')
    assert compile_mission('provide live switching command and relay setting').status.startswith('BLOCKED')
    assessment=assess_maturity('x','preliminary_simulation',{'determinism','tests','provenance'}); assert assessment.promotable

def test_trust_economics_and_gridbench():
    source=score_source('fixture',authority=.8,directness=1,freshness=1,reproducibility=1,independence=.5,licence_clarity=1); assert source.composite_score>.8
    assert claim_confidence([.8,.7])>.9
    assert evaluate_case('x',capex_index=10,opex_index=1,expected_avoided_unserved_mwh=5).evidence_hash
    assert score_submission(performance=.8,robustness=.8,explainability=.8,evidence=.8,safety=1,overconfidence=0)>80
    assert benchmark_manifest()['claims']['real_grid_benchmark'] is False
    assert fixture_registry().manifest()['source_count']==2
