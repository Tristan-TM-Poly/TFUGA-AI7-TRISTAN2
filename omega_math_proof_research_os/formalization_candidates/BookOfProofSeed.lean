/-
Ω-MATH-PROOF-RESEARCH-OS R0.1 — formalization candidates.

OAK STATUS: CANDIDATE / KERNEL GATE ACTIVE.
These statements are intentionally small translations of paraphrased logical
rules extracted from the supplied Book of Proof metadata. Kernel acceptance
under the pinned Lean toolchain certifies only the formal declarations; it does
not by itself certify semantic identity with the natural-language source.
-/

universe u

section ClassicalLogicSeeds

variable {α : Type u} (P : α → Prop)

/-- Classical quantifier-negation candidate. -/
theorem not_forall_iff_exists_not : (¬ ∀ x, P x) ↔ ∃ x, ¬ P x := by
  classical
  constructor
  · intro h
    apply Classical.byContradiction
    intro hne
    apply h
    intro x
    apply Classical.byContradiction
    intro hpx
    apply hne
    exact ⟨x, hpx⟩
  · intro hex hall
    cases hex with
    | intro x hpx =>
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
    · apply Classical.byContradiction
      intro hnp
      apply h
      intro hp
      exact False.elim (hnp hp)
    · intro hq
      apply h
      intro _
      exact hq
  · intro hand himp
    exact hand.right (himp hand.left)

end ConditionalSeed
