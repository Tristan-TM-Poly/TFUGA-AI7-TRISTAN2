from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_intent_t.r03 import ImpactRouter, ProofArtifactBuilder, RepoTwinScanner, ValidationReceipt, run_oakbench

with tempfile.TemporaryDirectory(prefix="omega-intent-r03-demo-") as tmp:
    root = Path(tmp)
    (root / "omega_demo").mkdir()
    (root / "tests").mkdir()
    (root / ".github/workflows").mkdir(parents=True)
    (root / "omega_demo/core.py").write_text("def identity(value): return value\n", encoding="utf-8")
    (root / "tests/test_demo.py").write_text("import omega_demo\ndef test_import(): assert omega_demo is not None\n", encoding="utf-8")
    (root / ".github/workflows/demo.yml").write_text(
        "name: Demo\non:\n  pull_request:\n    paths:\n      - 'omega_demo/**'\n      - 'tests/test_demo.py'\n",
        encoding="utf-8",
    )
    manifest = RepoTwinScanner().scan(root)
    plan = ImpactRouter().route(manifest, ["omega_demo/core.py"])
    artifact = ProofArtifactBuilder().build(
        root / "omega_demo/core.py",
        root=root,
        provenance=("INTENT-DEMO-R03",),
        derived_from=(plan.plan_id,),
        validations=(ValidationReceipt("compile", "passed", "python -m compileall"),),
    )
    payload = {
        "manifest": manifest.to_dict(),
        "impact_plan": plan.to_dict(),
        "proof_artifact": artifact.to_dict(),
        "oak": run_oakbench().to_dict(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
