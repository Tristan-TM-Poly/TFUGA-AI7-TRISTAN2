from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import asdict
import json

from omega_pct_t.r03max import LagrangianCompiler, OAKBench, scalar_portal_candidate

candidate = scalar_portal_candidate()
compiled = LagrangianCompiler().compile(candidate)
report = OAKBench().evaluate(candidate)

print(json.dumps({
    "theory": candidate.id,
    "fingerprint": compiled.fingerprint,
    "operators": len(compiled.operators),
    "oak_passed": report.passed,
    "gate_results": report.gate_results,
}, indent=2, sort_keys=True))
