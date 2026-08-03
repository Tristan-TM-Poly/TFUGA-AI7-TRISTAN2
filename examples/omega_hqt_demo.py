from pathlib import Path
from omega_hqt_t.experiment import run_campaign
from omega_hqt_t.interventions import catalog
from omega_hqt_t.parliament import deliberate
from omega_hqt_t.report import write_decision_bundle
from omega_hqt_t.scenarios import compound_ice_storm

report=run_campaign(compound_ice_storm(),catalog(),world_count=32)
decision=deliberate(report)
paths=write_decision_bundle(Path("generated/omega_hqt_t/demo"),report,decision)
print(decision.status, paths)
