import json
import sys
from dataclasses import asdict

from .models import Claim, Evidence
from .compiler import MetaCompiler, compile_receipt
from .mutation import invariant_mutation_probes
from .skill_civilization import (
    SkillGenome,
    compile_counterfactual_plans,
    crystallize_skill_plan,
    generate_residual_skill_candidates,
    meta_generalize,
    regeneration_seed,
    select_minimum_sufficient_plan,
)


def example():
    evidence = Evidence(id="E-001", statement="Prototype benchmark supports bounded scope", scope=0.6, provenance="example-benchmark", independent=True, uncertainty=0.1)
    claim = Claim(id="C-001", statement="The prototype improves the bounded benchmark", scope=0.5, epistemic_status="TESTED", evidence_ids=[evidence.id], falsifiers=["fails baseline", "out-of-sample regression"], provenance="example")
    compiler = MetaCompiler()
    result = compiler.promotion_gate(claim, [evidence], generator_role="generator-A", judge_role="verifier-B", verified_gain=0.8, complexity_debt=0.2, risk_debt=0.1)
    receipt = compile_receipt([claim.id], "promotion-evaluation", ["candidate"], [evidence.id], 0.1, "human-review", "example", "revert candidate")
    print(json.dumps({"promotion_gate": result.to_dict(), "receipt": asdict(receipt), "mutation_probes": invariant_mutation_probes()}, indent=2, sort_keys=True))


def skill_example():
    skills = [
        SkillGenome(
            name="router",
            capabilities=frozenset({"route", "compose"}),
            verified=True,
            evidence_refs=("E-router",),
            cost=0.5,
            risk=0.1,
            complexity=0.1,
            transfer=0.8,
            regenerability=0.8,
        ),
        SkillGenome(
            name="judge",
            capabilities=frozenset({"verify", "crystallize"}),
            verified=True,
            evidence_refs=("E-judge",),
            cost=0.5,
            risk=0.1,
            complexity=0.1,
            transfer=0.8,
            regenerability=0.9,
        ),
    ]
    required = {"route", "compose", "verify", "crystallize"}
    plans = compile_counterfactual_plans(required, skills)
    chosen = select_minimum_sufficient_plan(plans)
    receipt = crystallize_skill_plan(
        name="BOOK0_SKILL_CANDIDATE",
        plan=chosen,
        skill_index={skill.name: skill for skill in skills},
        generator="generator-A",
        judge="judge-B",
        independent_evidence=True,
        tests_passed=True,
    )
    seed = regeneration_seed(receipt.crystal) if receipt.crystal else None
    payload = {
        "meta_generalization": meta_generalize(skills),
        "counterfactual_modes": sorted({plan.mode for plan in plans}),
        "selected_plan": asdict(chosen) if chosen else None,
        "residual_candidates": generate_residual_skill_candidates(required, skills),
        "crystallization": asdict(receipt),
        "regeneration_seed": asdict(seed) if seed else None,
        "external_action_performed": False,
        "auto_promoted": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=sorted))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "example"
    if command == "example":
        example()
    elif command == "skill-example":
        skill_example()
    else:
        raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    main()
