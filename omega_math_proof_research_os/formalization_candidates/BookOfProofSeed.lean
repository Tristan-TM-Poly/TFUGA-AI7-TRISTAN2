/-
Ω-MATH-PROOF-RESEARCH-OS R0.1 — formalization candidates.

OAK STATUS: CANDIDATE / NOT CI-CERTIFIED IN THIS PR.
These statements are intentionally small translations of paraphrased logical
rules extracted from the supplied Book of Proof metadata. Kernel acceptance,
when wired to a pinned Lean toolchain, still will not by itself certify that a
formal statement perfectly matches the intended natural-language source.
-/

universe u

section ClassicalLogicSeeds

variable {α : Type u} (P : α → Prop)

/-- Classical quantifier-negation candidate. -/
theorem not_forall_iff_exists_not : (¬ ∀ x, P x) ↔ ∃ x, ¬ P x := by
  classical
  constructor
  · intro h
    by_contra hne
    apply h
    intro x
    by_contra hpx
    exact hne ⟨x, hpx⟩
  · rintro ⟨x, hpx⟩ hall
    exact hpx (hall x)

end ClassicalLogicSeeds

section ConditionalSeed

variable (P Q : Prop)

/-- Classical negation-of-implication candidate. -/
theorem not_imp_iff_and_not : (¬ (P → Q)) ↔ P ∧ ¬ Q := by
  classical
  constructor
  · intro h
    constructor
    · by_contra hp
      apply h
      intro p
      exact False.elim (hp p)
    · intro q
      apply h
      intro _
      exact q
  · rintro ⟨hp, hnq⟩ hpq
    exact hnq (hpq hp)

end ConditionalSeed
