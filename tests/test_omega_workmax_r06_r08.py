from omega_workmax_t.search_lab import run_multifidelity_beam
from omega_workmax_t.scheduling_memory import SchedulingMemoryEvent,SchedulingMemoryLedger
from omega_workmax_t.policy_lab import PolicyOutcome,compare_policies

def test_beam_reports_regret_and_pareto_recall():
    report=run_multifidelity_beam({
      "stages":[{"name":"cheap","beam_width":2},{"name":"full","beam_width":1}],
      "candidates":[
        {"candidate_id":"a","evaluations":{"cheap":{"utility":8,"evidence":.8,"risk":.1,"cost":1},"full":{"utility":10,"evidence":1,"risk":.1,"cost":4}}},
        {"candidate_id":"b","evaluations":{"cheap":{"utility":9,"evidence":.9,"risk":.1,"cost":1},"full":{"utility":9,"evidence":1,"risk":.05,"cost":3}}},
        {"candidate_id":"c","evaluations":{"cheap":{"utility":4,"evidence":1,"risk":0,"cost":1},"full":{"utility":12,"evidence":1,"risk":.2,"cost":8}}},
      ]})
    assert report["evaluated_cells"]==5
    assert report["full_grid_cells"]==6
    assert report["evaluation_reduction"]>0
    assert report["beam_best"] in {"a","b"}
    assert report["exhaustive_best"]=="c"
    assert report["score_regret"]>0
    assert report["automatic_promotion_authorized"] is False

def test_memory_blocks_reproducible_negative_repeat():
    ledger=SchedulingMemoryLedger()
    neg=SchedulingMemoryEvent("M_MINUS","m1","p1","ctx","fanout regression",reproducible=True)
    assert ledger.append(neg) is True
    assert ledger.append(neg) is False
    assert ledger.blocks_repeat("p1","ctx") is True
    pos=SchedulingMemoryEvent("M_PLUS","m2","p1","ctx","mitigation validated",reproducible=True)
    ledger.append(pos)
    assert ledger.blocks_repeat("p1","ctx") is False
    assert ledger.evidence_score("p1","ctx")==0.0

def test_policy_lab_promotes_only_without_proof_regression():
    rows=[
      PolicyOutcome("inc","s1",True,100,1,0.8,5,0,0.1),
      PolicyOutcome("inc","s2",True,100,1,0.8,5,0,0.1),
      PolicyOutcome("fast","s1",True,70,1,0.85,3,0,0.1),
      PolicyOutcome("fast","s2",True,80,1,0.85,3,0,0.1),
      PolicyOutcome("unsafe","s1",True,40,.8,0.9,2,0,0.1),
      PolicyOutcome("unsafe","s2",True,40,.8,0.9,2,0,0.1),
    ]
    report=compare_policies(rows,incumbent_policy_id="inc")
    assert report["selected_policy"]=="fast"
    assert report["decision"]=="PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW"
    assert report["automatic_merge_authorized"] is False
