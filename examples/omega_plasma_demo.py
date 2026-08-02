import json
from pathlib import Path
from omega_plasma_t.state import PlasmaState
from omega_plasma_t.oak import audit_state
from omega_plasma_t.reporting import write_report

state=PlasmaState.from_dict(json.loads(Path("examples/omega_plasma_state.json").read_text()))
report=audit_state(state)
print(json.dumps({"status":report.status,"labels":report.assessment.labels,"recommended":[x.name for x in report.model_decision.recommended]},indent=2))
write_report(state,report,Path("generated/omega_plasma_t/demo"))
