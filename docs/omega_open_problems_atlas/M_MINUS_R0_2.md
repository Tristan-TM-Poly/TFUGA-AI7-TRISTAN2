# Ω-OPEN-PROBLEMS-ATLAS-T∞ — M⁻ R0.2

## Negative-memory rules

1. **Generated-cell inflation**
   - Failure: reporting an addressable research cell as a real open problem.
   - Rule: generated fixtures always keep `independently_checked_open=false`.

2. **Source-status substitution**
   - Failure: treating a website label as an independent current literature check.
   - Rule: source-reported status and independently checked status are separate fields.

3. **Competition mixing**
   - Failure: adding olympiad or benchmark problems to the open-research count.
   - Rule: competition kinds are excluded from research-open counts.

4. **Finite-to-universal promotion**
   - Failure: converting a successful finite computation into a universal theorem.
   - Rule: every computational receipt declares a bounded claim scope.

5. **Formal-placeholder illusion**
   - Failure: treating Lean `sorry`, Coq `Admitted` or Isabelle `sorry` as completed proof.
   - Rule: placeholder audits fail closed and require kernel/rebuild evidence.

6. **Transfer-by-vocabulary**
   - Failure: inferring mathematical equivalence from shared words or domains.
   - Rule: every transfer starts unvalidated and requires a reverse check.

7. **Priority-as-truth**
   - Failure: interpreting an allocation score as a posterior probability of truth.
   - Rule: score output is explicitly limited to research-resource routing.

8. **Copyright mirroring**
   - Failure: copying full problem statements or datasets without permission.
   - Rule: metadata and short normalized summaries are the default; source-specific review is mandatory.

9. **Stale competition automation**
   - Failure: relying on cached rules, deadlines or AI policies.
   - Rule: identity-bound or external submission remains blocked without a current rules snapshot and explicit authorization.

10. **Sensitive-data ingestion**
    - Failure: including passwords, API tokens, identity documents, tax identifiers or banking data in the atlas.
    - Rule: forbidden fields cause complete snapshot rejection.

11. **Unbounded-memory campaign**
    - Failure: materializing every generated obligation in memory.
    - Rule: large campaigns stream into SQLite WAL with finite invocation budgets.

12. **Git-volume vanity**
    - Failure: treating additions, commits or generated JSON volume as mathematical progress.
    - Rule: progress requires a verified source, useful result, reproducible artifact, counterexample, formalization or externally reviewed proof.

13. **Implicit SQL arity drift**
    - Failure observed in CI run `30827707917`: the `leads` table had eight columns, while a positional INSERT declared seven placeholders and supplied eight values.
    - Consequence: all Python 3.10–3.13 jobs failed before benchmark execution; the 250k gate was correctly skipped.
    - Rule: mutable tables use explicit column lists and matching placeholder counts; schema evolution must be exercised by integration tests before scale claims.
    - Correction: `upsert_lead` now names all eight columns and uses eight placeholders.

## Required interpretation

```text
250,000 stored obligations = software scale evidence
250,000 stored obligations != 250,000 mathematical advances
268,435,456 logical cells = address space
268,435,456 logical cells != verified open problems
CI failure = discovered engineering defect and M⁻ evidence
CI failure != successful MAX validation
```
