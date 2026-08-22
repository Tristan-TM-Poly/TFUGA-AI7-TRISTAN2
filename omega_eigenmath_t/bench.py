from __future__ import annotations

from dataclasses import dataclass

from .core import (
    AttackEngine,
    FormalizationReceipt,
    MathClaimStatus,
    NoveltyStatus,
    ProblemGenome,
    ProofCourt,
    ProofDebtLedger,
    ProofObligation,
    millennium_problem_genomes,
)


@dataclass(frozen=True)
class BenchResult:
    name: str
    passed: bool
    detail: str


class EigenMathBenchR01:
    """Deterministic OAK bench. No open problem solution is embedded."""

    def run(self) -> tuple[BenchResult, ...]:
        court = ProofCourt()
        attack = AttackEngine()
        results: list[BenchResult] = []

        toy = ProblemGenome(
            problem_id="modus_ponens",
            title="Modus ponens positive control",
            exact_statement="From P and P->Q derive Q",
            axioms=("P", "P->Q"),
        )
        receipt = FormalizationReceipt(
            human_statement_hash="h1",
            formal_statement_hash="f1",
            formal_system="toy-kernel",
            translator_id="translator",
            reviewer_id="reviewer",
            fidelity_checks=("quantifiers", "assumptions", "conclusion"),
        )
        good = ProofObligation(
            obligation_id="mp-proof",
            problem_id=toy.problem_id,
            statement="Q",
            assumptions=("P", "P->Q"),
            dependencies=(),
            status=MathClaimStatus.INDEPENDENTLY_VERIFIED,
            producer_id="generator",
            verifier_id="kernel",
            falsifier_id="red-team",
            provenance=("fixture:modus-ponens",),
            tests=("truth-table-replay",),
            proof_artifact="proof:P,P->Q|-Q",
            formalization=receipt,
            independent_replay=("replay-2",),
            novelty_status=NoveltyStatus.REPRODUCED,
        )
        decision = court.judge(toy, good)
        results.append(BenchResult("positive_control", decision.accepted, "; ".join(decision.reasons) or "accepted"))

        bad_roles = good.__class__(**{**good.__dict__, "obligation_id": "role-collision", "verifier_id": "generator"})
        results.append(BenchResult("generator_not_judge", not court.judge(toy, bad_roles).accepted, "collision rejected"))

        numerical = good.__class__(**{
            **good.__dict__,
            "obligation_id": "numerical-jump",
            "proof_artifact": None,
            "computational_evidence": ("first-million-cases",),
            "status": MathClaimStatus.FORMALLY_PROVED,
            "independent_replay": (),
        })
        results.append(BenchResult("numerical_not_proof", not court.judge(toy, numerical).accepted, "numerical jump rejected"))

        ambiguous_receipt = receipt.__class__(**{**receipt.__dict__, "unresolved_ambiguities": ("scope of quantifier",)})
        ambiguous = good.__class__(**{**good.__dict__, "obligation_id": "ambiguous", "formalization": ambiguous_receipt})
        results.append(BenchResult("formalization_gap", not court.judge(toy, ambiguous).accepted, "ambiguous formalization rejected"))

        circular = good.__class__(**{**good.__dict__, "obligation_id": "circular", "dependencies": ("circular",)})
        results.append(BenchResult("proof_attack_circularity", bool(attack.attack(circular)), "attack found circularity"))

        boss = next(p for p in millennium_problem_genomes() if p.problem_id == "riemann")
        boss_candidate = good.__class__(**{
            **good.__dict__,
            "obligation_id": "rh-candidate",
            "problem_id": boss.problem_id,
            "statement": "All non-trivial zeros have real part 1/2",
            "community_acceptance_receipt": None,
        })
        results.append(BenchResult("boss_lock", not court.judge(boss, boss_candidate).accepted, "open problem cannot self-promote"))

        debt = ProofDebtLedger(generated_obligations=10, checked_obligations=3, hidden_assumptions=1, unreplayed_proofs=2)
        results.append(BenchResult("proof_debt_throttle", debt.mode(max_debt=5) == "VERIFY_ATTACK_COMPRESS", f"debt={debt.debt()}"))
        return tuple(results)

    def all_pass(self) -> bool:
        return all(r.passed for r in self.run())


def main() -> int:
    bench = EigenMathBenchR01()
    results = bench.run()
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'} {result.name}: {result.detail}")
    print(f"summary: {sum(r.passed for r in results)}/{len(results)} PASS")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
