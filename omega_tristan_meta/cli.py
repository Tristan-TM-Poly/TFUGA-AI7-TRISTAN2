import json, sys
from dataclasses import asdict
from .models import Claim, Evidence
from .compiler import MetaCompiler, compile_receipt
from .mutation import invariant_mutation_probes

def example():
    evidence = Evidence(id="E-001", statement="Prototype benchmark supports bounded scope", scope=0.6, provenance="example-benchmark", independent=True, uncertainty=0.1)
    claim = Claim(id="C-001", statement="The prototype improves the bounded benchmark", scope=0.5, epistemic_status="TESTED", evidence_ids=[evidence.id], falsifiers=["fails baseline", "out-of-sample regression"], provenance="example")
    compiler = MetaCompiler()
    result = compiler.promotion_gate(claim, [evidence], generator_role="generator-A", judge_role="verifier-B", verified_gain=0.8, complexity_debt=0.2, risk_debt=0.1)
    receipt = compile_receipt([claim.id], "promotion-evaluation", ["candidate"], [evidence.id], 0.1, "human-review", "example", "revert candidate")
    print(json.dumps({"promotion_gate": result.to_dict(), "receipt": asdict(receipt), "mutation_probes": invariant_mutation_probes()}, indent=2, sort_keys=True))

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "example"
    if command == "example":
        example()
    else:
        raise SystemExit(f"unknown command: {command}")

if __name__ == "__main__":
    main()
