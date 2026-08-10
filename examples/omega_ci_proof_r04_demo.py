from pathlib import Path

from omega_ci_proof_t.r04.causal import CausalDiagnosticEngine
from omega_ci_proof_t.r04.experiments import DiscriminatingExperimentPlanner, experiments_from_mapping
from omega_ci_proof_t.r04.io import read_json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "omega_ci_proof_t"

model = read_json(DATA / "r04-model.json")
engine = CausalDiagnosticEngine.from_mapping(model)
observations = engine.observations_from_mapping(read_json(DATA / "r04-observations.json"))
diagnosis = engine.diagnose(str(model["failure_id"]), observations)
experiments = experiments_from_mapping(read_json(DATA / "r04-experiments.json"))
plan = DiscriminatingExperimentPlanner().plan(diagnosis, experiments, budget=1.0)

print(diagnosis.to_dict())
print(plan.to_dict())
