from dataclasses import asdict
from omega_solids_t.campaign import default_campaign_spec
from omega_solids_t.oak import evaluate_candidate
from omega_solids_t.hypergraph import from_candidate
import json
spec=default_campaign_spec(); candidate=spec.candidate_at(424242,2); report=evaluate_candidate(candidate); graph=from_candidate(candidate)
print(json.dumps({"campaign":{"base":spec.base_cardinality,"contextual":spec.contextual_cardinality,"fingerprint":spec.fingerprint},"candidate":asdict(candidate),"candidate_fingerprint":candidate.fingerprint,"oak":asdict(report),"hypergraph":graph.validate()},ensure_ascii=False,indent=2,default=str))
