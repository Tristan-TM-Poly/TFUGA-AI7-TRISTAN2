from __future__ import annotations
from dataclasses import asdict
import json
from .general_network import BalanceNode, DirectedArc
from .solver_crosscheck import crosscheck_general_flow, crosscheck_time_expanded_flow
from .temporal_network import TemporalArc, TemporalBalance
from .multi_commodity import Commodity, SharedArc, solve_fractional_multi_commodity
from .holdout import TemporalPredictionCase, evaluate_temporal_holdout
from .unit_ontology import convert_value
from .lcia_governance import MethodDescriptor, GovernedFactor, GovernedMethod, validate_governed_method
from .source_anchors import SOURCE_ANCHORS
from .live_sources import EUROSTAT_ENV_WASMUN_LIVE, EPA_SMM_LANDING_LIVE

def run_r06_evidence()->dict:
    nodes=(BalanceNode("source",2),BalanceNode("hub",0),BalanceNode("sink",-2))
    arcs=(DirectedArc("source","hub",2,1),DirectedArc("hub","sink",2,2),DirectedArc("source","sink",1,10))
    cross=crosscheck_general_flow(nodes,arcs)
    temporal_balances=(TemporalBalance("plant",0,2),TemporalBalance("user",2,-2))
    temporal_arcs=(TemporalArc("plant","hub",0,1,2,1),TemporalArc("hub","user",1,2,2,2))
    tcross=crosscheck_time_expanded_flow(temporal_balances,temporal_arcs,holdover_nodes=("hub",),periods=(0,1,2))
    commodities=(Commodity("copper","cu_source","sink_cu",1),Commodity("aluminium","al_source","sink_al",1))
    shared=(
        SharedArc("cu_in","cu_source","hub",1,0),SharedArc("al_in","al_source","hub",1,0),
        SharedArc("shared","hub","split",1.5,1),SharedArc("cu_out","split","sink_cu",1,0),
        SharedArc("al_out","split","sink_al",1,0),
    )
    mc=solve_fractional_multi_commodity(commodities,shared)
    hold=evaluate_temporal_holdout(
        (
            TemporalPredictionCase("2021",2021,500,{"omega":501,"persistence":499}),
            TemporalPredictionCase("2022",2022,510,{"omega":514,"persistence":509}),
            TemporalPredictionCase("2023",2023,511,{"omega":518,"persistence":510}),
            TemporalPredictionCase("2024",2024,517,{"omega":525,"persistence":512}),
        ),
        holdout_start=2023,canonical_method="omega",
    )
    descriptor=MethodDescriptor("external-demo-contract","1","external publisher","https://example.org/method","0"*64)
    governed=GovernedMethod(descriptor,(GovernedFactor("electricity","kWh","climate",0.5,"kgCO2e"),))
    validate_governed_method(governed)
    return {
      "bench_version":"0.6.0",
      "solver_crosscheck":{
        "flow_agreement":cross.flow_agreement,"cost_agreement":cross.cost_agreement,
        "internal_flow":cross.internal_flow,"external_flow":cross.external_flow,
        "external_solver":cross.external_solver,"claim_boundary":cross.claim_boundary,
      },
      "time_expanded_crosscheck":{
        "flow_agreement":tcross.flow_agreement,"cost_agreement":tcross.cost_agreement,
        "internal_flow":tcross.internal_flow,"external_flow":tcross.external_flow,
        "external_solver":tcross.external_solver,"claim_boundary":tcross.claim_boundary,
      },
      "multi_commodity":{
        "total_flow":mc.total_flow,"total_cost":mc.total_cost,"delivered":dict(mc.delivered),
        "shared_capacity_binding":abs(mc.total_flow-1.5)<=1e-9,
        "optimality_certified":mc.optimality_certified,"solver":mc.solver,"claim_boundary":mc.claim_boundary,
      },
      "temporal_holdout":{
        "train_count":hold.train_count,"test_count":hold.test_count,
        "best_method":hold.campaign.best_method_by_rmse,"canonical_is_best":hold.campaign.canonical_is_best,
        "canonical_rmse_regret":hold.campaign.canonical_rmse_regret,"claim_boundary":hold.claim_boundary,
      },
      "unit_ontology":{"one_metric_tonne_kg":convert_value(1,"metric_tonne","kg"),"three_point_six_MJ_kWh":convert_value(3.6,"MJ","kWh")},
      "lcia_governance":{"method":governed.descriptor.name,"factor_hash":governed.descriptor.factor_sha256,"claim_boundary":governed.claim_boundary,"bundled_recognized_factor_set":False},
      "source_anchors":[asdict(a) for a in SOURCE_ANCHORS],
      "live_acquisition_specs":[asdict(EUROSTAT_ENV_WASMUN_LIVE),asdict(EPA_SMM_LANDING_LIVE)],
      "limits":[
        "source anchors are current web-verified descriptors, not raw HTTP snapshots",
        "live HTTP acquisition is isolated in a separate evidence workflow and never mutates repository state",
        "SciPy/HiGHS cross-check is independent software evidence, not a formal proof",
        "multi-commodity result is fractional LP only; integer/process coupling remains future work",
        "temporal holdout scores supplied predictions and does not train a model",
        "no proprietary or endorsed LCIA factor set is bundled",
      ],
    }
def render_r06_evidence()->str:
    return json.dumps(run_r06_evidence(),indent=2,sort_keys=True)
